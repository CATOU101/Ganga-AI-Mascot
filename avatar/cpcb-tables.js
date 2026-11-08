(function attachCpcbTableRenderer(root, factory) {
  const renderCpcbTables = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = renderCpcbTables;
  if (root) root.renderCpcbTables = renderCpcbTables;
})(typeof window !== "undefined" ? window : globalThis, function createCpcbTableRenderer() {
  return function renderCpcbTables(container, tables, documentObject) {
    const doc = documentObject || document;
    if (!container || !Array.isArray(tables) || tables.length === 0) return;

    const group = doc.createElement("section");
    group.className = "cpcb-table-group";
    tables.forEach((tableData) => {
      if (!tableData || !Array.isArray(tableData.columns) || !Array.isArray(tableData.rows)) return;
      const block = doc.createElement("div");
      block.className = "cpcb-table-block";
      const title = doc.createElement("h4");
      title.className = "cpcb-table-title";
      title.textContent = String(tableData.title || "CPCB readings");
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
        cell.textContent = String(column);
        headerRow.appendChild(cell);
      });
      thead.appendChild(headerRow);
      table.appendChild(thead);

      const tbody = doc.createElement("tbody");
      tableData.rows.forEach((row) => {
        const rowElement = doc.createElement("tr");
        tableData.columns.forEach((_, index) => {
          const cell = doc.createElement("td");
          cell.textContent = String(Array.isArray(row) ? (row[index] ?? "N/A") : "N/A");
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
        source.textContent = `Source: ${tableData.source}`;
        block.appendChild(source);
      }
      group.appendChild(block);
    });
    if (group.children.length > 0) container.appendChild(group);
  };
});
