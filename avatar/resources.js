(function (root, factory) {
  const cleaner = root.GangaContentCleaner || (typeof require === 'function' ? require('./content-cleaner.js') : null);
  const api = factory(cleaner);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaResources = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (cleaner) {
  'use strict';

  const CATEGORIES = [
    { id: 'basin', label: 'River and Basin', labelKey: 'resources.cat.basin', query: 'Ganga river basin course tributaries' },
    { id: 'quality', label: 'Water Quality', labelKey: 'resources.cat.quality', query: 'water quality BOD DO pH dissolved oxygen' },
    { id: 'pollution', label: 'Pollution', labelKey: 'resources.cat.pollution', query: 'pollutant ingress sewage discharge runoff' },
    { id: 'ecology', label: 'Ecology and Biodiversity', labelKey: 'resources.cat.ecology', query: 'ecological restoration biodiversity habitat wetlands' },
    { id: 'conservation', label: 'Conservation and Restoration', labelKey: 'resources.cat.conservation', query: 'ecological restoration recommended actions conservation' },
    { id: 'governance', label: 'Namami Gange and Governance', labelKey: 'resources.cat.governance', query: 'Namami Gange mission governance' },
  ];
  const PAGE_SIZE = 12;

  function create({ document, fetch: fetchImpl = globalThis.fetch.bind(globalThis), i18n = globalThis.GangaUII18n }) {
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
    let currentDocument = null;
    let currentFocusSection = null;
    let lastStatus = null;

    function tr(key, values = {}) { return i18n ? i18n.t(key, values) : key; }
    function setUiText(element, key, values = {}) {
      if (i18n) i18n.setText(element, key, values);
      else element.textContent = tr(key, values);
    }
    function categoryLabel(category) { return tr(category.labelKey); }

    function node(tag, className, text) {
      const item = document.createElement(tag);
      if (className) item.className = className;
      if (text !== undefined) item.textContent = text;
      return item;
    }
    function requestJson(path) {
      return fetchImpl(path, { headers: { Accept: 'application/json' } }).then(response => {
        if (!response.ok) throw new Error(tr('resources.connectionError', { status: response.status }));
        return response.json();
      });
    }
    function sourceLine(section) {
      const page = section.page_start
        ? (section.page_end && section.page_end !== section.page_start
          ? tr('resources.pages', { start: section.page_start, end: section.page_end })
          : tr('resources.page', { page: section.page_start }))
        : tr('resources.pageUnavailable');
      return `${section.title} · ${section.file_name} · ${page}`;
    }
    function cleanText(text, heading) {
      return cleaner ? cleaner.cleanText(text, { sectionHeading: heading }) : String(text || '').trim();
    }
    function showStatus(key, kind = '', values = {}) {
      lastStatus = { key, kind, values };
      setUiText(status, key, values);
      status.dataset.state = kind;
    }
    function categoryResults(id) {
      return categoryMatches.get(id) || [];
    }
    function renderCategories() {
      categoriesNode.replaceChildren();
      const all = node('button', `resource-category${selectedCategory === 'all' ? ' active' : ''}`, tr('resources.all'));
      all.type = 'button';
      all.setAttribute('aria-pressed', String(selectedCategory === 'all'));
      all.addEventListener('click', () => { selectedCategory = 'all'; matches = new Map(); search.value = '';  visibleCount = PAGE_SIZE; renderCategories(); renderDocuments(documents); showStatus('resources.approvedCount', '', { count: documents.length }); });
      categoriesNode.appendChild(all);
      CATEGORIES.forEach(category => {
        if (!categoryResults(category.id).length) return;
        const button = node('button', `resource-category${selectedCategory === category.id ? ' active' : ''}`, categoryLabel(category));
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
          showStatus('resources.documentsMatched', '', { count: files.size, category: categoryLabel(category) });
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
      return tr('resources.sectionsAvailable', { count: doc.section_count });
    }
    function renderDocuments(items) {
      visibleDocuments = items;
      list.replaceChildren();
      const current = items.slice(0, visibleCount);
      current.forEach(doc => {
        const card = node('article', 'resource-book-card');
        card.append(
          node('p', 'resource-card-kicker', doc.source_id ? tr('resources.source', { id: doc.source_id }) : tr('resources.approvedSource')),
          node('h3', 'resource-document-title', doc.title),
          node('p', 'resource-document-meta', `${tr('resources.sectionsCount', { count: doc.section_count })} · ${doc.file_name}`),
          node('p', 'resource-card-description', cardDescription(doc))
        );
        const open = node('button', 'resource-open-button', tr('resources.open'));
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
      if (!target.textContent.trim()) target.appendChild(node('p', 'resource-empty-copy', tr('resources.noReadableText')));
    }
    function renderDocument(doc, focusSection = null) {
      currentDocument = doc;
      currentFocusSection = focusSection;
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
        const pageLabel = section.page_start
          ? (section.page_end && section.page_end !== section.page_start
            ? tr('resources.pages', { start: section.page_start, end: section.page_end })
            : tr('resources.page', { page: section.page_start }))
          : tr('resources.pagesUnavailable');
        summary.append(node('span', 'resource-section-heading', label), node('span', 'resource-section-page', pageLabel));
        const content = node('div', 'resource-section-content');
        const classification = [section.classification, section.knowledge_type, section.time_period, section.geographic_scope].filter(Boolean).join(' · ');
        content.appendChild(node('p', 'resource-section-metadata', classification));
        const body = node('div', 'resource-section-text');
        renderReadableText(body, section.text, section.section);
        content.appendChild(body);
        content.appendChild(node('p', 'resource-reference', tr('awareness.source', { source: sourceLine(section) })));
        details.append(summary, content);
        sections.appendChild(details);
      });
      if (!sectionRows.length) sections.appendChild(node('p', 'resource-empty-copy', tr('resources.noSections')));
      const expanded = Array.from(sections.children).find(item => item.open);
      if (expanded && focusSection) expanded.scrollIntoView?.({ block: 'start' });
    }
    async function openDocument(fileName, sectionName = null, pageStart = null) {
      showStatus('resources.opening', 'loading');
      try {
        const doc = await requestJson(`/api/integration/resources/document?file_name=${encodeURIComponent(fileName)}`);
        doc.focusPage = pageStart;
        renderDocument(doc, sectionName);
      } catch (_) {
        showStatus('resources.openFailed', 'error');
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
        showStatus('resources.approvedCount', '', { count: documents.length });
        return;
      }
      selectedCategory = '';
      renderCategories();
      showStatus('resources.searching', 'loading');
      try {
        const payload = await requestJson(`/api/integration/resources/search?q=${encodeURIComponent(normalized)}&limit=20`);
        const results = payload.results || [];
        matches = new Map(results.map(item => [item.file_name, item]));
        const docMap = new Map(documents.map(item => [item.file_name, item]));
        const matchedDocs = [...matches.keys()].map(fileName => docMap.get(fileName)).filter(Boolean);
        visibleCount = PAGE_SIZE;
        renderDocuments(matchedDocs);
        if (matchedDocs.length) showStatus('resources.searchMatches', '', { count: matchedDocs.length });
        else showStatus('resources.noMatches', 'empty');
      } catch (_) {
        showStatus('resources.searchFailed', 'error');
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
      showStatus('resources.loading', 'loading');
      try {
        const payload = await requestJson('/api/integration/resources');
        documents = payload.documents || [];
        const values = payload.counts || {};
        setUiText(counts, 'resources.loadedCount', { documents: values.documents ?? documents.length, sections: values.approved_sections ?? '—' });
        loaded = true;
        renderDocuments(documents);
        showStatus('resources.approvedCount', '', { count: documents.length });
        loadCategories();
      } catch (_) {
        loaded = false;
        showStatus('resources.loadFailed', 'error');
      }
    }
    search.addEventListener('input', () => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => runSearch(search.value), 220);
    });
    loadMore.addEventListener('click', () => { visibleCount += PAGE_SIZE; renderDocuments(visibleDocuments); });
    backButton.addEventListener('click', () => { detailView.hidden = true; libraryView.hidden = false; });
    if (typeof globalThis.addEventListener === 'function') {
      globalThis.addEventListener('ganga-website-language-change', () => {
        renderCategories();
        renderDocuments(selectedCategory === 'all' ? documents : visibleDocuments);
        if (!detailView.hidden && currentDocument) renderDocument(currentDocument, currentFocusSection);
        if (lastStatus) {
          const values = { ...lastStatus.values };
          if (lastStatus.key === 'resources.documentsMatched') values.category = categoryLabel(CATEGORIES.find(category => category.id === selectedCategory) || CATEGORIES[0]);
          showStatus(lastStatus.key, lastStatus.kind, values);
        }
      });
    }
    return {
      show() { if (!loaded) load(); },
      async openSection(fileName, section, pageStart) { await openDocument(fileName, section, pageStart); },
      categories: CATEGORIES,
    };
  }
  return { create, CATEGORIES };
});
