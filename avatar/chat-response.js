(function attachAssistantTableRenderer(root, factory) {
  const appendAssistantTables = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = appendAssistantTables;
  if (root) root.appendAssistantTables = appendAssistantTables;
})(typeof window !== 'undefined' ? window : globalThis, function createAssistantTableRenderer() {
  return function appendAssistantTables(cardRow, tables, documentObject, tableRenderer) {
    if (!cardRow || !Array.isArray(tables) || tables.length === 0 || typeof tableRenderer !== 'function') return;
    const visibleAnswer = cardRow.querySelector('.bubble-content-text');
    if (visibleAnswer) tableRenderer(visibleAnswer, tables, documentObject);
  };
});
