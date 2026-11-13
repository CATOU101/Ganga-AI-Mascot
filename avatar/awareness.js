(function (root, factory) {
  const cleaner = root.GangaContentCleaner || (typeof require === 'function' ? require('./content-cleaner.js') : null);
  const api = factory(cleaner);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaAwareness = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (cleaner) {
  'use strict';

  const TOPICS = {
    ganga: { titleKey: 'awareness.topic.ganga', introKey: 'awareness.intro.ganga', query: 'Defining River Ganga six main headstreams', section: /^2\.3\.\s*Defining River Ganga$/i, pointsPerSource: 3 },
    pollution: { titleKey: 'awareness.topic.pollution', introKey: 'awareness.intro.pollution', query: 'Ganga pollutant ingress direct discharge polluted runoff', section: /^5\. Ganga River System:\s*Pollutant Ingress$/i, pointsPerSource: 3 },
    protect: { titleKey: 'awareness.topic.protect', introKey: 'awareness.intro.protect', query: 'Ganga ecological restoration recommended actions environmental flows', section: /^6\. Summary of Recommended Actions$/i, pointsPerSource: 5, useFullText: true },
    myth: { titleKey: 'awareness.topic.myth', introKey: 'awareness.intro.myth', query: 'Defining River Ganga six main headstreams', section: /^2\.3\.\s*Defining River Ganga$/i, pointsPerSource: 3 },
  };

  function create({ document, fetch: fetchImpl = globalThis.fetch.bind(globalThis), openResource = () => {}, i18n = globalThis.GangaUII18n }) {
    const topics = document.getElementById('awarenessTopics');
    const status = document.getElementById('awarenessStatus');
    const cards = document.getElementById('awarenessCards');
    let loaded = false;
    let currentTopic = 'ganga';
    let requestNumber = 0;
    let currentResults = null;
    let currentLessonResults = null;
    let lastStatus = null;
    let claimChoice = null;

    function tr(key, values = {}) { return i18n ? i18n.t(key, values) : key; }

    function el(tag, className, text) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    }
    function setStatus(key, state = '', values = {}) {
      lastStatus = { key, state, values };
      status.replaceChildren();
      status.dataset.state = state;
      const displayValues = { ...values };
      if (displayValues.topicKey) displayValues.topic = tr(displayValues.topicKey);
      status.appendChild(el('span', '', tr(key, displayValues)));
      if (key === 'awareness.loadFailed') {
        const retry = el('button', 'resource-retry-button', tr('awareness.retry'));
        retry.type = 'button';
        retry.addEventListener('click', () => selectTopic(currentTopic));
        status.appendChild(retry);
      }
    }
    function citationText(item) {
      const pages = item.page_start ? (item.page_end && item.page_end !== item.page_start ? tr('resources.pages', { start: item.page_start, end: item.page_end }) : tr('resources.page', { page: item.page_start })) : tr('resources.pageUnavailable');
      return `${item.title} · ${item.file_name} · ${pages}${item.section ? ` · ${item.section}` : ''}`;
    }
    function pointsFor(item) {
      const sourceText = item.lessonText || item.excerpt;
      const clean = cleaner ? cleaner.cleanText(sourceText, { sectionHeading: item.section }) : String(sourceText || '').trim();
      return cleaner ? cleaner.learningPoints(clean, { sectionHeading: item.section }).slice(0, 2) : clean.split(/(?<=[.!?])\s+/).filter(point => point.length > 45).slice(0, 2);
    }
    function sourceBlock(item, points) {
      const article = el('article', 'awareness-lesson-source');
      article.appendChild(el('p', 'awareness-source-kicker', item.section || tr('awareness.sourceSection')));
      const list = el('ul', 'awareness-learning-points');
      points.forEach(point => list.appendChild(el('li', '', point)));
      article.appendChild(list);
      const metadata = [item.knowledge_type, item.time_period, item.geographic_scope].filter(Boolean).join(' · ');
      if (metadata) article.appendChild(el('p', 'awareness-metadata', metadata));
      article.appendChild(el('p', 'awareness-citation', tr('awareness.source', { source: citationText(item) })));
      const open = el('button', 'awareness-source-link', tr('awareness.readSection'));
      open.type = 'button';
      open.addEventListener('click', () => openResource(item.file_name, item.section, item.page_start));
      article.appendChild(open);
      return article;
    }
    function renderLesson(key, results) {
      const config = TOPICS[key];
      cards.replaceChildren();
      cards.appendChild(el('header', 'awareness-lesson-heading'));
      cards.lastChild.append(el('p', 'app-page-eyebrow', tr('awareness.lessonEyebrow')), el('h3', '', tr(config.titleKey)), el('p', 'awareness-lesson-intro', tr(config.introKey)));
      if (key === 'myth') {
        const evidence = results.find(item => item.section.toLowerCase().includes('defining river ganga') && /six main headstreams/i.test(item.excerpt));
        if (!evidence) return false;
        cards.appendChild(renderClaimCheck(evidence, claimChoice));
        return true;
      }
      let pointCount = 0;
      for (const item of results) {
        const points = pointsFor(item).slice(0, config.pointsPerSource || 2);
        if (!points.length) continue;
        cards.appendChild(sourceBlock(item, points));
        pointCount += points.length;
        if (pointCount >= 5) break;
      }
      return pointCount > 0;
    }
    function renderClaimCheck(item, selectedChoice = null) {
      const article = el('article', 'awareness-claim-card');
      article.append(
        el('p', 'awareness-source-kicker', tr('awareness.claimEyebrow')),
        el('h4', '', tr('awareness.claimText')),
        el('p', 'awareness-claim-note', tr('awareness.claimNote'))
      );
      const controls = el('div', 'awareness-claim-controls');
      const result = el('p', 'awareness-claim-result', selectedChoice ? (selectedChoice === 'fact' ? tr('awareness.factResult') : tr('awareness.factSupported')) : tr('awareness.choose'));
      result.setAttribute('role', 'status');
      const explanation = el('div', 'awareness-claim-explanation');
      const myth = el('button', 'awareness-source-link awareness-choice', tr('awareness.myth'));
      const fact = el('button', 'awareness-source-link awareness-choice', tr('awareness.fact'));
      myth.type = fact.type = 'button';
      myth.disabled = fact.disabled = Boolean(selectedChoice);
      const reveal = (choice) => {
        claimChoice = choice;
        const correct = choice === 'fact';
        result.textContent = correct ? tr('awareness.factResult') : tr('awareness.factSupported');
        myth.disabled = fact.disabled = true;
        if (cleaner) explanation.appendChild(cleaner.renderText(document, item.excerpt, { sectionHeading: item.section }));
        else explanation.textContent = item.excerpt;
      };
      myth.addEventListener('click', () => reveal('myth'));
      fact.addEventListener('click', () => reveal('fact'));
      controls.append(myth, fact);
      article.append(controls, result, explanation);
      if (selectedChoice) reveal(selectedChoice);
      const metadata = [item.knowledge_type, item.time_period, item.geographic_scope].filter(Boolean).join(' · ');
      if (metadata) article.appendChild(el('p', 'awareness-metadata', metadata));
      article.appendChild(el('p', 'awareness-citation', tr('awareness.source', { source: citationText(item) })));
      const open = el('button', 'awareness-source-link', tr('awareness.readFullSection'));
      open.type = 'button';
      open.addEventListener('click', () => openResource(item.file_name, item.section, item.page_start));
      article.appendChild(open);
      return article;
    }
    async function loadFullSections(items) {
      return Promise.all(items.map(async item => {
        try {
          const response = await fetchImpl(`/api/integration/resources/document?file_name=${encodeURIComponent(item.file_name)}`, { headers: { Accept: 'application/json' } });
          if (!response.ok) return item;
          const doc = await response.json();
          const section = (doc.sections || []).find(candidate => candidate.section === item.section && (!item.page_start || candidate.page_start === item.page_start));
          return section ? { ...item, lessonText: section.text } : item;
        } catch (_) { return item; }
      }));
    }

    async function selectTopic(key) {
      const config = TOPICS[key];
      if (!config) return;
      currentTopic = key;
      currentLessonResults = null;
      const thisRequest = ++requestNumber;
      topics.querySelectorAll('[data-awareness-topic]').forEach(button => {
        const active = button.dataset.awarenessTopic === key;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
      cards.replaceChildren();
      setStatus('awareness.loading', 'loading');
      try {
        const response = await fetchImpl(`/api/integration/resources/search?q=${encodeURIComponent(config.query)}&limit=20`, { headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(tr('awareness.searchError', { status: response.status }));
        const payload = await response.json();
        if (thisRequest !== requestNumber) return;
        const results = (payload.results || []).filter(item => config.section.test(item.section || ''));
        currentResults = results;
        claimChoice = null;
        if (!results.length) {
          cards.replaceChildren();
          setStatus('awareness.noLesson', 'empty', { topicKey: config.titleKey });
          return;
        }
        const fullResults = config.useFullText ? await loadFullSections(results.slice(0, 1)) : results.slice(0, 3);
        if (thisRequest !== requestNumber) return;
        currentLessonResults = fullResults;
        if (!renderLesson(key, fullResults)) {
          cards.replaceChildren();
          setStatus('awareness.notEnough', 'empty');
          return;
        }
        setStatus('awareness.status', '', { topicKey: config.titleKey });
      } catch (_) {
        if (thisRequest !== requestNumber) return;
        setStatus('awareness.loadFailed', 'error');
      }
    }
    topics.querySelectorAll('[data-awareness-topic]').forEach(button => {
      button.addEventListener('click', () => selectTopic(button.dataset.awarenessTopic));
    });
    if (typeof globalThis.addEventListener === 'function') globalThis.addEventListener('ganga-website-language-change', () => {
      if (lastStatus) setStatus(lastStatus.key, lastStatus.state, lastStatus.values);
      if (currentLessonResults) renderLesson(currentTopic, currentLessonResults);
      if (i18n) i18n.applySubtree(topics);
    });
    return {
      show() { if (!loaded) { loaded = true; selectTopic(currentTopic); } },
      selectTopic,
      topics: TOPICS,
    };
  }
  return { create, TOPICS };
});
