(function (root, factory) {
  const cleaner = root.GangaContentCleaner || (typeof require === 'function' ? require('./content-cleaner.js') : null);
  const api = factory(cleaner);
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaAwareness = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function (cleaner) {
  'use strict';

  const TOPICS = {
    ganga: { title: 'Know Your Ganga', intro: 'Explore source-backed information about the river’s origin, course and basin.', query: 'Defining River Ganga six main headstreams', section: /^2\.3\.\s*Defining River Ganga$/i, pointsPerSource: 3 },
    pollution: { title: 'Pollution Awareness', intro: 'Learn how approved Ganga Basin reports describe pollutant pathways and sources.', query: 'Ganga pollutant ingress direct discharge polluted runoff', section: /^5\. Ganga River System:\s*Pollutant Ingress$/i, pointsPerSource: 3 },
    protect: { title: 'Protect the River', intro: 'Review actions recommended in the approved ecological restoration material.', query: 'Ganga ecological restoration recommended actions environmental flows', section: /^6\. Summary of Recommended Actions$/i, pointsPerSource: 5, useFullText: true },
    myth: { title: 'Myth vs Fact', intro: 'Check one reviewed statement against the cited GRBMP passage. This is a source check, not a claim about a widespread myth.', query: 'Defining River Ganga six main headstreams', section: /^2\.3\.\s*Defining River Ganga$/i, pointsPerSource: 3 },
  };

  function create({ document, fetch: fetchImpl = globalThis.fetch.bind(globalThis), openResource = () => {} }) {
    const topics = document.getElementById('awarenessTopics');
    const status = document.getElementById('awarenessStatus');
    const cards = document.getElementById('awarenessCards');
    let loaded = false;
    let currentTopic = 'ganga';
    let requestNumber = 0;

    function el(tag, className, text) {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    }
    function setStatus(text, state = '') {
      status.replaceChildren();
      status.dataset.state = state;
      status.appendChild(el('span', '', text));
    }
    function citationText(item) {
      const pages = item.page_start ? `Page ${item.page_start}${item.page_end && item.page_end !== item.page_start ? `–${item.page_end}` : ''}` : 'Page reference unavailable';
      return `${item.title} · ${item.file_name} · ${pages}${item.section ? ` · ${item.section}` : ''}`;
    }
    function pointsFor(item) {
      const sourceText = item.lessonText || item.excerpt;
      const clean = cleaner ? cleaner.cleanText(sourceText, { sectionHeading: item.section }) : String(sourceText || '').trim();
      return cleaner ? cleaner.learningPoints(clean, { sectionHeading: item.section }).slice(0, 2) : clean.split(/(?<=[.!?])\s+/).filter(point => point.length > 45).slice(0, 2);
    }
    function sourceBlock(item, points) {
      const article = el('article', 'awareness-lesson-source');
      article.appendChild(el('p', 'awareness-source-kicker', item.section || 'Approved source section'));
      const list = el('ul', 'awareness-learning-points');
      points.forEach(point => list.appendChild(el('li', '', point)));
      article.appendChild(list);
      const metadata = [item.knowledge_type, item.time_period, item.geographic_scope].filter(Boolean).join(' · ');
      if (metadata) article.appendChild(el('p', 'awareness-metadata', metadata));
      article.appendChild(el('p', 'awareness-citation', `Source: ${citationText(item)}`));
      const open = el('button', 'awareness-source-link', 'Read this approved section');
      open.type = 'button';
      open.addEventListener('click', () => openResource(item.file_name, item.section, item.page_start));
      article.appendChild(open);
      return article;
    }
    function renderLesson(key, results) {
      const config = TOPICS[key];
      cards.replaceChildren();
      cards.appendChild(el('header', 'awareness-lesson-heading'));
      cards.lastChild.append(el('p', 'app-page-eyebrow', 'SOURCE-BASED LESSON'), el('h3', '', config.title), el('p', 'awareness-lesson-intro', config.intro));
      if (key === 'myth') {
        const evidence = results.find(item => item.section.toLowerCase().includes('defining river ganga') && /six main headstreams/i.test(item.excerpt));
        if (!evidence) return false;
        cards.appendChild(renderClaimCheck(evidence));
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
    function renderClaimCheck(item) {
      const article = el('article', 'awareness-claim-card');
      article.append(
        el('p', 'awareness-source-kicker', 'Reviewed claim · answer using this source'),
        el('h4', '', 'The GRBMP defines the Ganga as including six main Himalayan headstreams.'),
        el('p', 'awareness-claim-note', 'This statement is checked against one cited passage; it is not presented as a widespread myth.')
      );
      const controls = el('div', 'awareness-claim-controls');
      const result = el('p', 'awareness-claim-result', 'Choose Myth or Fact to reveal the source-based answer.');
      result.setAttribute('role', 'status');
      const explanation = el('div', 'awareness-claim-explanation');
      const myth = el('button', 'awareness-source-link awareness-choice', 'Myth');
      const fact = el('button', 'awareness-source-link awareness-choice', 'Fact');
      myth.type = fact.type = 'button';
      const reveal = (choice) => {
        const correct = choice === 'fact';
        result.textContent = correct ? 'Fact — the cited GRBMP section states this.' : 'The cited GRBMP section supports this as a fact.';
        myth.disabled = fact.disabled = true;
        if (cleaner) explanation.appendChild(cleaner.renderText(document, item.excerpt, { sectionHeading: item.section }));
        else explanation.textContent = item.excerpt;
      };
      myth.addEventListener('click', () => reveal('myth'));
      fact.addEventListener('click', () => reveal('fact'));
      controls.append(myth, fact);
      article.append(controls, result, explanation);
      const metadata = [item.knowledge_type, item.time_period, item.geographic_scope].filter(Boolean).join(' · ');
      if (metadata) article.appendChild(el('p', 'awareness-metadata', metadata));
      article.appendChild(el('p', 'awareness-citation', `Source: ${citationText(item)}`));
      const open = el('button', 'awareness-source-link', 'Read the full source section');
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
      const thisRequest = ++requestNumber;
      topics.querySelectorAll('[data-awareness-topic]').forEach(button => {
        const active = button.dataset.awarenessTopic === key;
        button.classList.toggle('active', active);
        button.setAttribute('aria-pressed', String(active));
      });
      cards.replaceChildren();
      setStatus('Finding approved learning sources…', 'loading');
      try {
        const response = await fetchImpl(`/api/integration/resources/search?q=${encodeURIComponent(config.query)}&limit=20`, { headers: { Accept: 'application/json' } });
        if (!response.ok) throw new Error(`Search failed (${response.status})`);
        const payload = await response.json();
        if (thisRequest !== requestNumber) return;
        const results = (payload.results || []).filter(item => config.section.test(item.section || ''));
        if (!results.length) {
          cards.replaceChildren();
          setStatus(`The approved collection does not currently have a matching lesson for ${config.title}.`, 'empty');
          return;
        }
        const fullResults = config.useFullText ? await loadFullSections(results.slice(0, 1)) : results.slice(0, 3);
        if (thisRequest !== requestNumber) return;
        if (!renderLesson(key, fullResults)) {
          cards.replaceChildren();
          setStatus('The matching passages did not contain enough clean readable text for a lesson.', 'empty');
          return;
        }
        setStatus(`${config.title} · learning points are taken from the cited approved sections.`);
      } catch (_) {
        if (thisRequest !== requestNumber) return;
        setStatus('Awareness sources could not be loaded. Check the connection and select this topic to retry.', 'error');
        const retry = el('button', 'resource-retry-button', 'Retry');
        retry.type = 'button';
        retry.addEventListener('click', () => selectTopic(currentTopic));
        status.appendChild(retry);
      }
    }
    topics.querySelectorAll('[data-awareness-topic]').forEach(button => {
      button.addEventListener('click', () => selectTopic(button.dataset.awarenessTopic));
    });
    return {
      show() { if (!loaded) { loaded = true; selectTopic(currentTopic); } },
      selectTopic,
      topics: TOPICS,
    };
  }
  return { create, TOPICS };
});
