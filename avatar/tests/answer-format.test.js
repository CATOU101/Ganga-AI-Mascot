const assert = require('node:assert/strict');
const test = require('node:test');
const formatAnswer = require('../answer-format.js');

test('keeps paragraphs and list structure instead of converting every line to bullets', () => {
  const html = formatAnswer('First paragraph.\n\nSecond paragraph.\n\n- One\n- Two');
  assert.match(html, /<p>First paragraph\.<\/p>/);
  assert.match(html, /<p>Second paragraph\.<\/p>/);
  assert.match(html, /<ul><li>One<\/li><li>Two<\/li><\/ul>/);
});

test('renders Markdown comparison tables as tables', () => {
  const html = formatAnswer('| Item | Value |\n| --- | --- |\n| A | 1 |\n| B | 2 |');
  assert.match(html, /<table class="answer-markdown-table">/);
  assert.match(html, /<th>Item<\/th>/);
  assert.match(html, /<td>2<\/td>/);
});

test('escapes markup and does not create executable HTML', () => {
  const html = formatAnswer('<img src=x onerror=alert(1)>\n\n| x | y |\n| --- | --- |\n| <script> | ok |');
  assert.doesNotMatch(html, /<img|<script>/);
  assert.match(html, /&lt;img/);
  assert.match(html, /&lt;script&gt;/);
});
