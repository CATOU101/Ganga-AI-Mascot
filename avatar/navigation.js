(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.GangaNavigation = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const ROUTES = new Set(['home', 'resources', 'awareness', 'settings', 'about']);

  function create({ document, window, onViewChange = () => {}, onQuizChange = () => {} }) {
    const buttons = Array.from(document.querySelectorAll('.sidebar-nav [data-nav]'));
    const views = Array.from(document.querySelectorAll('[data-app-view]'));
    let currentView = null;

    function showFromLocation(moveFocus = false) {
      const hash = window.location.hash.replace(/^#/, '').toLowerCase();
      const showQuiz = hash === 'quiz';
      const nextView = showQuiz ? 'home' : (ROUTES.has(hash) ? hash : 'home');
      views.forEach(view => { view.hidden = view.dataset.appView !== nextView; });
      buttons.forEach(button => {
        const active = button.dataset.nav === nextView;
        button.classList.toggle('active', active);
        if (active) button.setAttribute('aria-current', 'page');
        else button.removeAttribute('aria-current');
      });
      onQuizChange(showQuiz);
      if (currentView !== nextView) {
        currentView = nextView;
        onViewChange(nextView);
      }
      if (moveFocus) {
        const target = showQuiz
          ? document.getElementById('quizTitle')
          : document.querySelector(`[data-app-view="${nextView}"] h2`);
        if (target) {
          if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
          target.focus();
        }
      }
    }

    buttons.forEach(button => {
      button.addEventListener('click', () => {
        const target = ROUTES.has(button.dataset.nav) ? button.dataset.nav : 'home';
        const nextHash = `#${target}`;
        if (window.location.hash === nextHash) {
          showFromLocation(true);
          onViewChange(target);
        }
        else window.location.hash = nextHash;
      });
    });
    window.addEventListener('hashchange', () => showFromLocation(true));
    showFromLocation(false);
    return { currentView: () => currentView, refresh: () => showFromLocation(false) };
  }

  return { create, ROUTES };
});
