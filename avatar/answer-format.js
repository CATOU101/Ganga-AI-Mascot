(function attachAnswerFormatter(root, factory) {
  const formatter = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = formatter;
  if (root) root.formatAssistantAnswer = formatter;
})(typeof window !== 'undefined' ? window : globalThis, function createAnswerFormatter() {
  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[character]);
  }

  function formatAssistantAnswer(answer) {
    const lines = String(answer || '').replace(/\r/g, '').split('\n');
    const output = [];
    let paragraph = [];
    let listType = null;
    let listItems = [];

    const flushParagraph = () => {
      if (paragraph.length) output.push(`<p>${paragraph.map(escapeHtml).join('<br>')}</p>`);
      paragraph = [];
    };
    const flushList = () => {
      if (listItems.length) {
        const tag = listType === 'ol' ? 'ol' : 'ul';
        output.push(`<${tag}>${listItems.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</${tag}>`);
      }
      listItems = [];
      listType = null;
    };

    for (let index = 0; index < lines.length;) {
      const line = lines[index].trim();
      const nextLine = lines[index + 1] || '';
      const cells = line.startsWith('|') && line.endsWith('|')
        ? line.slice(1, -1).split('|').map((cell) => cell.trim()) : null;
      const separator = cells && /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(nextLine);
      if (cells && separator) {
        flushParagraph(); flushList();
        const header = `<thead><tr>${cells.map((cell) => `<th>${escapeHtml(cell)}</th>`).join('')}</tr></thead>`;
        const rows = [];
        index += 2;
        while (index < lines.length && lines[index].trim().startsWith('|') && lines[index].trim().endsWith('|')) {
          const row = lines[index].trim().slice(1, -1).split('|').map((cell) => cell.trim());
          rows.push(`<tr>${cells.map((_, cellIndex) => `<td>${escapeHtml(row[cellIndex] || '')}</td>`).join('')}</tr>`);
          index += 1;
        }
        output.push(`<div class="answer-markdown-table-wrap"><table class="answer-markdown-table">${header}<tbody>${rows.join('')}</tbody></table></div>`);
        continue;
      }
      const heading = line.match(/^(#{1,3})\s+(.+)$/);
      if (heading) {
        flushParagraph(); flushList();
        const level = heading[1].length + 2;
        output.push(`<h${level}>${escapeHtml(heading[2])}</h${level}>`);
        index += 1;
        continue;
      }
      const bullet = line.match(/^[-*•]\s+(.+)$/);
      const numbered = line.match(/^\d+[.)]\s+(.+)$/);
      if (bullet || numbered) {
        flushParagraph();
        const type = numbered ? 'ol' : 'ul';
        if (listType && listType !== type) flushList();
        listType = type;
        listItems.push((bullet || numbered)[1]);
        index += 1;
        continue;
      }
      flushList();
      if (!line) flushParagraph();
      else paragraph.push(line);
      index += 1;
    }
    flushParagraph(); flushList();
    return output.join('');
  }
  return formatAssistantAnswer;
});
