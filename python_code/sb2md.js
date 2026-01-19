if (!Object.prototype.then) {
  Object.prototype.then = function (f) { return f.call(null, this); }
}

process.stdin.resume();
process.stdin.setEncoding('utf8');
let input_string = '';

process.stdin.on('data', chunk => {
  input_string += chunk;
});

process.stdin.on('end', () => {
  const text = input_string;
  console.log(sb2md(text));
});

function sb2md(text) {
  // code block
  const escapeCodeBlocks = s => s.replace(
    /^code:(.+)$((\n^[ \t].*$)+)/mg,
    (_, p1, p2) =>
      '```' + p1 + p2.replace(/^[ \t]/mg, '').replace(/\r|\n|\r\n/g, '+++') + '+++```'
  );

  const unescapeCodeBlocks = s => s.replace(/\+{3}/g, '\n');

  const replaceLine = line =>
    /^`{3}/.test(line) ? line :
      // level 2 heading
      line.replace(/^\[\[([^\[\]]+)\]\]$/, '## $1')
      .replace(/^\[\*\s+(\S[^\[\]]*)\]$/, '## $1')

      // anchor link
      .replace(/\[(\S.*)\s+(https?:\/\/\S+)\]/g, '[$1]($2)')
      .replace(/\[(https?:\/\/\S+)\s+(\S.*)\]/g, '[$2]($1)')

      // image block
      .replace(/^\[(https?:\/\/\S+\.(png|gif|jpe?g))\]$/, '![]($1)')
      .replace(/^\[(https:\/\/gyazo.com\/\S+)\]$/, '![]($1.png)')

      // unordered list
      .replace(/^\s(\S.*)$/, '- $1')
      .replace(/^\s{2}(\S.*)$/, '  - $1')
      .replace(/^\s{3}(\S.*)$/, '    - $1')

      // bold text
      .replace(/\[\[([^\[\]]+)\]\]/g, '**$1**')
      .replace(/\[\*\s+([^\[\]]+)\]/g, '**$1**')

      // italic text
      .replace(/\[\/\s+([^\[\]]+)\]/g, '*$1*');

  return text
    .then(escapeCodeBlocks)
    .split(/\r|\n|\r\n/)
    // first line is level 1 heading
    .then(lines => [lines[0].replace(/^(.+)$/, '# $1')].concat(lines.slice(1)))
    .map(replaceLine)
    .join('\n')
    .then(unescapeCodeBlocks);
}