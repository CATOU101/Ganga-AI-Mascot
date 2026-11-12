const assert = require('node:assert/strict');
const test = require('node:test');
const appendAssistantTables = require('../chat-response.js');
const renderCpcbTables = require('../cpcb-tables.js');

class Element {
  constructor(name) { this.tagName = name; this.children = []; this.textContent = ''; this.attributes = {}; }
  appendChild(child) { this.children.push(child); return child; }
  setAttribute(name, value) { this.attributes[name] = value; }
}

const doc = { createElement: (name) => new Element(name) };
const find = (root, name) => root.children.flatMap((child) => [
  ...(child.tagName === name ? [child] : []), ...find(child, name),
]);

test('CPCB tables are appended to the visible assistant chat bubble', () => {
  const visibleBubble = new Element('div');
  const hiddenAnswer = new Element('div');
  const cardRow = { querySelector: (selector) => selector === '.bubble-content-text' ? visibleBubble : hiddenAnswer };
  const payload = [{ title: 'Water quality', columns: ['Location', 'pH', 'BOD', 'DO'], rows: [['Haridwar', '7.2', 'N/A', '6.1']], source: 'CPCB RTWQMS' }];

  appendAssistantTables(cardRow, payload, doc, renderCpcbTables);

  assert.equal(find(visibleBubble, 'table').length, 1);
  assert.equal(find(visibleBubble, 'td').length, 4);
  assert.equal(find(hiddenAnswer, 'table').length, 0);
  assert.equal(find(visibleBubble, 'p').some((item) => item.textContent.includes('CPCB RTWQMS')), true);
});

test('table insertion does nothing when there is no visible answer bubble', () => {
  let called = false;
  appendAssistantTables({ querySelector: () => null }, [{ columns: [], rows: [] }], doc, () => { called = true; });
  assert.equal(called, false);
});
