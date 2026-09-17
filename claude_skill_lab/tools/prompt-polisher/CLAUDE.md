# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A minimal VS Code extension ("Prompt Polisher"). It takes selected draft text in the
editor and rewrites it in place into a structured Markdown prompt (目的 / 背景・前提 /
制約条件 / 期待する出力) suitable for pasting into an LLM like Claude or ChatGPT.

The entire extension is `src/extension.ts` (~90 lines) — there is no other source to
navigate. It registers one command, `promptPolisher.polishSelection` (default keybinding
`Ctrl+Alt+P` / `Cmd+Alt+P`, active only when there's an editor selection).

## Commands

```bash
npm install       # install dependencies
npm run compile   # tsc -p ./  (src/**/*.ts -> out/)
npm run watch     # tsc -watch -p ./
```

There is no lint script and no test suite. To manually verify a change, open this folder
in VS Code and press `F5` (or run the "拡張機能を実行" launch config) to start an Extension
Development Host, then select some text and run the command.

## Architecture notes

- Uses VS Code's built-in Language Model API (`vscode.lm`), not a direct API key to any
  provider. It calls `vscode.lm.selectChatModels()` and uses whatever model a chat
  extension (e.g. GitHub Copilot Chat) currently exposes — there is no model selection
  logic beyond taking `models[0]`. If no LM-providing extension is enabled, the command
  fails with a user-facing error instead of calling out to an external API.
- The prompt sent to the model is hardcoded as `SYSTEM_INSTRUCTION` in `src/extension.ts`.
  Changing the output format/rules means editing that string directly — there is no
  config/settings surface for it.
- The instruction explicitly tells the model to preserve the original (Japanese) language
  and never invent information not present in the source text (mark missing info as
  `(要確認)` instead of fabricating it). Preserve this constraint if you edit the prompt.
- On success, the command replaces the original editor selection with the model's trimmed
  response via a single `editor.edit()`; on empty response or `LanguageModelError`, it
  shows a warning/error message and leaves the selection untouched.
- `out/` is compiled output (checked into this working copy but is a build artifact, not
  source of truth — always edit `src/extension.ts`, then `npm run compile`).
