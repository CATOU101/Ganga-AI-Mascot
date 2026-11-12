(function attachThemeController(root, factory) {
  const themeController = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = themeController;
  if (root && root.document) themeController.initialize(root.document);
})(typeof globalThis !== 'undefined' ? globalThis : this, function createThemeController() {
  const STORAGE_KEY = 'gangaTheme';
  const DARK_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="4"></circle><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"></path></svg>';
  const LIGHT_ICON = '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';

  function readPreference(storage) {
    try {
      const saved = storage && storage.getItem(STORAGE_KEY);
      return saved === 'dark' || saved === 'light' ? saved : null;
    } catch (_) {
      return null;
    }
  }

  function setTheme(documentObject, theme, button) {
    documentObject.documentElement.dataset.theme = theme;
    if (!button) return;
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    const icon = theme === 'dark' ? DARK_ICON : LIGHT_ICON;
    if (button.id === 'settingsThemeToggleBtn') {
      const iconSlot = button.querySelector('.settings-theme-icon');
      const label = button.querySelector('.settings-theme-label');
      if (iconSlot) iconSlot.innerHTML = icon;
      if (label) label.textContent = `Switch to ${nextTheme} mode`;
    } else {
      button.innerHTML = icon;
    }
    button.setAttribute('aria-label', `Switch to ${nextTheme} mode`);
    button.setAttribute('title', `Switch to ${nextTheme} mode`);
    button.setAttribute('aria-pressed', String(theme === 'dark'));
  }

  function initialize(documentObject) {
    let storage = null;
    let matchMedia = null;
    try { storage = globalThis.localStorage; } catch (_) {}
    try { matchMedia = globalThis.matchMedia && globalThis.matchMedia.bind(globalThis); } catch (_) {}
    return create(documentObject, storage, matchMedia);
  }

  function create(documentObject, storage, matchMedia) {
    let preference = readPreference(storage);
    let mediaQuery = null;
    try {
      mediaQuery = matchMedia ? matchMedia('(prefers-color-scheme: dark)') : null;
    } catch (_) {}

    let currentTheme = preference || (mediaQuery && mediaQuery.matches ? 'dark' : 'light');
    let buttons = [];
    setTheme(documentObject, currentTheme, null);

    function refreshButton() {
      buttons = ['themeToggleBtn', 'settingsThemeToggleBtn']
        .map(id => documentObject.getElementById(id))
        .filter(Boolean);
      buttons.forEach(button => {
        setTheme(documentObject, currentTheme, button);
        if (button.dataset.themeBound) return;
        button.dataset.themeBound = 'true';
        button.addEventListener('click', toggle);
      });
    }

    function renderTheme() {
      if (!buttons.length) {
        setTheme(documentObject, currentTheme, null);
        return;
      }
      buttons.forEach(button => setTheme(documentObject, currentTheme, button));
    }

    function toggle() {
      currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
      preference = currentTheme;
      try { if (storage) storage.setItem(STORAGE_KEY, currentTheme); } catch (_) {}
      renderTheme();
    }

    if (mediaQuery) {
      const onSystemThemeChange = (event) => {
        if (preference) return;
        currentTheme = event.matches ? 'dark' : 'light';
        renderTheme();
      };
      if (typeof mediaQuery.addEventListener === 'function') {
        mediaQuery.addEventListener('change', onSystemThemeChange);
      } else if (typeof mediaQuery.addListener === 'function') {
        mediaQuery.addListener(onSystemThemeChange);
      }
    }

    if (documentObject.readyState === 'loading') {
      documentObject.addEventListener('DOMContentLoaded', refreshButton, { once: true });
    } else {
      refreshButton();
    }

    return {
      getTheme: () => currentTheme,
      toggle,
    };
  }

  return { create, initialize };
});
