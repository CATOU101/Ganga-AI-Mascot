const assert = require("node:assert/strict");
const test = require("node:test");
const renderCpcbTables = require("../cpcb-tables.js");
const uiI18n = require('../ui-i18n.js');

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.attributes = {};
    this.textContent = "";
    this.className = "";
  }

  appendChild(child) {
    this.children.push(child);
    return child;
  }

  setAttribute(name, value) {
    this.attributes[name] = value;
  }
}

const fakeDocument = { createElement: (tagName) => new FakeElement(tagName) };

function descendants(root, tagName) {
  return root.children.flatMap((child) => [
    ...(child.tagName === tagName ? [child] : []),
    ...descendants(child, tagName),
  ]);
}

test("combined CPCB payload renders two accessible tables and source labels in chat", () => {
  const chat = new FakeElement("div");
  renderCpcbTables(chat, [
    {
      title: "Water quality",
      columns: ["Station", "pH", "BOD", "DO"],
      rows: [["Haridwar (UK55)", "7.5 (unitless)\n08 Nov 2026, 19:00 IST\nStatus: Meets Class B", "N/A\nTime unavailable\nStatus: Unavailable", "6.2 mg/l\n08 Nov 2026, 19:00 IST\nStatus: Outside Class B"]],
      source: "Source: CPCB RTWQMS. Class B organized outdoor-bathing screen; not a water-safety verdict.",
    },
    {
      title: "Water level and depth",
      columns: ["Station", "River stage (m)", "Depth (m)"],
      rows: [["Haridwar (UK55)", "282 m\n08 Nov 2026, 19:00 IST\nStatus: Unavailable", "0.3 m\n08 Nov 2026, 19:00 IST\nStatus: Unavailable"]],
      source: "Source: CPCB RTWQMS. No verified matching CWC gauge and current thresholds.",
    },
  ], fakeDocument);

  const tables = descendants(chat, "table");
  assert.equal(tables.length, 2);
  assert.deepEqual(descendants(tables[0], "th").map((cell) => cell.textContent), ["Station", "pH", "BOD", "DO"]);
  assert.deepEqual(descendants(tables[1], "th").map((cell) => cell.textContent), ["Station", "River stage (m)", "Depth (m)"]);
  assert.equal(descendants(chat, "td").some((cell) => cell.textContent.startsWith("N/A\nTime unavailable\nStatus: Unavailable")), true);
  assert.equal(descendants(chat, "td").some((cell) => cell.textContent.includes("Status: Meets Class B")), true);
  const readingCells = descendants(chat, "td").filter((cell) => !cell.textContent.includes("(UK55)"));
  assert.equal(readingCells.every((cell) => cell.textContent.split("\n").length === 3), true);
  assert.equal(descendants(chat, "td").every((cell) => !/(Reading:|Timestamp:|Source:|Threshold\/range:)/.test(cell.textContent)), true);
  assert.equal(descendants(chat, "p").filter((item) => item.className === "cpcb-table-source").length, 2);
  assert.equal(tables[0].attributes["aria-label"], "Water quality");
});

test("table values are inserted as text, not interpreted as HTML", () => {
  const chat = new FakeElement("div");
  const hostileValue = "<img src=x onerror=alert(1)>";
  renderCpcbTables(chat, [{ title: "CPCB", columns: ["Station"], rows: [[hostileValue]] }], fakeDocument);

  assert.equal(descendants(chat, "td")[0].textContent, hostileValue);
  assert.equal(descendants(chat, "img").length, 0);
});

test('CPCB interface labels and rule statuses follow website language while preserving source attribution', () => {
  uiI18n.setLanguage('hi', { persist: false, document: null, window: null });
  const chat = new FakeElement('div');
  renderCpcbTables(chat, [{
    title: 'Water quality', columns: ['Station', 'pH'],
    rows: [['Haridwar', '7.0\n08 Nov 2026, 19:00 IST\nStatus: Meets Class B']],
    source: 'Source: CPCB RTWQMS official source',
  }], fakeDocument);
  const table = descendants(chat, 'table')[0];
  assert.equal(descendants(table, 'th')[0].textContent, 'केंद्र');
  assert.match(descendants(chat, 'td')[1].textContent, /स्थिति: Class B मानदंड पूरा/);
  assert.equal(descendants(chat, 'p')[0].textContent, 'स्रोत: CPCB RTWQMS official source');
  uiI18n.setLanguage('en', { persist: false, document: null, window: null });
});
