const test = require('node:test');
const assert = require('node:assert/strict');
const { create } = require('../navigation.js');

function node(dataset = {}) {
  const listeners = {};
  const attributes = {};
  const classes = new Set();
  return {
    dataset,
    hidden: false,
    listeners,
    attributes,
    classList: {
      toggle(name, enabled) { if (enabled) classes.add(name); else classes.delete(name); },
      contains(name) { return classes.has(name); },
    },
    addEventListener(type, callback) { listeners[type] = callback; },
    setAttribute(name, value) { attributes[name] = value; },
    removeAttribute(name) { delete attributes[name]; },
    hasAttribute(name) { return Object.hasOwn(attributes, name); },
    focus() { this.focused = true; },
  };
}

function setup(initialHash = '') {
  const buttons = ['home', 'resources', 'awareness', 'settings'].map(key => node({ nav: key }));
  const views = ['home', 'resources', 'awareness', 'settings', 'about'].map(key => node({ appView: key }));
  const quizTitle = node();
  const events = {};
  const document = {
    querySelectorAll(selector) {
      if (selector === '.sidebar-nav [data-nav]') return buttons;
      if (selector === '[data-app-view]') return views;
      return [];
    },
    getElementById(id) { return id === 'quizTitle' ? quizTitle : null; },
    querySelector(selector) {
      const match = selector.match(/\[data-app-view="([^"]+)"\] h2/);
      if (!match) return null;
      return views.find(view => view.dataset.appView === match[1])?.heading || null;
    },
  };
  const location = { _hash: initialHash, get hash() { return this._hash; }, set hash(value) { this._hash = value; events.hashchange?.(); } };
  const window = { location, addEventListener(type, callback) { events[type] = callback; } };
  const changes = [];
  const quiz = [];
  const controller = create({ document, window, onViewChange: value => changes.push(value), onQuizChange: value => quiz.push(value) });
  return { buttons, views, quizTitle, location, changes, quiz, controller, document, window };
}

test('navigation defaults to Home, opens separate pages, and returns without replacing Home', () => {
  const state = setup();
  assert.equal(state.views.find(view => view.dataset.appView === 'home').hidden, false);
  assert.equal(state.buttons[0].attributes['aria-current'], 'page');
  state.buttons[1].listeners.click();
  assert.equal(state.location.hash, '#resources');
  assert.equal(state.views.find(view => view.dataset.appView === 'resources').hidden, false);
  state.buttons[0].listeners.click();
  assert.equal(state.views.find(view => view.dataset.appView === 'home').hidden, false);
  assert.deepEqual(state.changes, ['home', 'resources', 'home']);
});

test('refresh routes directly to About and quiz hash opens the existing Home quiz overlay', () => {
  const about = setup('#about');
  assert.equal(about.views.find(view => view.dataset.appView === 'about').hidden, false);
  const quiz = setup('#quiz');
  assert.equal(quiz.views.find(view => view.dataset.appView === 'home').hidden, false);
  assert.equal(quiz.quiz.at(-1), true);
});

test('page containers explicitly honor hidden state despite grid display styles', () => {
  const fs = require('node:fs');
  const path = require('node:path');
  const css = fs.readFileSync(path.join(__dirname, '..', 'style.css'), 'utf8');
  assert.match(css, /\.home-view\[hidden\]\s*\{\s*display:\s*none\s*!important;/);
  assert.match(css, /\.app-page-view\[hidden\]\s*\{\s*display:\s*none\s*!important;/);
});

test('selecting the already active page invokes its loader again for retry', () => {
  const state = setup('#resources');
  let calls = 0;
  const navigation = create({
    document: state.document,
    window: state.window,
    onViewChange: () => { calls += 1; },
  });
  const resourcesButton = state.buttons.find(button => button.dataset.nav === 'resources');
  resourcesButton.listeners.click();
  assert.equal(navigation.currentView(), 'resources');
  assert.equal(calls, 2);
});
