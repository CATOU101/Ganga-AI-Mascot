const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const MultilingualKeyboard = require('../keyboard.js');

class Classes {
  constructor() { this.items = new Set(); }
  add(name) { this.items.add(name); }
  remove(name) { this.items.delete(name); }
  toggle(name, force) {
    const shouldAdd = force === undefined ? !this.items.has(name) : force;
    if (shouldAdd) this.items.add(name); else this.items.delete(name);
    return shouldAdd;
  }
}

class Button {
  constructor(lang = '') { this.dataset = { lang }; this.classList = new Classes(); this.listeners = {}; this.attributes = {}; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  setAttribute(name, value) { this.attributes[name] = value; }
}

class Container {
  constructor() {
    this.innerHTML = '';
    this.listeners = {};
    this.classList = new Classes();
    this.tabs = ['en', 'hi', 'kn', 'ta', 'te', 'bn', 'mr', 'gu', 'ml', 'pa', 'ur', 'or', 'as'].map((lang) => new Button(lang));
    this.keypad = { innerHTML: '' };
    this.toggle = new Button();
    this.controls = {
      '#vkKeypad': this.keypad,
      '#vkSwitchToggle': this.toggle,
      '#vkShiftToggle': new Button(),
      '#vkModeToggle': new Button(),
      '#vkEmojiToggle': new Button(),
      '.vk-space-key span': { textContent: '' },
    };
  }
  querySelector(selector) { return this.controls[selector] || null; }
  querySelectorAll(selector) { return selector === '.vk-lang-tab' ? this.tabs : []; }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  click(selector, dataset = {}) {
    const target = { dataset, closest: (wanted) => wanted === selector ? target : null };
    this.listeners.click({ target });
  }
}

class TextInput {
  constructor(value = '') { this.value = value; this.selectionStart = value.length; this.selectionEnd = value.length; this.events = []; this.focusCount = 0; }
  setRangeText(text, start, end, mode) {
    this.value = this.value.slice(0, start) + text + this.value.slice(end);
    const caret = start + text.length;
    this.selectionStart = mode === 'end' ? caret : this.selectionStart;
    this.selectionEnd = this.selectionStart;
  }
  setSelectionRange(start, end) { this.selectionStart = start; this.selectionEnd = end; }
  dispatchEvent(event) { this.events.push(event.type); }
  focus() { this.focusCount++; }
}

function setup() {
  const input = new TextInput();
  const container = new Container();
  const drawer = { hidden: true, attributes: {}, setAttribute(name, value) { this.attributes[name] = value; } };
  const toggleButton = new Button();
  let submitted = 0;
  const keyboard = new MultilingualKeyboard(input, { container, drawer, toggleButton, onEnter: () => submitted++ });
  return { input, container, drawer, toggleButton, keyboard, submitted: () => submitted };
}

test('keyboard implements all requested scripts and language switching preserves text', () => {
  const { keyboard, input, container } = setup();
  const languages = ['en', 'hi', 'te', 'bn', 'mr', 'gu', 'ml', 'pa', 'ur', 'or', 'as', 'ta', 'kn'];
  assert.deepEqual(Object.keys(keyboard.layouts), languages);
  input.value = 'existing';
  keyboard.setLanguage('ta');
  assert.equal(keyboard.currentLang, 'ta');
  assert.match(container.keypad.innerHTML, /க/);
  assert.equal(input.value, 'existing');
  container.click('.vk-lang-tab', { lang: 'kn' });
  assert.equal(keyboard.currentLang, 'kn');
  assert.match(container.keypad.innerHTML, /ಕ/);
});

test('every language layout inserts a character, space and backspace', () => {
  const { keyboard, input } = setup();
  for (const language of Object.keys(keyboard.layouts)) {
    keyboard.setLanguage(language);
    const key = keyboard.layouts[language].rows.flat().find((item) => !['⇧', '⌫'].includes(item));
    input.value = '';
    input.setSelectionRange(0, 0);
    keyboard.handleKeyPress(key);
    assert.equal(input.value, key, `${language} character insertion`);
    keyboard.handleKeyPress(' ');
    assert.equal(input.value, `${key} `, `${language} space insertion`);
    keyboard.handleKeyPress('⌫');
    assert.equal(input.value, key, `${language} backspace`);
  }
  keyboard.setLanguage('ur');
  assert.equal(keyboard.input.dir, 'rtl');
  keyboard.setLanguage('te');
  assert.equal(keyboard.input.dir, 'auto');
});

test('keyboard opens/closes its outer drawer and updates accessible toggle state', () => {
  const { keyboard, drawer, toggleButton, container } = setup();
  keyboard.open();
  assert.equal(drawer.hidden, false);
  assert.equal(drawer.attributes['aria-hidden'], 'false');
  assert.equal(toggleButton.attributes['aria-expanded'], 'true');
  assert.equal(container.classList.items.has('open'), true);
  keyboard.close();
  assert.equal(drawer.hidden, true);
  assert.equal(drawer.attributes['aria-hidden'], 'true');
  assert.equal(toggleButton.attributes['aria-expanded'], 'false');
  keyboard.toggle();
  assert.equal(drawer.hidden, false);
});

test('language keys, spaces, backspace and cursor insertion update the real input', () => {
  const { keyboard, input, container } = setup();
  keyboard.setLanguage('hi');
  for (const key of ['ग']) container.click('.vk-key', { key });
  container.click('#vkShiftToggle');
  container.click('.vk-key', { key: 'ं' });
  container.click('#vkShiftToggle');
  container.click('.vk-key', { key: 'ग' });
  container.click('#vkShiftToggle');
  container.click('.vk-key', { key: 'ा' });
  container.click('#vkShiftToggle');
  container.click('.vk-key', { key: ' ' });
  container.click('.vk-key', { key: 'न' });
  container.click('.vk-key', { key: 'द' });
  container.click('#vkShiftToggle');
  container.click('.vk-key', { key: 'ी' });
  assert.equal(input.value, 'गंगा नदी');
  container.click('.vk-key', { key: '⌫' });
  assert.equal(input.value, 'गंगा न');
  input.value = 'abcd';
  input.setSelectionRange(2, 2);
  keyboard.handleKeyPress('क');
  assert.equal(input.value, 'abकcd');
  assert.ok(input.events.length >= 5);
});

test('backspace removes a complete grapheme and Enter submits the chat form', () => {
  const { keyboard, input, container, submitted } = setup();
  input.value = 'river 🌊';
  input.setSelectionRange(input.value.length, input.value.length);
  keyboard.handleKeyPress('⌫');
  assert.equal(input.value, 'river ');
  container.click('#vkEnterKey');
  assert.equal(submitted(), 1);
});

test('website language selector is separate from the independent 13-language output and voice selectors', () => {
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  const header = html.match(/class="header-right-actions"[\s\S]*?<\/header>/)?.[0] || '';
  assert.match(header, /id="websiteLangSelect"/);
  assert.doesNotMatch(header, /Typed language|Auto detected/);
  const websiteSelect = html.match(/<select id="websiteLangSelect"[\s\S]*?<\/select>/)?.[0] || '';
  assert.deepEqual(Array.from(websiteSelect.matchAll(/<option value="([^"]+)"/g), (match) => match[1]), ['en', 'hi', 'kn', 'ta']);
  assert.doesNotMatch(html, /id="inputLangSelect"/);
  assert.doesNotMatch(html, /outputLangSelector|class="lang-btn"/);
  assert.doesNotMatch(html, /id="answerText"|id="notifBtn"/);
  assert.match(html, /id="themeToggleBtn"/);
  const i18n = fs.readFileSync(path.join(__dirname, '..', 'ui-i18n.js'), 'utf8');
  assert.match(i18n, /gangaWebsiteLanguage/);
  assert.match(i18n, /ganga-website-language-change/);
  const outputSelect = html.match(/<select id="outputLangSelect"[\s\S]*?<\/select>/)?.[0] || '';
  const languageCodes = ['en', 'hi', 'kn', 'ta', 'te', 'bn', 'mr', 'gu', 'ml', 'pa', 'ur', 'or', 'as'];
  assert.deepEqual(Array.from(outputSelect.matchAll(/<option value="([^"]+)"/g), (match) => match[1]), languageCodes);
  const voiceSelect = html.match(/<select id="voiceInputLangSelect"[\s\S]*?<\/select>/)?.[0] || '';
  assert.deepEqual(Array.from(voiceSelect.matchAll(/<option value="([^"]+)"/g), (match) => match[1]), languageCodes);
  const app = fs.readFileSync(path.join(__dirname, '..', 'app.js'), 'utf8');
  assert.match(app, /localStorage\.setItem\('gangaOutputLanguage', currentOutputLanguage\)/);
  assert.match(app, /localStorage\.getItem\('gangaOutputLanguage'\)/);
  assert.match(app, /localStorage\.setItem\('gangaVoiceInputLanguage', currentVoiceInputLanguage\)/);
  assert.match(app, /localStorage\.getItem\('gangaVoiceInputLanguage'\)/);
  assert.match(app, /input_language:\s*inputLanguage/);
  assert.match(app, /data\.question && data\.answer[\s\S]*?renderCompletedResponse\(data\.question, data\)/);
  for (const locale of ['te-IN', 'bn-IN', 'mr-IN', 'gu-IN', 'ml-IN', 'pa-IN', 'ur-IN', 'or-IN', 'as-IN']) {
    assert.ok(app.includes(locale), `voice locale ${locale} configured`);
  }
  assert.match(html, /multilingualKeyboardDrawer" class="multilingual-keyboard-drawer" hidden/);
});
