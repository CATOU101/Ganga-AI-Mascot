const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const themeController = require('../theme.js');

function setup({ saved = null, systemDark = false } = {}) {
  const root = { dataset: {} };
  const button = {
    dataset: {},
    attributes: {},
    listeners: {},
    setAttribute(name, value) { this.attributes[name] = value; },
    addEventListener(name, listener) { this.listeners[name] = listener; },
  };
  const documentObject = {
    documentElement: root,
    readyState: 'complete',
    getElementById: (id) => id === 'themeToggleBtn' ? button : null,
  };
  const values = new Map(saved === null ? [] : [['gangaTheme', saved]]);
  const storage = {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
  };
  let systemChange;
  const matchMedia = () => ({
    matches: systemDark,
    addEventListener: (name, callback) => { if (name === 'change') systemChange = callback; },
  });
  const controller = themeController.create(documentObject, storage, matchMedia);
  return { root, button, values, controller, changeSystem: (matches) => systemChange?.({ matches }) };
}

test('theme follows system preference initially and toggle persists the opposite theme', () => {
  const { root, button, values } = setup({ systemDark: true });
  assert.equal(root.dataset.theme, 'dark');
  assert.equal(button.attributes['aria-label'], 'Switch to light mode');
  assert.equal(button.attributes['aria-pressed'], 'true');

  button.listeners.click();
  assert.equal(root.dataset.theme, 'light');
  assert.equal(values.get('gangaTheme'), 'light');
  assert.equal(button.attributes['aria-label'], 'Switch to dark mode');
  assert.equal(button.attributes['aria-pressed'], 'false');
  assert.match(button.innerHTML, /M21 12\.79/);
});

test('saved preference overrides system preference and prevents later system changes overriding it', () => {
  const { root, button, changeSystem } = setup({ saved: 'light', systemDark: true });
  assert.equal(root.dataset.theme, 'light');
  changeSystem(false);
  assert.equal(root.dataset.theme, 'light');

  button.listeners.click();
  assert.equal(root.dataset.theme, 'dark');
  changeSystem(false);
  assert.equal(root.dataset.theme, 'dark');
  assert.match(button.innerHTML, /M12 2v2/);
});

test('unsaved theme continues to follow system preference changes', () => {
  const { root, changeSystem } = setup({ systemDark: false });
  assert.equal(root.dataset.theme, 'light');
  changeSystem(true);
  assert.equal(root.dataset.theme, 'dark');
});

test('page wires the toggle and dark palette across shared interface surfaces', () => {
  const avatarDir = path.join(__dirname, '..');
  const html = fs.readFileSync(path.join(avatarDir, 'index.html'), 'utf8');
  const css = fs.readFileSync(path.join(avatarDir, 'style.css'), 'utf8');
  assert.match(html, /theme\.js\?v=/);
  assert.match(html, /id="themeToggleBtn"/);
  assert.doesNotMatch(html, /id="notifBtn"|id="answerText"|outputLangSelector/);
  assert.match(css, /:root\[data-theme="dark"\]/);
  assert.match(css, /\.sidebar-nav[\s\S]*?background-color: var\(--bg-surface\)/);
  assert.match(css, /\.assistant-card[\s\S]*?background-color: var\(--bg-surface\)/);
  assert.match(css, /\.info-modal-card[\s\S]*?background-color: var\(--bg-surface\)/);
  assert.match(css, /\.multilingual-keyboard-drawer[\s\S]*?background: var\(--bg-surface\)/);
});
