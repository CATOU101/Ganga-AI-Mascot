const assert = require('node:assert/strict');
const test = require('node:test');
const i18n = require('../ui-i18n.js');
const questions = require('../quiz-data.js');

class Node {
  constructor(attrs = {}) { this.attrs = { ...attrs }; this.textContent = ''; this.children = []; this.listeners = {}; }
  getAttribute(name) { return this.attrs[name] ?? null; }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  removeAttribute(name) { delete this.attrs[name]; }
  matches(selector) { return selector.includes('[data-i18n]') && Boolean(this.attrs['data-i18n']); }
  querySelectorAll() { return this.children; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
}

test('website language supports four local UI dictionaries with no missing entries or translation service calls', () => {
  assert.deepEqual(i18n.languages.map(item => item.code), ['en', 'hi', 'kn', 'ta']);
  for (const language of ['en', 'hi', 'kn', 'ta']) assert.deepEqual(i18n.missingKeys(language), []);
  const source = require('node:fs').readFileSync(require('node:path').join(__dirname, '..', 'ui-i18n.js'), 'utf8');
  assert.doesNotMatch(source, /fetch\s*\(|XMLHttpRequest|\.generate\s*\(/);
});

test('website preference persists independently and updates translated text and accessible attributes', () => {
  const text = new Node({ 'data-i18n': 'nav.resources' });
  const button = new Node({ 'data-i18n-title': 'theme.switchDark', 'data-i18n-aria-label': 'theme.switchDark' });
  const selector = { value: 'en', addEventListener() {} };
  const document = {
    documentElement: {}, title: '',
    querySelectorAll: () => [text, button],
    getElementById: id => id === 'websiteLangSelect' ? selector : null,
    querySelector: () => null,
  };
  const values = new Map([['gangaOutputLanguage', 'ta'], ['gangaVoiceInputLanguage', 'kn']]);
  const events = [];
  const window = {
    localStorage: { getItem: key => values.get(key), setItem: (key, value) => values.set(key, value) },
    CustomEvent: class { constructor(type, init) { this.type = type; this.detail = init.detail; } },
    dispatchEvent: event => events.push(event),
  };
  i18n.setLanguage('ta', { document, window });
  assert.equal(values.get('gangaWebsiteLanguage'), 'ta');
  assert.equal(values.get('gangaOutputLanguage'), 'ta');
  assert.equal(values.get('gangaVoiceInputLanguage'), 'kn');
  assert.equal(document.documentElement.lang, 'ta');
  assert.equal(selector.value, 'ta');
  assert.match(text.textContent, /கங்கை வளங்கள்/);
  assert.equal(button.getAttribute('title'), i18n.t('theme.switchDark'));
  assert.equal(button.getAttribute('aria-label'), i18n.t('theme.switchDark'));
  assert.equal(events.at(-1).type, 'ganga-website-language-change');
});

test('dynamic quiz text is localized while official source names and references stay unchanged', () => {
  i18n.setLanguage('kn', { persist: false, document: null, window: null });
  assert.equal(questions.length, 10);
  for (const question of questions) {
    const localized = i18n.translateQuiz(question);
    assert.notEqual(localized.question, question.question);
    assert.equal(localized.source.title, question.source.title);
    assert.equal(localized.source.reference, question.source.reference);
    assert.equal(localized.options.length, question.options.length);
  }
  i18n.setLanguage('en', { persist: false, document: null, window: null });
});
