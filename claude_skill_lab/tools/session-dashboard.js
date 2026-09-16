#!/usr/bin/env node
/**
 * Claude Code セッションダッシュボード（ローカルサーバー版）
 *
 * ~/.claude/projects/ 以下の *.jsonl (セッションログ) をスキャンし、
 * セッション一覧を見やすいダッシュボードとしてローカルサーバーで配信します。
 * ファイル変更を検知すると自動的に画面が更新され、PWAとしてインストールも可能です。
 *
 * 使い方:
 *   node session-dashboard.js
 *   → http://localhost:4756/ が起動し、既定のブラウザで自動的に開きます
 *
 *   node session-dashboard.js --port=8080   # ポート変更
 *   node session-dashboard.js --no-open     # ブラウザを自動で開かない
 *
 * 機能:
 * - 検索（タイトル・プロジェクト名） / プロジェクト絞り込み / ピン留め（ブラウザのlocalStorageに保存）
 * - ~/.claude/projects の変更を監視し、SSEで画面を自動更新（ローカルサーバー化・PWA化）
 * - 「実行中」判定は、まず lsof（Linux/macOS）または /proc（Linux）でそのセッションファイルを
 *   実際に開いているclaudeプロセスがあるかを確認する。どちらも使えない環境（素のWindows等）では
 *   従来通り「直近◯分以内に更新されたファイル」による簡易判定にフォールバックする。
 *
 * 注意:
 * - Claude Codeの内部ファイル形式は非公式・非保証のため、
 *   バージョンによってパスやJSON構造が変わる可能性があります。
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const http = require('http');
const { execSync } = require('child_process');

const CLAUDE_PROJECTS_DIR = path.join(os.homedir(), '.claude', 'projects');
const ACTIVE_THRESHOLD_MIN = 10; // プロセス監視が使えない場合の簡易判定：この分数以内に更新 → 「実行中」とみなす
const DEFAULT_PORT = 4756;
const UPDATE_DEBOUNCE_MS = 400;
const SSE_HEARTBEAT_MS = 30000;
const ACTIVE_INFO_CACHE_MS = 2000;

// ---------- セッション読み取り ----------

function findJsonlFiles(dir) {
  const results = [];
  if (!fs.existsSync(dir)) return results;

  function walk(current) {
    const entries = fs.readdirSync(current, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        walk(fullPath);
      } else if (entry.isFile() && entry.name.endsWith('.jsonl')) {
        results.push(fullPath);
      }
    }
  }
  walk(dir);
  return results;
}

function decodeProjectName(dirName) {
  // Claude Codeはプロジェクトパスの "/" を "-" に置換してディレクトリ名にしている
  return dirName.replace(/^-/, '/').replace(/-/g, '/');
}

function parseSession(filePath, activeInfo) {
  const stat = fs.statSync(filePath);
  const sessionId = path.basename(filePath, '.jsonl');
  const projectDir = path.basename(path.dirname(filePath));

  let promptCount = 0;
  let firstUserMessage = null;

  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n').filter(Boolean);

    for (const line of lines) {
      try {
        const entry = JSON.parse(line);
        // ユーザーの発話をプロンプトとしてカウント(ツール結果等は除外)
        if (entry.type === 'user' && entry.message && entry.message.role === 'user') {
          const c = entry.message.content;
          const isToolResult = Array.isArray(c) && c.every(b => b.type === 'tool_result');
          if (!isToolResult) {
            promptCount++;
            if (!firstUserMessage) {
              if (typeof c === 'string') firstUserMessage = c;
              else if (Array.isArray(c)) {
                const textBlock = c.find(b => b.type === 'text');
                if (textBlock) firstUserMessage = textBlock.text;
              }
            }
          }
        }
      } catch (e) {
        // 壊れた行はスキップ
      }
    }
  } catch (e) {
    // 読み取り失敗はスキップ
  }

  const minutesAgo = (Date.now() - stat.mtimeMs) / 60000;

  let isActive;
  let activeSource;
  if (activeInfo && activeInfo.source) {
    isActive = activeInfo.files.has(path.resolve(filePath));
    activeSource = 'process';
  } else {
    isActive = minutesAgo <= ACTIVE_THRESHOLD_MIN;
    activeSource = 'heuristic';
  }

  return {
    sessionId,
    project: decodeProjectName(projectDir),
    title: firstUserMessage ? firstUserMessage.slice(0, 60) : '(タイトルなし)',
    promptCount,
    lastUpdated: stat.mtime,
    minutesAgo,
    isActive,
    activeSource,
  };
}

// ---------- 「実行中」判定（プロセス監視） ----------
//
// 1. lsof で ~/.claude/projects 以下のファイルを開いているプロセスを調べる（Linux/macOSで概ね利用可）
// 2. lsofが無ければ /proc を直接読んで、claudeを含むコマンドラインを持つプロセスのfdを調べる（Linux/WSL）
// 3. どちらも使えなければ null を返し、呼び出し側でタイムスタンプ簡易判定にフォールバックする

function getProcessActiveJsonlFilesViaLsof() {
  try {
    const out = execSync(`lsof +D "${CLAUDE_PROJECTS_DIR}" -F cn 2>/dev/null`, {
      encoding: 'utf-8',
      timeout: 3000,
    });
    const found = new Set();
    let currentCommand = '';
    for (const line of out.split('\n')) {
      if (line.startsWith('c')) {
        currentCommand = line.slice(1);
      } else if (line.startsWith('n') && /claude/i.test(currentCommand)) {
        const filePath = line.slice(1);
        if (filePath.endsWith('.jsonl')) found.add(path.resolve(filePath));
      }
    }
    return found;
  } catch (e) {
    return null; // lsof未インストール、権限エラーなど
  }
}

function getProcessActiveJsonlFilesViaProc() {
  if (process.platform !== 'linux') return null;
  try {
    const found = new Set();
    const pids = fs.readdirSync('/proc').filter(n => /^\d+$/.test(n));
    for (const pid of pids) {
      let cmdline;
      try {
        cmdline = fs.readFileSync(`/proc/${pid}/cmdline`, 'utf-8');
      } catch (e) {
        continue; // 権限なし・プロセス消失など
      }
      if (!/claude/i.test(cmdline)) continue;

      let fds;
      try {
        fds = fs.readdirSync(`/proc/${pid}/fd`);
      } catch (e) {
        continue;
      }
      for (const fd of fds) {
        try {
          const target = fs.readlinkSync(`/proc/${pid}/fd/${fd}`);
          if (target.endsWith('.jsonl') && target.startsWith(CLAUDE_PROJECTS_DIR)) {
            found.add(path.resolve(target));
          }
        } catch (e) {
          // fdが閉じられた直後など
        }
      }
    }
    return found;
  } catch (e) {
    return null;
  }
}

function getProcessActiveJsonlFiles() {
  const viaLsof = getProcessActiveJsonlFilesViaLsof();
  if (viaLsof !== null) return { files: viaLsof, source: 'lsof' };

  const viaProc = getProcessActiveJsonlFilesViaProc();
  if (viaProc !== null) return { files: viaProc, source: 'proc' };

  return { files: new Set(), source: null };
}

let activeInfoCache = null;
let activeInfoCacheAt = 0;
function getProcessActiveJsonlFilesCached() {
  const now = Date.now();
  if (activeInfoCache && now - activeInfoCacheAt < ACTIVE_INFO_CACHE_MS) return activeInfoCache;
  activeInfoCache = getProcessActiveJsonlFiles();
  activeInfoCacheAt = now;
  return activeInfoCache;
}

function getSessions() {
  const files = findJsonlFiles(CLAUDE_PROJECTS_DIR);
  const activeInfo = getProcessActiveJsonlFilesCached();
  return files
    .map(f => parseSession(f, activeInfo))
    .sort((a, b) => new Date(b.lastUpdated) - new Date(a.lastUpdated));
}

// ---------- ファイル監視 → 自動更新(SSE) ----------

const sseClients = new Set();

function broadcastUpdate() {
  for (const res of sseClients) {
    try {
      res.write('data: update\n\n');
    } catch (e) {
      sseClients.delete(res);
    }
  }
}

let debounceTimer = null;
function scheduleUpdate() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(broadcastUpdate, UPDATE_DEBOUNCE_MS);
}

const watchedDirs = new Set();
function watchTopLevelDirs() {
  if (!fs.existsSync(CLAUDE_PROJECTS_DIR)) return;
  const entries = fs.readdirSync(CLAUDE_PROJECTS_DIR, { withFileTypes: true });
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const dir = path.join(CLAUDE_PROJECTS_DIR, entry.name);
    if (watchedDirs.has(dir)) continue;
    try {
      fs.watch(dir, () => scheduleUpdate());
      watchedDirs.add(dir);
    } catch (e) {
      // 監視できないディレクトリは無視
    }
  }
}

function setupWatcher() {
  try {
    fs.watch(CLAUDE_PROJECTS_DIR, { recursive: true }, () => scheduleUpdate());
    console.log('📡 再帰監視モードでファイル変更を追跡します');
  } catch (e) {
    console.log('📡 このプラットフォームでは再帰監視が使えないため、プロジェクトごとに監視します');
    watchTopLevelDirs();
    setInterval(watchTopLevelDirs, 30000); // 新規プロジェクトフォルダの追加を拾うための定期再スキャン
  }
}

// ---------- PWA用アセット ----------

const MANIFEST_JSON = JSON.stringify({
  name: 'Claude Sessions Dashboard',
  short_name: 'CC Sessions',
  start_url: '/',
  display: 'standalone',
  background_color: '#0d0d0d',
  theme_color: '#0d0d0d',
  icons: [
    { src: '/icon.svg', sizes: 'any', type: 'image/svg+xml', purpose: 'any maskable' },
  ],
});

const ICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128">
  <rect width="128" height="128" rx="24" fill="#0d0d0d"/>
  <circle cx="64" cy="64" r="36" fill="#4ade80"/>
  <text x="64" y="79" font-size="48" text-anchor="middle" fill="#0d0d0d" font-family="sans-serif" font-weight="bold">C</text>
</svg>`;

const SW_JS = `const CACHE = 'cc-dashboard-v1';
const SHELL = ['/', '/manifest.json', '/icon.svg'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/') || url.pathname === '/events') return; // 常に最新を取りに行く
  event.respondWith(
    fetch(event.request)
      .then((res) => {
        const clone = res.clone();
        caches.open(CACHE).then((cache) => cache.put(event.request, clone));
        return res;
      })
      .catch(() => caches.match(event.request))
  );
});
`;

// ---------- HTMLシェル ----------

function buildShellHtml() {
  return `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0d0d0d">
<link rel="manifest" href="/manifest.json">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<title>Claude Sessions</title>
<style>
  body { background:#0d0d0d; color:#eee; font-family:sans-serif; padding:24px; }
  h1 { font-size:20px; display:flex; align-items:center; gap:10px; }
  .detection { font-size:11px; color:#888; font-weight:normal; background:#1a1a1a; padding:2px 8px; border-radius:10px; }
  .stats { display:flex; gap:24px; margin:16px 0; }
  .stat { background:#1a1a1a; padding:12px 20px; border-radius:8px; }
  .stat .num { font-size:22px; font-weight:bold; color:#4ade80; }
  .controls { display:flex; gap:10px; margin:16px 0; flex-wrap:wrap; }
  .controls input, .controls select {
    background:#1a1a1a; color:#eee; border:1px solid #2a2a2a; border-radius:6px;
    padding:8px 10px; font-size:14px;
  }
  .controls input { flex:1; min-width:200px; }
  table { width:100%; border-collapse:collapse; margin-top:8px; }
  th, td { text-align:left; padding:10px; border-bottom:1px solid #2a2a2a; font-size:14px; }
  th { color:#999; font-weight:normal; }
  .title { font-weight:bold; }
  .meta { color:#888; font-size:12px; margin-top:2px; }
  .badge { background:#2a2a2a; padding:1px 6px; border-radius:4px; font-family:monospace; }
  .dot { display:inline-block; width:6px; height:6px; background:#4ade80; border-radius:50%; margin:0 4px; }
  button { background:#2a2a2a; color:#eee; border:none; padding:6px 10px; border-radius:6px; cursor:pointer; font-size:13px; }
  button:hover { background:#3a3a3a; }
  .pin-btn { background:none; font-size:16px; padding:2px 6px; }
  .pin-btn.pinned { color:#facc15; }
  .empty { color:#888; padding:20px 0; text-align:center; }
</style>
</head>
<body>
  <h1>Claude Sessions（ローカル） <span class="detection" id="detection">検出方式: -</span></h1>
  <div class="stats">
    <div class="stat"><div class="num" id="statActive">-</div>実行中</div>
    <div class="stat"><div class="num" id="statRecent">-</div>24時間以内</div>
    <div class="stat"><div class="num" id="statTotal">-</div>セッション合計</div>
  </div>
  <div class="controls">
    <input id="search" type="search" placeholder="検索（タイトル・プロジェクト名）">
    <select id="projectFilter"><option value="">すべてのプロジェクト</option></select>
  </div>
  <table>
    <thead><tr><th></th><th>セッション</th><th>最終更新</th><th>プロンプト</th><th>操作</th></tr></thead>
    <tbody id="tbody"><tr><td colspan="5" class="empty">読み込み中...</td></tr></tbody>
  </table>

<script>
  const PIN_KEY = 'cc-dashboard-pinned';
  let allSessions = [];

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function getPinned() {
    try { return new Set(JSON.parse(localStorage.getItem(PIN_KEY) || '[]')); }
    catch (e) { return new Set(); }
  }
  function setPinned(set) {
    try { localStorage.setItem(PIN_KEY, JSON.stringify([...set])); } catch (e) {}
  }
  function togglePin(sessionId) {
    const pinned = getPinned();
    if (pinned.has(sessionId)) pinned.delete(sessionId); else pinned.add(sessionId);
    setPinned(pinned);
    render();
  }
  window.togglePin = togglePin;

  function copyResume(sessionId) {
    const cmd = 'claude --resume ' + sessionId;
    navigator.clipboard.writeText(cmd);
    alert('コピーしました:\\n' + cmd);
  }
  window.copyResume = copyResume;

  function formatRelativeTime(minutesAgo) {
    if (minutesAgo < 1) return 'たった今';
    if (minutesAgo < 60) return Math.floor(minutesAgo) + '分前';
    if (minutesAgo < 60 * 24) return Math.floor(minutesAgo / 60) + '時間前';
    return Math.floor(minutesAgo / (60 * 24)) + '日前';
  }

  function updateProjectOptions() {
    const sel = document.getElementById('projectFilter');
    const current = sel.value;
    const projects = [...new Set(allSessions.map(s => s.project))].sort();
    sel.innerHTML = '<option value="">すべてのプロジェクト</option>' +
      projects.map(p => '<option value="' + escapeHtml(p) + '">' + escapeHtml(p) + '</option>').join('');
    if (projects.includes(current)) sel.value = current;
  }

  function updateStats() {
    const activeCount = allSessions.filter(s => s.isActive).length;
    const last24h = allSessions.filter(s => s.minutesAgo <= 60 * 24).length;
    document.getElementById('statActive').textContent = activeCount;
    document.getElementById('statRecent').textContent = last24h;
    document.getElementById('statTotal').textContent = allSessions.length;
  }

  function render() {
    const pinned = getPinned();
    const q = document.getElementById('search').value.trim().toLowerCase();
    const proj = document.getElementById('projectFilter').value;

    let list = allSessions.filter(s => {
      if (proj && s.project !== proj) return false;
      if (q && !((s.title || '').toLowerCase().includes(q) || (s.project || '').toLowerCase().includes(q))) return false;
      return true;
    });

    list.sort((a, b) => {
      const ap = pinned.has(a.sessionId), bp = pinned.has(b.sessionId);
      if (ap !== bp) return ap ? -1 : 1;
      return new Date(b.lastUpdated) - new Date(a.lastUpdated);
    });

    const tbody = document.getElementById('tbody');
    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="empty">該当するセッションがありません</td></tr>';
      return;
    }

    tbody.innerHTML = list.map(s => {
      const isPinned = pinned.has(s.sessionId);
      const activeTitle = s.activeSource === 'process' ? 'プロセス監視で検出' : '更新時刻による簡易判定';
      return '<tr>' +
        '<td><button class="pin-btn ' + (isPinned ? 'pinned' : '') + '" onclick="togglePin(\\'' + s.sessionId + '\\')" title="ピン留め">' + (isPinned ? '★' : '☆') + '</button></td>' +
        '<td>' +
          '<div class="title">' + escapeHtml(s.title) + '</div>' +
          '<div class="meta">' + escapeHtml(s.project) + ' <span class="badge">' + s.sessionId.slice(0, 8) + '</span> ' +
          (s.isActive ? '<span class="dot" title="' + activeTitle + '"></span>実行中' : '') +
          '</div>' +
        '</td>' +
        '<td>' + formatRelativeTime(s.minutesAgo) + '</td>' +
        '<td>' + s.promptCount + '</td>' +
        '<td><button onclick="copyResume(\\'' + s.sessionId + '\\')">再開コマンドをコピー</button></td>' +
      '</tr>';
    }).join('');
  }

  async function fetchAndRender() {
    try {
      const res = await fetch('/api/sessions');
      const data = await res.json();
      allSessions = data.sessions;
      const methodLabel = { lsof: 'プロセス監視(lsof)', proc: 'プロセス監視(/proc)', heuristic: '簡易判定(更新時刻)' };
      document.getElementById('detection').textContent = '検出方式: ' + (methodLabel[data.detectionMethod] || '-');
      updateProjectOptions();
      updateStats();
      render();
    } catch (e) {
      console.error('セッション取得に失敗しました', e);
    }
  }

  document.getElementById('search').addEventListener('input', render);
  document.getElementById('projectFilter').addEventListener('change', render);

  fetchAndRender();

  const es = new EventSource('/events');
  es.onmessage = () => fetchAndRender();

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  }
</script>
</body>
</html>`;
}

// ---------- HTTPサーバー ----------

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');

  if (url.pathname === '/' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(buildShellHtml());
    return;
  }

  if (url.pathname === '/api/sessions' && req.method === 'GET') {
    const activeInfo = getProcessActiveJsonlFilesCached();
    const sessions = getSessions();
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ detectionMethod: activeInfo.source || 'heuristic', sessions }));
    return;
  }

  if (url.pathname === '/events' && req.method === 'GET') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream; charset=utf-8',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    });
    res.write('\n');
    sseClients.add(res);
    const heartbeat = setInterval(() => {
      try { res.write(': ping\n\n'); } catch (e) { clearInterval(heartbeat); }
    }, SSE_HEARTBEAT_MS);
    req.on('close', () => {
      clearInterval(heartbeat);
      sseClients.delete(res);
    });
    return;
  }

  if (url.pathname === '/manifest.json') {
    res.writeHead(200, { 'Content-Type': 'application/manifest+json; charset=utf-8' });
    res.end(MANIFEST_JSON);
    return;
  }

  if (url.pathname === '/icon.svg') {
    res.writeHead(200, { 'Content-Type': 'image/svg+xml' });
    res.end(ICON_SVG);
    return;
  }

  if (url.pathname === '/sw.js') {
    res.writeHead(200, { 'Content-Type': 'application/javascript; charset=utf-8' });
    res.end(SW_JS);
    return;
  }

  res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('Not Found');
});

function openBrowser(url) {
  try {
    if (process.platform === 'darwin') {
      execSync(`open "${url}"`);
    } else if (process.platform === 'win32') {
      execSync(`start "" "${url}"`, { shell: 'cmd.exe' });
    } else {
      execSync(`xdg-open "${url}"`);
    }
  } catch (e) {
    // 自動オープンに失敗しても致命的ではないので無視（URLはコンソールに出力済み）
  }
}

function main() {
  const args = process.argv.slice(2);
  const portArg = args.find(a => a.startsWith('--port='));
  const port = portArg ? parseInt(portArg.split('=')[1], 10) : DEFAULT_PORT;
  const noOpen = args.includes('--no-open');

  if (!fs.existsSync(CLAUDE_PROJECTS_DIR)) {
    console.log(`セッションディレクトリが見つかりませんでした: ${CLAUDE_PROJECTS_DIR}`);
    process.exit(1);
  }

  setupWatcher();

  server.listen(port, () => {
    const url = `http://localhost:${port}/`;
    console.log(`✅ ダッシュボードサーバーを起動しました: ${url}`);
    console.log('   ファイル変更を検知すると自動的に画面が更新されます（Ctrl+Cで終了）');
    if (!noOpen) openBrowser(url);
  });
}

main();
