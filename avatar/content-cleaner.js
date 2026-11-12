(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaContentCleaner = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const FIGURE_CAPTION = /^\s*(?:fig(?:ure)?\.?\s*)\d+(?:[.-]\d+)*(?:\s*[a-z])?\s*[:.)-]?.*$/i;
  const IMAGE_MARKER = /^\s*(?:\[(?:image|figure)(?:\s+(?:placeholder|not available|extracted|description unavailable))?[^\]]*\]|<(?:img|image|figure)\b[^>]*>|(?:image|figure)_\d+\.(?:png|jpe?g|gif|tiff?|svg|webp))\s*$/i;
  const EMPTY_MARKER = /^\s*(?:\[?(?:no image description|empty image description|image description unavailable|ocr text unavailable|no readable text)\]?)\s*$/i;
  const PAGE_MARKER = /^\s*\[?page\s+\d+\]?\s*$/i;
  const TABLE_SEPARATOR = /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$/;
  const OCR_WORD_FIXES = [
    [/\bcompri\s+sing\b/gi, 'comprising'],
    [/\bw\s+ays\b/gi, 'ways'],
    [/\bsub\s+surface\b/gi, 'subsurface'],
    [/\ba\s+ssessment\b/gi, 'assessment'],
    [/\bpri\s+mary\b/gi, 'primary'],
    [/\bpol\s+lution\b/gi, 'pollution'],
    [/\ba\s+nd\b/gi, 'and'],
    [/\bNirma\s+l\b/g, 'Nirmal'],
  ];

  function cleanText(input, { sectionHeading = '' } = {}) {
    const source = OCR_WORD_FIXES.reduce((text, [pattern, replacement]) => text.replace(pattern, replacement), String(input || '').replace(/\r\n?/g, '\n').replace(/\u0000/g, '').replace(/\u00ad/g, '').replace(/\ufffd/g, ''));
    const rawLines = source.split('\n').map(line => line.trim());
    const occurrences = new Map();
    rawLines.filter(Boolean).forEach(line => {
      const key = line.toLocaleLowerCase().replace(/\s+/g, ' ');
      occurrences.set(key, (occurrences.get(key) || 0) + 1);
    });
    const seen = new Set();
    const cleaned = [];
    for (let index = 0; index < rawLines.length; index += 1) {
      let line = rawLines[index];
      if (!line || FIGURE_CAPTION.test(line) || IMAGE_MARKER.test(line) || EMPTY_MARKER.test(line) || PAGE_MARKER.test(line)) continue;
      if (/^(?:[-_=*•·|\s])+$/.test(line) && !TABLE_SEPARATOR.test(line)) continue;
      line = line.replace(/\b(?:image|figure)_\d+\.(?:png|jpe?g|gif|tiff?|svg|webp)\b/ig, '').trim();
      if (!line) continue;
      if (/^\[(?:page\s*)?\d+\]$/i.test(line)) continue;
      if (sectionHeading && line.toLocaleLowerCase() === sectionHeading.toLocaleLowerCase()) continue;
      const key = line.toLocaleLowerCase().replace(/\s+/g, ' ');
      if (seen.has(key)) continue;
      seen.add(key);
      // Repeated short GRBMP/page headers and footers are extraction furniture, not body text.
      const isRepeatedPageFurniture = occurrences.get(key) > 1 && line.length < 180 && /\b(?:grbmp|main plan document|extended summary|page\s+\d+|header|footer)\b/i.test(line);
      const isReportRunningHeader = /^GRBMP\s*[–-].*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}/i.test(line) && line.length < 180;
      const previousText = rawLines.slice(0, index).reverse().find(value => value.trim()) || '';
      const previousIsPageHeader = /^GRBMP\s*[–-]|^(?:page\s+\d+|\[page\s+\d+\])/i.test(previousText);
      if (isRepeatedPageFurniture || isReportRunningHeader || (/^\d{1,4}$/.test(line) && previousIsPageHeader)) continue;
      cleaned.push(line);
    }
    return cleaned.join('\n').replace(/\n{3,}/g, '\n\n').trim();
  }

  function renderText(document, input, { sectionHeading = '' } = {}) {
    const fragment = document.createDocumentFragment();
    const lines = cleanText(input, { sectionHeading }).split('\n');
    let paragraph = [];
    let list = null;
    let tableLines = [];
    const flushParagraph = () => {
      if (!paragraph.length) return;
      const p = document.createElement('p');
      p.textContent = paragraph.join(' ');
      fragment.appendChild(p);
      paragraph = [];
    };
    const flushList = () => { list = null; };
    const flushTable = () => {
      if (!tableLines.length) return;
      const rows = tableLines.map(line => line.trim().replace(/^\|/, '').replace(/\|$/, '').split('|').map(cell => cell.trim()));
      const hasHeader = rows.length >= 2 && rows[1].every(cell => /^:?-{3,}:?$/.test(cell));
      if (hasHeader && rows[0].length > 1) {
        const table = document.createElement('table');
        table.className = 'resource-readable-table';
        rows.forEach((cells, index) => {
          if (index === 1 && hasHeader) return;
          const row = document.createElement('tr');
          cells.forEach(value => {
            const cell = document.createElement(index === 0 ? 'th' : 'td');
            cell.textContent = value;
            row.appendChild(cell);
          });
          if (index === 0 && hasHeader) {
            const thead = document.createElement('thead'); thead.appendChild(row); table.appendChild(thead);
          } else {
            let tbody = table.querySelector('tbody');
            if (!tbody) { tbody = document.createElement('tbody'); table.appendChild(tbody); }
            tbody.appendChild(row);
          }
        });
        fragment.appendChild(table);
      }
      tableLines = [];
    };
    for (let lineIndex = 0; lineIndex < lines.length; lineIndex += 1) {
      const line = lines[lineIndex];
      if (!line.trim()) { flushParagraph(); flushList(); flushTable(); continue; }
      const pipeCount = (line.match(/\|/g) || []).length;
      const startsAndEndsTableRow = pipeCount >= 3 && line.trim().startsWith('|') && line.trim().endsWith('|');
      const tableCandidate = TABLE_SEPARATOR.test(line) || startsAndEndsTableRow || (pipeCount >= 1 && (TABLE_SEPARATOR.test(lines[lineIndex + 1] || '') || TABLE_SEPARATOR.test(lines[lineIndex - 1] || '')));
      if (tableCandidate) { flushParagraph(); flushList(); tableLines.push(line); continue; }
      flushTable();
      const item = line.match(/^\s*(?:[-*•]\s+|\d+[.)]\s+)(.+)$/);
      if (item) {
        flushParagraph();
        const ordered = /^\s*\d/.test(line);
        if (!list || list.tagName.toLowerCase() !== (ordered ? 'ol' : 'ul')) {
          flushList();
          list = document.createElement(ordered ? 'ol' : 'ul');
          list.className = 'resource-readable-list';
          fragment.appendChild(list);
        }
        const li = document.createElement('li'); li.textContent = item[1]; list.appendChild(li);
        continue;
      }
      flushList();
      paragraph.push(line);
    }
    flushParagraph(); flushTable();
    return fragment;
  }

  function learningPoints(input, options = {}) {
    const cleaned = cleanText(input, options).replace(/\s+/g, ' ').trim();
    if (!cleaned) return [];
    const listMarkers = [...cleaned.matchAll(/(?:^|[\s:;,])((?:\d+|[ivx]{1,4}))\)\s+/gi)];
    if (listMarkers.length >= 2) {
      const listed = listMarkers.map((marker, index) => {
        const start = marker.index + marker[0].length;
        const end = index + 1 < listMarkers.length ? listMarkers[index + 1].index : cleaned.length;
        let item = cleaned.slice(start, end).trim().replace(/[;,\s]+$/, '').replace(/\s+(?:and|or)$/i, '').replace(/,\.$/, '.');
        const sentenceEnd = item.search(/[.!?](?:\s|$)/);
        if (sentenceEnd >= 0) item = item.slice(0, sentenceEnd + 1);
        return item;
      }).filter(item => item.length >= 25);
      if (listed.length >= 2) {
        return listed.slice(0, 5).map(item => {
          const capitalized = item[0].toLocaleUpperCase() + item.slice(1);
          return /[.!?)]$/.test(capitalized) ? capitalized : `${capitalized}.`;
        });
      }
    }
    const clauses = cleaned.replace(/,\s*(?:and\s+)?(?:the\s+)?(subsequent|final)\s+/gi, '. $1 ');
    return clauses.split(/(?<=[.!?])\s+(?=[\p{L}\p{N}“"'‘(])/u)
      .map(sentence => {
        const trimmed = sentence.trim();
        return trimmed ? trimmed[0].toLocaleUpperCase() + trimmed.slice(1) : trimmed;
      })
      .filter(sentence => sentence.length >= 45 && sentence.length <= 760 && /[.!?)]$/.test(sentence))
      .slice(0, 5);
  }


  return { cleanText, renderText, learningPoints };
});
