(function attachCpcbTableRenderer(root, factory) {
  const renderCpcbTables = factory(root);
  if (typeof module !== "undefined" && module.exports) module.exports = renderCpcbTables;
  if (root) root.renderCpcbTables = renderCpcbTables;
})(typeof window !== "undefined" ? window : globalThis, function createCpcbTableRenderer(root) {
  let languageListenerInstalled = false;
  return function renderCpcbTables(container, tables, documentObject) {
    const doc = documentObject || document;
    const i18n = globalThis.GangaUII18n;
    const english = { 'table.waterQuality': 'Water quality', 'table.waterLevel': 'Water level and depth', 'table.station': 'Station', 'table.parameter': 'Parameter', 'table.value': 'Value', 'table.status': 'Status', 'table.timestamp': 'Timestamp', 'table.source': 'Source' };
    const translate = (key) => i18n ? i18n.t(key) : (english[key] || key);
    if (!container || !Array.isArray(tables) || tables.length === 0) return;

    const group = doc.createElement("section");
    group.className = "cpcb-table-group";
    group.__cpcbTableData = tables;
    group.__cpcbDocument = doc;
    tables.forEach((tableData) => {
      if (!tableData || !Array.isArray(tableData.columns) || !Array.isArray(tableData.rows)) return;
      const block = doc.createElement("div");
      block.className = "cpcb-table-block";
      const title = doc.createElement("h4");
      title.className = "cpcb-table-title";
      const rawTitle = String(tableData.title || 'CPCB readings');
      title.textContent = i18n && /water\s*quality/i.test(rawTitle) ? translate('table.waterQuality') : i18n && /water\s*(level|stage|depth)/i.test(rawTitle) ? translate('table.waterLevel') : rawTitle;
      block.appendChild(title);

      const scroll = doc.createElement("div");
      scroll.className = "cpcb-table-scroll";
      const table = doc.createElement("table");
      table.className = "cpcb-data-table";
      table.setAttribute("aria-label", title.textContent);
      const thead = doc.createElement("thead");
      const headerRow = doc.createElement("tr");
      tableData.columns.forEach((column) => {
        const cell = doc.createElement("th");
        cell.scope = "col";
        const label = String(column);
        const standard = { Station: 'table.station', Parameter: 'table.parameter', Value: 'table.value', Status: 'table.status', Timestamp: 'table.timestamp', Source: 'table.source', 'River stage (m)': 'table.riverStage', 'Depth (m)': 'table.depth' };
        cell.textContent = standard[label] ? translate(standard[label]) : label;
        headerRow.appendChild(cell);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = doc.createElement("tbody");
      tableData.rows.forEach((row) => {
        const rowElement = doc.createElement("tr");
        tableData.columns.forEach((_, index) => {
          const cell = doc.createElement("td");
          const rawValue = String(Array.isArray(row) ? (row[index] ?? "N/A") : "N/A");
          const statusKeys = { 'meets class b criterion': 'table.meetsClassB', 'meets class b': 'table.meetsClassB', 'outside class b criterion': 'table.outsideClassB', 'outside class b': 'table.outsideClassB', unavailable: 'table.unavailable', 'stale reading': 'table.stale', 'below warning': 'table.belowWarning', 'at/above danger': 'table.atDanger', warning: 'table.warning', danger: 'table.danger', fresh: 'table.fresh' };
          cell.textContent = i18n ? rawValue.replace(/Status:\s*(Meets Class B criterion|Meets Class B|Outside Class B criterion|Outside Class B|Unavailable|Stale reading|Below warning|At\/above danger|Warning|Danger|Fresh)/gi, (_, label) => `${i18n.t('table.status')}: ${i18n.t(statusKeys[label.toLowerCase()])}`) : rawValue;
          rowElement.appendChild(cell);
        });
        tbody.appendChild(rowElement);
      });
      table.appendChild(tbody);
      scroll.appendChild(table);
      block.appendChild(scroll);

      if (tableData.source) {
        const source = doc.createElement("p");
        source.className = "cpcb-table-source";
        const sourceText = String(tableData.source).replace(/^Source:\s*/i, '');
        source.textContent = i18n ? i18n.t('cpcb.source', { source: sourceText }) : `Source: ${sourceText}`;
        block.appendChild(source);
      }
      group.appendChild(block);
    });
    if (group.children.length > 0) {
      container.appendChild(group);
      if (!languageListenerInstalled && root && typeof root.addEventListener === 'function') {
        languageListenerInstalled = true;
        root.addEventListener('ganga-website-language-change', () => {
          const groups = root.document?.querySelectorAll('.cpcb-table-group') || [];
          groups.forEach(oldGroup => {
            const parent = oldGroup.parentNode;
            if (!parent || !oldGroup.__cpcbTableData) return;
            const temporary = oldGroup.__cpcbDocument.createElement('div');
            renderCpcbTables(temporary, oldGroup.__cpcbTableData, oldGroup.__cpcbDocument);
            const replacement = temporary.firstElementChild;
            if (replacement) parent.replaceChild(replacement, oldGroup);
          });
        });
      }
    }
  };
});
