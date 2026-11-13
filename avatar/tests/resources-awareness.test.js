const assert = require('node:assert/strict');
const test = require('node:test');
const resources = require('../resources.js');
const awareness = require('../awareness.js');
const cleaner = require('../content-cleaner.js');
const i18n = require('../ui-i18n.js');

class Element {
  constructor(tag = 'div', dataset = {}) {
    this.tagName = tag;
    this.dataset = dataset;
    this.children = [];
    this.attributes = {};
    this.listeners = {};
    this.hidden = false;
    this.value = '';
    this._text = '';
    this.classList = { toggle() {} };
  }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  append(...items) { this.children.push(...items); }
  appendChild(item) { this.children.push(item); return item; }
  get lastChild() { return this.children.at(-1) || null; }
  replaceChildren(...items) { this._text = ''; this.children = items; }
  addEventListener(type, listener) { this.listeners[type] = listener; }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  querySelectorAll(selector) { return selector === 'button' ? this.children.filter(child => child.tagName === 'button') : []; }
  querySelector(selector) { return selector === 'tbody' ? this.children.find(child => child.tagName === 'tbody') || null : null; }
}
function makeDocument(ids) {
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  return { elements, getElementById: id => elements[id] || null, createElement: tag => new Element(tag), createDocumentFragment: () => new Element('fragment') };
}
const tick = () => new Promise(resolve => setImmediate(resolve));
const sampleSection = {
  title: 'GRBMP report', file_name: 'report.pdf', source_id: 'SRC-1', section: 'River origins', subsection: null,
  page_start: 4, page_end: 5, classification: 'KEEP_HISTORICAL', knowledge_type: 'HISTORICAL',
  time_period: 'Historical report', geographic_scope: 'Ganga Basin',
  text: 'River flows from its Himalayan headstreams toward the Bay of Bengal.\nFig. 2.3: extracted image caption\nEquation: Q = A × v.'
};

test('presentation cleaner removes image furniture but preserves prose, values, equations and lists', () => {
  const cleaned = cleaner.cleanText('Report header\n[Page 21]\nFig. 1.2: River photograph\nimage_03.png\nThe figure shows the measured value is 12 mg/L.\nEquation: Q = A × v.\n- Protect riparian vegetation.\nReport header');
  assert.doesNotMatch(cleaned, /Page 21|Fig\. 1\.2|image_03\.png|Report header/);
  assert.match(cleaned, /figure shows the measured value is 12 mg\/L/);
  assert.match(cleaner.cleanText('River is compri sing six headstreams.'), /comprising/);
  assert.match(cleaned, /Q = A × v/);
  assert.match(cleaned, /Protect riparian vegetation/);
  const document = makeDocument([]);
  const table = cleaner.renderText(document, '|Parameter|Value|\n|---|---|\n|pH|7.2|');
  assert.equal(table.children[0].tagName, 'table');
  assert.match(table.children[0].textContent, /pH7.2/);
  const brokenTable = cleaner.renderText(document, '|fragment|\n|----|');
  assert.equal(brokenTable.children.length, 0);
});

test('Resources library categories use supported documents and document sections stay ordered and readable', async () => {
  const ids = ['resourceCounts','resourceSearchInput','resourceStatus','resourceDocumentList','resourceCategories','resourceSearchResults','resourceLoadMore','resourceLibraryView','resourceDocumentView','resourceBackButton','resourceDocumentTitle','resourceDocumentMeta','resourceDocumentDescription','resourceSectionList'];
  const document = makeDocument(ids);
  const sections = [sampleSection, { ...sampleSection, section: 'Conservation measures', page_start: 6, page_end: 7, text: 'Recommended action: restore native riverbank vegetation.' }];
  const fetch = async url => {
    if (url.includes('/document?')) return { ok: true, json: async () => ({ title: 'GRBMP report', file_name: 'report.pdf', source_id: 'SRC-1', section_count: 2, classifications: ['KEEP_HISTORICAL'], knowledge_types: ['HISTORICAL'], sections }) };
    if (url.includes('/search?')) {
      const query = new URLSearchParams(url.split('?')[1]).get('q') || '';
      return { ok: true, json: async () => ({ results: query.startsWith('water quality') ? [] : [{ ...sampleSection, excerpt: sampleSection.text }] }) };
    }
    return { ok: true, json: async () => ({ counts: { documents: 1, approved_sections: 2, indexed_chunks: 3 }, documents: [{ title: 'GRBMP report', file_name: 'report.pdf', source_id: 'SRC-1', section_count: 2 }] }) };
  };
  const oldAddEventListener = globalThis.addEventListener;
  const listeners = new Map();
  globalThis.addEventListener = (name, listener) => listeners.set(name, listener);
  const controller = resources.create({ document, fetch, i18n });
  controller.show();
  await tick(); await tick();
  assert.match(document.elements.resourceCounts.textContent, /1 documents/);
  assert.ok(document.elements.resourceCategories.children.length > 1);
  assert.doesNotMatch(document.elements.resourceCategories.textContent, /Water Quality/);
  const search = document.elements.resourceSearchInput;
  search.value = 'Gaumukh'; search.listeners.input();
  await new Promise(resolve => setTimeout(resolve, 240)); await tick();
  assert.equal(document.elements.resourceDocumentList.children.length, 1);
  assert.match(document.elements.resourceStatus.textContent, /matching approved sections/);
  search.value = ''; search.listeners.input();
  await new Promise(resolve => setTimeout(resolve, 240)); await tick();
  const card = document.elements.resourceDocumentList.children[0];
  card.children.at(-1).listeners.click();
  await tick(); await tick();
  assert.equal(document.elements.resourceDocumentTitle.textContent, 'GRBMP report');
  const accordion = document.elements.resourceSectionList.children;
  assert.equal(accordion.length, 2);
  assert.equal(accordion[0].open, true);
  assert.equal(accordion[1].open, false);
  assert.match(accordion[0].textContent, /Pages 4–5/);
  assert.doesNotMatch(accordion[0].textContent, /Fig\. 2\.3|extracted image caption/);
  assert.match(accordion[0].textContent, /12|Q = A × v/);
  document.elements.resourceBackButton.listeners.click();
  assert.equal(document.elements.resourceDocumentView.hidden, true);
  assert.equal(document.elements.resourceLibraryView.hidden, false);
  i18n.setLanguage('kn', { persist: false, document: null, window: { dispatchEvent: event => listeners.get(event.type)?.(event) } });
  assert.match(document.elements.resourceCategories.textContent, /ಎಲ್ಲಾ ಸಂಪನ್ಮೂಲಗಳು/);
  assert.equal(document.elements.resourceDocumentTitle.textContent, 'GRBMP report');
  assert.match(document.elements.resourceStatus.textContent, /ತೆರೆಯಲಾಗುತ್ತಿದೆ/);
  i18n.setLanguage('en', { persist: false, document: null, window: null });
  if (oldAddEventListener === undefined) delete globalThis.addEventListener;
  else globalThis.addEventListener = oldAddEventListener;
});

