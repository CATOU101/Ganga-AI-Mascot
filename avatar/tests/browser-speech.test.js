const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const { resolveVoice } = require('../browser-speech.js');

test('first and subsequent browser speech resolve the selected exact-language voice for every supported locale', async () => {
  for (const locale of ['en-IN', 'hi-IN', 'bn-IN', 'ta-IN', 'te-IN', 'kn-IN', 'ml-IN', 'gu-IN', 'mr-IN', 'pa-IN', 'ur-IN', 'or-IN', 'as-IN']) {
    let voices = [];
    const listeners = new Set();
    const synthesis = {
      getVoices: () => voices,
      addEventListener: (_name, listener) => listeners.add(listener),
      removeEventListener: (_name, listener) => listeners.delete(listener),
    };
    const firstPlayback = resolveVoice(synthesis, locale, 200);
    const selectedVoice = { name: `${locale} voice`, lang: locale };
    voices = [selectedVoice];
    for (const listener of listeners) listener();
    assert.equal(await firstPlayback, selectedVoice, `first playback ${locale}`);
    assert.equal(listeners.size, 0);
    assert.equal(await resolveVoice(synthesis, locale), selectedVoice, `next playback ${locale}`);
  }
});

test('missing exact-language voice returns unavailable without substituting another locale', async () => {
  const synthesis = {
    getVoices: () => [{ name: 'English voice', lang: 'en-IN' }],
    addEventListener() {},
    removeEventListener() {},
  };
  assert.equal(await resolveVoice(synthesis, 'ta-IN', 5), null);
});

test('voice fallback is connected to UI and voice warning remains in the composer status area', () => {
  const avatarDir = path.join(__dirname, '..');
  const html = fs.readFileSync(path.join(avatarDir, 'index.html'), 'utf8');
  const app = fs.readFileSync(path.join(avatarDir, 'app.js'), 'utf8');
  assert.match(html, /browser-speech\.js/);
  assert.match(html, /id="voiceStatusMsg"[^>]*aria-live="polite"/);
  assert.match(app, /await window\.GangaBrowserSpeech\.resolveVoice/);
  assert.match(app, /voiceStatusMsg\.textContent = ''/);
  assert.match(app, /Browser speech playback failed/);
});
