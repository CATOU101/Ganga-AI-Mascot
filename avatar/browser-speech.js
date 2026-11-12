(function attachBrowserSpeech(root, factory) {
  const browserSpeech = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = browserSpeech;
  if (root) root.GangaBrowserSpeech = browserSpeech;
})(typeof globalThis !== 'undefined' ? globalThis : this, function createBrowserSpeech() {
  async function resolveVoice(synthesis, locale, timeoutMs = 1500) {
    if (!synthesis || typeof synthesis.getVoices !== 'function') return null;
    const matches = () => synthesis.getVoices().find(
      voice => (voice.lang || '').toLowerCase() === locale.toLowerCase()
    ) || null;

    const initial = matches();
    if (initial) return initial;
    if (typeof synthesis.addEventListener !== 'function') return null;

    return new Promise(resolve => {
      let settled = false;
      const finish = voice => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        synthesis.removeEventListener?.('voiceschanged', onVoicesChanged);
        resolve(voice);
      };
      const onVoicesChanged = () => {
        const voice = matches();
        if (voice) finish(voice);
      };
      const timer = setTimeout(() => finish(matches()), timeoutMs);
      synthesis.addEventListener('voiceschanged', onVoicesChanged);
      // The list may have populated between the initial check and listener setup.
      onVoicesChanged();
    });
  }

  return { resolveVoice };
});