test('Awareness lesson uses source-derived points and Myth vs Fact reveals its cited answer', async () => {
  const topics = new Element();
  const mythTopic = new Element('button', { awarenessTopic: 'myth' });
  const pollutionTopic = new Element('button', { awarenessTopic: 'pollution' });
  topics.querySelectorAll = () => [mythTopic, pollutionTopic];
  const status = new Element();
  const cards = new Element();
  const document = { getElementById: id => ({ awarenessTopics: topics, awarenessStatus: status, awarenessCards: cards })[id], createElement: tag => new Element(tag), createDocumentFragment: () => new Element('fragment') };
  const evidence = { ...sampleSection, section: '2.3. Defining River Ganga', page_start: 21, page_end: 21, excerpt: 'River Ganga is defined herein as comprising six main headstreams originating in the Himalayas, including Alaknanda and Bhagirathi rivers.' };
  const pollution = { ...sampleSection, section: '5. Ganga River System: Pollutant Ingress', page_start: 25, page_end: 25, excerpt: 'Pollutant ingress into the Ganga river system occurs in three ways, 1) by direct discharge of pollutants, 2) discharge of polluted surface runoff into rivers, and 3) seepage of polluted subsurface flows into rivers.', text: 'Pollutant ingress into the Ganga river system occurs in three ways, 1) by direct discharge of pollutants, 2) discharge of polluted surface runoff into rivers, and 3) seepage of polluted subsurface flows into rivers.' };
  const fetch = async url => {
    if (url.includes('/document?')) return { ok: true, json: async () => ({ sections: [pollution] }) };
    const item = url.includes('pollutant') ? pollution : evidence;
    return { ok: true, json: async () => ({ results: [item] }) };
  };
  const oldAddEventListener = globalThis.addEventListener;
  const listeners = new Map();
  globalThis.addEventListener = (name, listener) => listeners.set(name, listener);
  const controller = awareness.create({ document, fetch, i18n });
  await controller.selectTopic('pollution');
  assert.match(cards.textContent, /Pollutant Ingress/);
  assert.match(cards.textContent, /Page 25/);
  assert.match(cards.textContent, /direct discharge/);
  await controller.selectTopic('myth');
  const card = cards.children[1];
  assert.match(card.children[2].textContent, /not presented as a widespread myth/i);
  assert.equal(card.children[4].textContent, 'Choose Myth or Fact to reveal the source-based answer.');
  const choiceRow = card.children[3];
  assert.deepEqual(choiceRow.children.map(button => button.textContent), ['Myth', 'Fact']);
  choiceRow.children[1].listeners.click();
  assert.match(card.children[4].textContent, /Fact — the cited GRBMP section states this/);
  assert.match(card.children[5].textContent, /six main headstreams/);
  assert.match(card.children[7].textContent, /Page 21/);
  i18n.setLanguage('hi', { persist: false, document: null, window: { dispatchEvent: event => listeners.get(event.type)?.(event) } });
  assert.match(cards.textContent, /स्रोत-आधारित पाठ/);
  assert.match(cards.textContent, /सही|तथ्य/);
  assert.match(cards.textContent, /GRBMP report/);
  i18n.setLanguage('en', { persist: false, document: null, window: null });
  if (oldAddEventListener === undefined) delete globalThis.addEventListener;
  else globalThis.addEventListener = oldAddEventListener;
});
