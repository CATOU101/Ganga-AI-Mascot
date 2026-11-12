(function (root, factory) {
  const cleaner = root.GangaContentCleaner || (typeof require === 'function' ? require('./content-cleaner.js') : null);
  const api = factory(cleaner);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaResources = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (cleaner) {
  'use strict';

  const CATEGORIES = [
    { id: 'basin', label: 'River and Basin', query: 'Ganga river basin course tributaries' },
    { id: 'quality', label: 'Water Quality', query: 'water quality BOD DO pH dissolved oxygen' },
    { id: 'pollution', label: 'Pollution', query: 'pollutant ingress sewage discharge runoff' },
    { id: 'ecology', label: 'Ecology and Biodiversity', query: 'ecological restoration biodiversity habitat wetlands' },
    { id: 'conservation', label: 'Conservation and Restoration', query: 'ecological restoration recommended actions conservation' },
    { id: 'governance', label: 'Namami Gange and Governance', query: 'Namami Gange mission governance' },
  ];
  const PAGE_SIZE = 12;

  function create({ document, fetch: fetchImpl = globalThis.fetch.bind(globalThis) }) {
    const counts = document.getElementById('resourceCounts');
    const search = document.getElementById('resourceSearchInput');
    const status = document.getElementById('resourceStatus');
    const list = document.getElementById('resourceDocumentList');
    const categoriesNode = document.getElementById('resourceCategories');
    const loadMore = document.getElementById('resourceLoadMore');
    const libraryView = document.getElementById('resourceLibraryView');
    const detailView = document.getElementById('resourceDocumentView');
    const backButton = document.getElementById('resourceBackButton');
    const title = document.getElementById('resourceDocumentTitle');
    const meta = document.getElementById('resourceDocumentMeta');
    const description = document.getElementById('resourceDocumentDescription');
    const sections = document.getElementById('resourceSectionList');
    let documents = [];
    let matches = new Map();
    let categoryMatches = new Map();
    let visibleDocuments = [];
    let selectedCategory = 'all';
    let loaded = false;
    let searchTimer;
    let visibleCount = PAGE_SIZE;

    function node(tag, className, text) {
      const item = document.createElement(tag);
      if (className) item.className = className;
      if (text !== undefined) item.textContent = text;
      return item;
    }
    function requestJson(path) {
      return fetchImpl(path, { headers: { Accept: 'application/json' } }).then(response => {
        if (!response.ok) throw new Error(`Request failed (${response.status})`);
        return response.json();
      });
    }
    function sourceLine(section) {
      const page = section.page_start ? `Page ${section.page_start}${section.page_end && section.page_end !== section.page_start ? `–${section.page_end}` : ''}` : 'Page reference unavailable';
      return `${section.title} · ${section.file_name} · ${page}`;
    }
    function cleanText(text, heading) {
      return cleaner ? cleaner.cleanText(text, { sectionHeading: heading }) : String(text || '').trim();
    }
    function showStatus(message, kind = '') {
      status.textContent = message;
      status.dataset.state = kind;
    }
    function categoryResults(id) {
      return categoryMatches.get(id) || [];
    }
    function renderCategories() {
      categoriesNode.replaceChildren();
      const all = node('button', `resource-category${selectedCategory === 'all' ? ' active' : ''}`, 'All resources');
      all.type = 'button';
      all.setAttribute('aria-pressed', String(selectedCategory === 'all'));
      all.addEventListener('click', () => { selectedCategory = 'all'; matches = new Map(); search.value = '';  visibleCount = PAGE_SIZE; renderCategories(); renderDocuments(documents); showStatus(`${documents.length} approved documents in the library.`); });
      categoriesNode.appendChild(all);
      CATEGORIES.forEach(category => {
        if (!categoryResults(category.id).length) return;
        const button = node('button', `resource-category${selectedCategory === category.id ? ' active' : ''}`, category.label);
        button.type = 'button';
        button.setAttribute('aria-pressed', String(selectedCategory === category.id));
        button.addEventListener('click', () => {
          selectedCategory = category.id;
          matches = new Map();
          search.value = '';
          visibleCount = PAGE_SIZE;
          const files = new Set(categoryResults(category.id).map(item => item.file_name));
          renderCategories();
          renderDocuments(documents.filter(item => files.has(item.file_name)));
          showStatus(`${files.size} documents matched approved sections for ${category.label}.`);
        });
        categoriesNode.appendChild(button);
      });
    }
    function cardDescription(doc) {
      const match = matches.get(doc.file_name) || CATEGORIES.map(category => categoryResults(category.id).find(item => item.file_name === doc.file_name)).find(Boolean);
      if (match?.excerpt) {
        const excerpt = cleanText(match.excerpt, match.section).replace(/\s+/g, ' ');
        if (excerpt.length <= 220) return excerpt;
        const cutoff = excerpt.lastIndexOf(' ', 210);
        return `${excerpt.slice(0, cutoff > 0 ? cutoff : 210)}…`;
      }
      return `${doc.section_count} approved sections available to browse.`;
    }
    function renderDocuments(items) {
      visibleDocuments = items;
      list.replaceChildren();
      const current = items.slice(0, visibleCount);
      current.forEach(doc => {
        const card = node('article', 'resource-book-card');
        card.append(
          node('p', 'resource-card-kicker', doc.source_id ? `Source ${doc.source_id}` : 'Approved source document'),
          node('h3', 'resource-document-title', doc.title),
          node('p', 'resource-document-meta', `${doc.section_count} approved sections · ${doc.file_name}`),
          node('p', 'resource-card-description', cardDescription(doc))
        );
        const open = node('button', 'resource-open-button', 'Open document');
        open.type = 'button';
        open.addEventListener('click', () => openDocument(doc.file_name));
        card.appendChild(open);
        list.appendChild(card);
      });
      loadMore.hidden = items.length <= current.length;
    }
    function renderReadableText(target, text, sectionHeading) {
      target.replaceChildren();
      if (cleaner) target.appendChild(cleaner.renderText(document, text, { sectionHeading }));
      else target.textContent = text || '';
      if (!target.textContent.trim()) target.appendChild(node('p', 'resource-empty-copy', 'No readable text is available for this approved section.'));
    }
    function renderDocument(doc, focusSection = null) {
      libraryView.hidden = true;
      detailView.hidden = false;
      title.textContent = doc.title;
      const docMeta = [doc.file_name, doc.source_id ? `Source ${doc.source_id}` : '', `${doc.section_count} approved sections`, ...(doc.classifications || []), ...(doc.knowledge_types || [])].filter(Boolean);
      meta.textContent = docMeta.join(' · ');
      const firstSection = (doc.sections || []).find(section => cleanText(section.text, section.section).length > 80);
      const intro = firstSection ? cleanText(firstSection.text, firstSection.section).replace(/\s+/g, ' ').slice(0, 300) : '';
      description.textContent = intro && intro.length < 300 ? intro : intro ? `${intro.slice(0, intro.lastIndexOf(' ', 280))}…` : '';
      sections.replaceChildren();
      const sectionRows = doc.sections || [];
      sectionRows.forEach((section, index) => {
        const details = node('details', 'resource-section-accordion');
        details.open = focusSection ? section.section === focusSection && section.page_start === doc.focusPage : index === 0;
        const summary = node('summary', 'resource-section-summary');
        const label = section.subsection ? `${section.section} · ${section.subsection}` : section.section;
        summary.append(node('span', 'resource-section-heading', label), node('span', 'resource-section-page', section.page_start ? `Pages ${section.page_start}${section.page_end && section.page_end !== section.page_start ? `–${section.page_end}` : ''}` : 'Pages unavailable'));
        const content = node('div', 'resource-section-content');
        const classification = [section.classification, section.knowledge_type, section.time_period, section.geographic_scope].filter(Boolean).join(' · ');
        content.appendChild(node('p', 'resource-section-metadata', classification));
        const body = node('div', 'resource-section-text');
        renderReadableText(body, section.text, section.section);
        content.appendChild(body);
        content.appendChild(node('p', 'resource-reference', `Source: ${sourceLine(section)}`));
        details.append(summary, content);
        sections.appendChild(details);
      });
      if (!sectionRows.length) sections.appendChild(node('p', 'resource-empty-copy', 'This approved document has no readable sections in the current index.'));
      const expanded = Array.from(sections.children).find(item => item.open);
      if (expanded && focusSection) expanded.scrollIntoView?.({ block: 'start' });
    }
    async function openDocument(fileName, sectionName = null, pageStart = null) {
      showStatus('Opening approved document…', 'loading');
      try {
        const doc = await requestJson(`/api/integration/resources/document?file_name=${encodeURIComponent(fileName)}`);
        doc.focusPage = pageStart;
        renderDocument(doc, sectionName);
      } catch (_) {
        showStatus('This approved document could not be opened. Check the connection and try again.', 'error');
      }
    }
    async function runSearch(query) {
      const normalized = query.trim();
      if (!normalized) {
        selectedCategory = 'all';
        matches = new Map();
        visibleCount = PAGE_SIZE;
        renderCategories();
        renderDocuments(documents);
        showStatus(`${documents.length} approved documents in the library.`);
        return;
      }
      selectedCategory = '';
      renderCategories();
      showStatus('Searching approved sections…', 'loading');
      try {
        const payload = await requestJson(`/api/integration/resources/search?q=${encodeURIComponent(normalized)}&limit=20`);
        const results = payload.results || [];
        matches = new Map(results.map(item => [item.file_name, item]));
        const docMap = new Map(documents.map(item => [item.file_name, item]));
        const matchedDocs = [...matches.keys()].map(fileName => docMap.get(fileName)).filter(Boolean);
        visibleCount = PAGE_SIZE;
        renderDocuments(matchedDocs);
        showStatus(matchedDocs.length ? `${matchedDocs.length} documents have matching approved sections.` : 'No approved sections matched that search. Try a broader term.', matchedDocs.length ? '' : 'empty');
      } catch (_) {
        showStatus('The library search could not be completed. Check the connection and try again.', 'error');
      }
    }
    async function loadCategories() {
      const settled = await Promise.allSettled(CATEGORIES.map(async category => {
        const payload = await requestJson(`/api/integration/resources/search?q=${encodeURIComponent(category.query)}&limit=20`);
        return [category.id, payload.results || []];
      }));
      settled.forEach(result => { if (result.status === 'fulfilled') categoryMatches.set(...result.value); });
      renderCategories();
      if (selectedCategory === 'all') renderDocuments(documents);
    }
    async function load() {
      showStatus('Loading the approved Ganga collection…', 'loading');
      try {
        const payload = await requestJson('/api/integration/resources');
        documents = payload.documents || [];
        const values = payload.counts || {};
        counts.textContent = `${values.documents ?? documents.length} documents · ${values.approved_sections ?? '—'} sections`;
        loaded = true;
        renderDocuments(documents);
        showStatus(`${documents.length} approved documents in the library.`);
        loadCategories();
      } catch (_) {
        loaded = false;
        showStatus('The approved library could not be loaded. Check the connection and select Resources to retry.', 'error');
      }
    }
    search.addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => runSearch(search.value), 220);
    });
    loadMore.addEventListener('click', () => { visibleCount += PAGE_SIZE; renderDocuments(visibleDocuments); });
    backButton.addEventListener('click', () => { detailView.hidden = true; libraryView.hidden = false; });
    return {
      show() { if (!loaded) load(); },
      async openSection(fileName, section, pageStart) { await openDocument(fileName, section, pageStart); },
      categories: CATEGORIES,
    };
  }
  return { create, CATEGORIES };
});
