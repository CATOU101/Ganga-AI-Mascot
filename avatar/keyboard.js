/**
 * Multilingual Virtual On-Screen Keyboard for Ganga AI Mascot
 * 
 * Supports full native script layouts for Indian languages:
 * - Hindi (हिंदी)
 * - English (English QWERTY)
 * - Bengali (বাংলা)
 * - Tamil (தமிழ்)
 * - Telugu (తెలుగు)
 * - Kannada (ಕನ್ನಡ)
 * - Malayalam (മലയാളം)
 * - Gujarati (ગુજરાતી)
 * - Punjabi (ਪੰਜਾਬੀ Gurmukhi)
 * - Odia (ଓଡ଼ିଆ)
 * - Marathi (मराठी)
 * 
 * Preserves cursor position, never clears current message, supports physical keyboard concurrently.
 */

class MultilingualKeyboard {
  constructor(inputElement, options = {}) {
    this.input = inputElement;
    this.container = options.container || document.getElementById('virtualKeyboardContainer');
    this.currentLang = options.defaultLanguage || 'en';
    this.isShift = false;
    this.isNumberMode = false;
    this.isOpen = false;
    this.onEnter = options.onEnter || null;

    this.layouts = {
      // 1. ENGLISH (QWERTY) - Default
      en: {
        name: 'English',
        rows: [
          ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
          ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
          ['⇧', 'z', 'x', 'c', 'v', 'b', 'n', 'm', '?', '⌫']
        ],
        shiftRows: [
          ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
          ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
          ['⇧', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '!', '⌫']
        ],
        spaceLabel: 'Space'
      },

      // 2. HINDI (हिंदी - Devanagari)
      hi: {
        name: 'Hindi (हिंदी)',
        rows: [
          ['क', 'ख', 'ग', 'घ', 'ङ', 'च', 'छ', 'ज', 'झ', 'ञ', 'ट', 'ठ', 'ड', 'ढ', 'ण'],
          ['त', 'थ', 'द', 'ध', 'न', 'प', 'फ', 'ब', 'भ', 'म', 'य', 'र', 'ल', 'व'],
          ['श', 'ष', 'स', 'ह', 'क्ष', 'त्र', 'ज्ञ', 'ॐ', '।', '?', '⌫']
        ],
        vowels: [
          ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ', 'अं', 'अः'],
          ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', 'ं', 'ः', 'ँ', '्', '़'],
          ['१', '२', '३', '४', '५', '६', '७', '८', '९', '०', '।', '⌫']
        ],
        spaceLabel: 'स्पेस'
      },

      // 3. BENGALI (বাংলা)
      bn: {
        name: 'বাংলা',
        rows: [
          ['ক', 'খ', 'গ', 'ঘ', 'ঙ', 'চ', 'ছ', 'জ', 'ঝ', 'ঞ', 'ট', 'ঠ', 'ড', 'ঢ', 'ণ'],
          ['ত', 'থ', 'দ', 'ধ', 'ন', 'প', 'ফ', 'ব', 'ভ', 'ম', 'য', 'র', 'ল', 'ব'],
          ['শ', 'ষ', 'স', 'হ', 'ড়', 'ঢ়', 'য়', 'ৎ', 'ং', 'ঃ', 'ঁ', '।', '⌫']
        ],
        vowels: [
          ['অ', 'আ', 'ই', 'ঈ', 'উ', 'ঊ', 'ঋ', 'এ', 'ঐ', 'ও', 'ঔ'],
          ['া', 'ি', 'ী', 'ু', 'ূ', 'ৃ', 'ে', 'ৈ', 'ো', 'ৌ', '্', '১', '২', '৩', '৪', '৫'],
          ['৬', '৭', '৮', '৯', '০', '!', '?', '⌫']
        ],
        spaceLabel: 'স্পেস'
      },

      // 4. TAMIL (தமிழ்)
      ta: {
        name: 'தமிழ்',
        rows: [
          ['க', 'ங', 'ச', 'ஞ', 'ட', 'ண', 'த', 'ந', 'ப', 'ம', 'ய', 'ர', 'ல', 'வ'],
          ['ழ', 'ள', 'ற', 'ன', 'ஜ', 'ஷ', 'ஸ', 'ஹ', 'க்ஷ', 'ஸ்ரீ', '?', '⌫']
        ],
        vowels: [
          ['அ', 'ஆ', 'இ', 'ஈ', 'உ', 'ஊ', 'எ', 'ஏ', 'ஐ', 'ஒ', 'ஓ', 'ஔ', 'ஃ'],
          ['ா', 'ி', 'ீ', 'ு', 'ூ', 'ெ', 'ே', 'ை', 'ொ', 'ோ', 'ௌ', '்', '⌫']
        ],
        spaceLabel: 'இடைவெளி'
      },

      // 5. TELUGU (తెలుగు)
      te: {
        name: 'తెలుగు',
        rows: [
          ['క', 'ఖ', 'గ', 'ఘ', 'ఙ', 'చ', 'ఛ', 'జ', 'ఝ', 'ఞ', 'ట', 'ఠ', 'డ', 'ఢ', 'ణ'],
          ['త', 'థ', 'ద', 'ధ', 'న', 'ప', 'ఫ', 'బ', 'భ', 'మ', 'య', 'ర', 'ల', 'వ'],
          ['శ', 'ష', 'స', 'హ', 'ళ', 'క్ష', 'ఱ', 'ం', 'ః', '?', '⌫']
        ],
        vowels: [
          ['అ', 'ఆ', 'ఇ', 'ఈ', 'ఉ', 'ఊ', 'ఋ', 'ఎ', 'ఏ', 'ఐ', 'ఒ', 'ఓ', 'ఔ'],
          ['ా', 'ి', 'ీ', 'ు', 'ూ', 'ృ', 'ె', 'ే', 'ై', 'ొ', 'ో', 'ౌ', '్', '⌫']
        ],
        spaceLabel: 'స్పేస్'
      },

      // 6. KANNADA (ಕನ್ನಡ)
      kn: {
        name: 'ಕನ್ನಡ',
        rows: [
          ['ಕ', 'ಖ', 'ಗ', 'ಘ', 'ಙ', 'ಚ', 'ಛ', 'ಜ', 'ಝ', 'ಞ', 'ಟ', 'ಠ', 'ಡ', 'ಢ', 'ಣ'],
          ['ತ', 'ಥ', 'ದ', 'ಧ', 'ನ', 'ಪ', 'ಫ', 'ಬ', 'ಭ', 'ಮ', 'ಯ', 'ರ', 'ಲ', 'ವ'],
          ['ಶ', 'ಷ', 'ಸ', 'ಹ', 'ಳ', 'ಕ್ಷ', 'ಂ', 'ಃ', '?', '⌫']
        ],
        vowels: [
          ['ಅ', 'ಆ', 'ಇ', 'ಈ', 'ಉ', 'ಊ', 'ಋ', 'ಎ', 'ಏ', 'ಐ', 'ಒ', 'ಓ', 'ಔ'],
          ['ಾ', 'ಿ', 'ೀ', 'ು', 'ೂ', 'ೃ', 'ೆ', 'ೇ', 'ೈ', 'ೊ', 'ೋ', 'ೌ', '್', '⌫']
        ],
        spaceLabel: 'ಸ್ಪೇಸ್'
      },

      // 7. MALAYALAM (മലയാളം)
      ml: {
        name: 'മലയാളം',
        rows: [
          ['ക', 'ഖ', 'ഗ', 'ഘ', 'ങ', 'ച', 'ഛ', 'ജ', 'ഝ', 'ഞ', 'ട', 'ഠ', 'ഡ', 'ഢ', 'ണ'],
          ['ത', 'ഥ', 'ദ', 'ധ', 'ന', 'പ', 'ഫ', 'ബ', 'ഭ', 'മ', 'യ', 'ര', 'ല', 'വ'],
          ['ശ', 'ഷ', 'സ', 'ഹ', 'ള', 'ഴ', 'റ', 'ം', 'ഃ', '?', '⌫']
        ],
        vowels: [
          ['അ', 'ആ', 'ഇ', 'ഈ', 'ഉ', 'ഊ', 'ഋ', 'എ', 'ഏ', 'ഐ', 'ഒ', 'ഓ', 'ഔ'],
          ['ാ', 'ി', 'ീ', 'ു', 'ൂ', 'ൃ', 'െ', 'േ', 'ൈ', 'ൊ', 'ോ', 'ൌ', '്', '⌫']
        ],
        spaceLabel: 'സ്പേസ്'
      },

      // 8. GUJARATI (ગુજરાતી)
      gu: {
        name: 'ગુજરાતી',
        rows: [
          ['ક', 'ખ', 'ગ', 'ઘ', 'ઙ', 'ચ', 'છ', 'જ', 'ઝ', 'ઞ', 'ટ', 'ઠ', 'ડ', 'ઢ', 'ણ'],
          ['ત', 'થ', 'દ', 'ધ', 'ન', 'પ', 'ફ', 'બ', 'ભ', 'મ', 'ય', 'ર', 'લ', 'વ'],
          ['શ', 'ષ', 'સ', 'હ', 'ળ', 'ક્ષ', 'જ્ઞ', '।', '?', '⌫']
        ],
        vowels: [
          ['અ', 'આ', 'ઇ', 'ઈ', 'ઉ', 'ઊ', 'ઋ', 'એ', 'ઐ', 'ઓ', 'ઔ', 'અં', 'અઃ'],
          ['ા', 'િ', 'ી', 'ુ', 'ૂ', 'ૃ', 'ે', 'ૈ', 'ો', 'ૌ', 'ં', 'ઃ', '્', '⌫']
        ],
        spaceLabel: 'સ્પેસ'
      },

      // 9. PUNJABI (ਪੰਜਾਬੀ Gurmukhi)
      pa: {
        name: 'ਪੰਜਾਬੀ',
        rows: [
          ['ਕ', 'ਖ', 'ਗ', 'ਘ', 'ਙ', 'ਚ', 'ਛ', 'ਜ', 'ਝ', 'ਞ', 'ਟ', 'ਠ', 'ਡ', 'ਢ', 'ਣ'],
          ['ਤ', 'ਥ', 'ਦ', 'ਧ', 'ਨ', 'ਪ', 'ਫ', 'ਬ', 'ਭ', 'ਮ', 'ਯ', 'ਰ', 'ਲ', 'ਵ'],
          ['ੜ', 'ਸ', 'ਹ', 'ਖ਼', 'ਗ਼', 'ਜ਼', 'ਫ਼', 'ਲ਼', '।', '?', '⌫']
        ],
        vowels: [
          ['ਅ', 'ਆ', 'ਇ', 'ਈ', 'ਉ', 'ਊ', 'ਏ', 'ਐ', 'ਓ', 'ਔ'],
          ['ਾ', 'ਿ', 'ੀ', 'ੁ', 'ੂ', 'ੇ', 'ੈ', 'ੋ', 'ੌ', 'ੰ', 'ੱ', '਼', '੍', '⌫']
        ],
        spaceLabel: 'ਸਪੇਸ'
      },

      // 10. ODIA (ଓଡ଼ିଆ)
      or: {
        name: 'ଓଡ଼ିଆ',
        rows: [
          ['କ', 'ଖ', 'ଗ', 'ଘ', 'ଙ', 'ଚ', 'ଛ', 'ଜ', 'ଝ', 'ଞ', 'ଟ', 'ଠ', 'ଡ', 'ଢ', 'ଣ'],
          ['ତ', 'ଥ', 'ଦ', 'ଧ', 'ନ', 'ପ', 'ଫ', 'ବ', 'ଭ', 'ମ', 'ଯ', 'ର', 'ଳ', 'ୱ'],
          ['ଶ', 'ଷ', 'ସ', 'ହ', 'କ୍ଷ', 'ୟ', 'ଡ଼', 'ଢ଼', '।', '?', '⌫']
        ],
        vowels: [
          ['ଅ', 'ଆ', 'ଇ', 'ଈ', 'ଉ', 'ଊ', 'ଋ', 'ଏ', 'ଐ', 'ଓ', 'ଔ'],
          ['ା', 'ି', 'ୀ', 'ୁ', 'ୂ', 'ୃ', 'େ', 'ୈ', 'ୋ', 'ୌ', 'ଂ', 'ଃ', '୍', '⌫']
        ],
        spaceLabel: 'ସ୍ପେସ୍'
      },

      // 11. MARATHI (मराठी)
      mr: {
        name: 'मराठी',
        rows: [
          ['क', 'ख', 'ग', 'घ', 'ङ', 'च', 'छ', 'ज', 'झ', 'ञ', 'ट', 'ठ', 'ड', 'ढ', 'ण'],
          ['त', 'थ', 'द', 'ध', 'न', 'प', 'फ', 'ब', 'भ', 'म', 'य', 'र', 'ल', 'व'],
          ['श', 'ष', 'स', 'ह', 'ळ', 'क्ष', 'ज्ञ', 'ॐ', '।', '?', '⌫']
        ],
        vowels: [
          ['अ', 'आ', 'इ', 'ई', 'उ', 'ऊ', 'ऋ', 'ए', 'ऐ', 'ओ', 'औ', 'अं', 'अः'],
          ['ा', 'ि', 'ी', 'ु', 'ू', 'ृ', 'े', 'ै', 'ो', 'ौ', 'ं', 'ः', 'ँ', '्', 'ॅ', 'ॉ', '⌫']
        ],
        spaceLabel: 'स्पेस'
      }
    };

    // Numbers & Symbols Layout
    this.symbolLayout = [
      ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
      ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'],
      ['-', '_', '=', '+', '[', ']', '{', '}', '\\', '|'],
      [';', ':', '"', '\'', '<', '>', ',', '.', '/', '⌫']
    ];

    // Popular Emojis
    this.emojiLayout = [
      ['🙏', '🌊', '🌿', '🌱', '💧', '🐟', '🇮🇳', '❤️', '👍', '😊'],
      [' गंगा', ' स्वच्छ', ' निर्मल', ' अविरल', ' नमामि', ' हर हर गंगे', '⌫']
    ];

    this.init();
  }

  init() {
    if (!this.container) return;
    this.render();
    this.attachEventListeners();
  }

  render() {
    this.container.innerHTML = `
      <div class="virtual-keyboard-card">
        <div class="vk-header">
          <div class="vk-title">
            <span class="vk-icon" aria-hidden="true">⌨</span>
            <span class="vk-label">Multilingual Keyboard</span>
          </div>
          <div class="vk-header-actions">
            <label class="vk-toggle-label">
              <input type="checkbox" id="vkSwitchToggle" ${this.isOpen ? 'checked' : ''} />
              <span class="vk-switch-slider"></span>
              <span class="vk-switch-text">On-Screen Keyboard</span>
            </label>
            <button type="button" id="vkCloseBtn" class="vk-close-btn" title="Close Keyboard" aria-label="Close on-screen keyboard">×</button>
          </div>
        </div>

        <div class="vk-language-tabs" id="vkLangTabs">
          ${Object.keys(this.layouts).map(langKey => `
            <button type="button" class="vk-lang-tab ${this.currentLang === langKey ? 'active' : ''}" data-lang="${langKey}">
              ${this.layouts[langKey].name}
            </button>
          `).join('')}
        </div>

        <div class="vk-keypad" id="vkKeypad">
          <!-- Dynamically populated rows -->
        </div>

        <div class="vk-bottom-bar">
          <button type="button" class="vk-special-btn ${this.isNumberMode ? 'active' : ''}" id="vkModeToggle" title="Numbers and Symbols">
            ${this.isNumberMode ? 'ABC' : '123'}
          </button>
          <button type="button" class="vk-special-btn ${this.isShift ? 'active' : ''}" id="vkShiftToggle" title="Vowels / Matras or Shift">
            ${this.currentLang === 'en' ? '⇧ Shift' : (this.isShift ? 'व्यंजन' : 'स्वर/मात्रा')}
          </button>
          <button type="button" class="vk-special-btn" id="vkEmojiToggle" title="Ganga Emojis & Quick Words">
            😀
          </button>
          <button type="button" class="vk-key vk-space-key" data-key=" ">
            <span>${this.layouts[this.currentLang]?.spaceLabel || 'Space'}</span>
          </button>
          <button type="button" class="vk-key vk-nav-key" id="vkNavLeft" title="Cursor Left">←</button>
          <button type="button" class="vk-key vk-nav-key" id="vkNavRight" title="Cursor Right">→</button>
          <button type="button" class="vk-key vk-enter-key" id="vkEnterKey" title="Send Question">
            <span>⏎</span>
          </button>
        </div>
      </div>
    `;

    this.renderKeypad();
  }

  renderKeypad() {
    const keypad = this.container.querySelector('#vkKeypad');
    if (!keypad) return;

    let rowsToRender = [];
    const langData = this.layouts[this.currentLang] || this.layouts['hi'];

    if (this.isNumberMode) {
      rowsToRender = this.symbolLayout;
    } else if (this.isEmojiMode) {
      rowsToRender = this.emojiLayout;
    } else if (this.isShift) {
      if (this.currentLang === 'en') {
        rowsToRender = langData.shiftRows || langData.rows;
      } else {
        rowsToRender = langData.vowels || langData.rows;
      }
    } else {
      rowsToRender = langData.rows;
    }

    keypad.innerHTML = rowsToRender.map(row => `
      <div class="vk-row">
        ${row.map(k => {
          const isBksp = k === '⌫';
          const isShiftKey = k === '⇧';
          return `
            <button type="button" class="vk-key ${isBksp ? 'vk-bksp-key' : ''} ${isShiftKey ? 'vk-shift-key' : ''}" data-key="${k}">
              ${k}
            </button>
          `;
        }).join('')}
      </div>
    `).join('');
  }

  attachEventListeners() {
    // 1. Language tab switching
    this.container.addEventListener('click', (e) => {
      const tab = e.target.closest('.vk-lang-tab');
      if (tab) {
        const lang = tab.dataset.lang;
        this.setLanguage(lang);
        return;
      }

      // 2. Virtual key press
      const keyBtn = e.target.closest('.vk-key');
      if (keyBtn) {
        const key = keyBtn.dataset.key;
        if (key) {
          this.handleKeyPress(key);
        }
        return;
      }

      // 3. Close button
      if (e.target.closest('#vkCloseBtn')) {
        this.close();
        return;
      }

      // 4. Mode toggle (123 / ABC)
      if (e.target.closest('#vkModeToggle')) {
        this.isNumberMode = !this.isNumberMode;
        this.isEmojiMode = false;
        this.updateControlButtons();
        this.renderKeypad();
        return;
      }

      // 5. Shift / Vowel toggle
      if (e.target.closest('#vkShiftToggle')) {
        this.isShift = !this.isShift;
        this.isNumberMode = false;
        this.isEmojiMode = false;
        this.updateControlButtons();
        this.renderKeypad();
        return;
      }

      // 6. Emoji toggle
      if (e.target.closest('#vkEmojiToggle')) {
        this.isEmojiMode = !this.isEmojiMode;
        this.isNumberMode = false;
        this.isShift = false;
        this.updateControlButtons();
        this.renderKeypad();
        return;
      }

      // 7. Left arrow
      if (e.target.closest('#vkNavLeft')) {
        this.moveCursor(-1);
        return;
      }

      // 8. Right arrow
      if (e.target.closest('#vkNavRight')) {
        this.moveCursor(1);
        return;
      }

      // 9. Enter button
      if (e.target.closest('#vkEnterKey')) {
        if (typeof this.onEnter === 'function') {
          this.onEnter();
        } else if (this.input && this.input.form) {
          if (typeof this.input.form.requestSubmit === 'function') {
            this.input.form.requestSubmit();
          } else {
            this.input.form.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
          }
        }
        return;
      }
    });

    // Header Switch toggle
    const toggle = this.container.querySelector('#vkSwitchToggle');
    if (toggle) {
      toggle.addEventListener('change', () => {
        if (toggle.checked) {
          this.open();
        } else {
          this.close();
        }
      });
    }
  }

  handleKeyPress(key) {
    if (!this.input) return;

    const start = this.input.selectionStart ?? this.input.value.length;
    const end = this.input.selectionEnd ?? this.input.value.length;

    if (key === '⌫') {
      if (start === end && start > 0) {
        this.input.setRangeText('', start - 1, end, 'end');
      } else if (start !== end) {
        this.input.setRangeText('', start, end, 'end');
      }
    } else if (key === '⇧') {
      this.isShift = !this.isShift;
      this.renderKeypad();
      return;
    } else {
      this.input.setRangeText(key, start, end, 'end');
    }

    // Trigger input event for real-time reactivity
    this.input.dispatchEvent(new Event('input', { bubbles: true }));
    this.input.focus();
  }

  moveCursor(offset) {
    if (!this.input) return;
    const current = this.input.selectionStart ?? this.input.value.length;
    const next = Math.max(0, Math.min(this.input.value.length, current + offset));
    this.input.setSelectionRange(next, next);
    this.input.focus();
  }

  setLanguage(lang) {
    if (!this.layouts[lang]) return;
    this.currentLang = lang;
    this.isNumberMode = false;
    this.isShift = false;
    this.isEmojiMode = false;

    // Update active tab style
    const tabs = this.container.querySelectorAll('.vk-lang-tab');
    tabs.forEach(tab => {
      tab.classList.toggle('active', tab.dataset.lang === lang);
    });

    this.updateControlButtons();
    this.renderKeypad();

    // Do NOT clear or reset input text!
    if (this.input) {
      this.input.focus();
    }
  }

  updateControlButtons() {
    const shiftBtn = this.container.querySelector('#vkShiftToggle');
    const modeBtn = this.container.querySelector('#vkModeToggle');
    const emojiBtn = this.container.querySelector('#vkEmojiToggle');
    const spaceBtn = this.container.querySelector('.vk-space-key span');

    if (shiftBtn) {
      shiftBtn.classList.toggle('active', this.isShift);
      if (this.currentLang === 'en') {
        shiftBtn.textContent = '⇧ Shift';
      } else {
        shiftBtn.textContent = this.isShift ? 'व्यंजन' : 'स्वर/मात्रा';
      }
    }

    if (modeBtn) {
      modeBtn.classList.toggle('active', this.isNumberMode);
      modeBtn.textContent = this.isNumberMode ? 'ABC' : '123';
    }

    if (emojiBtn) {
      emojiBtn.classList.toggle('active', Boolean(this.isEmojiMode));
    }

    if (spaceBtn) {
      spaceBtn.textContent = this.layouts[this.currentLang]?.spaceLabel || 'Space';
    }
  }

  open() {
    this.isOpen = true;
    this.container.classList.add('open');
    this.container.style.display = 'block';
    const toggle = this.container.querySelector('#vkSwitchToggle');
    if (toggle) toggle.checked = true;

    // Notify keyboard button in input
    const toggleBtn = document.getElementById('keyboardToggleBtn');
    if (toggleBtn) {
      toggleBtn.classList.add('active');
      toggleBtn.setAttribute('aria-expanded', 'true');
    }

    if (this.input) {
      this.input.focus();
    }
  }

  close() {
    this.isOpen = false;
    this.container.classList.remove('open');
    this.container.style.display = 'none';
    const toggle = this.container.querySelector('#vkSwitchToggle');
    if (toggle) toggle.checked = false;

    const toggleBtn = document.getElementById('keyboardToggleBtn');
    if (toggleBtn) {
      toggleBtn.classList.remove('active');
      toggleBtn.setAttribute('aria-expanded', 'false');
    }

    if (this.input) {
      this.input.focus();
    }
  }

  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }
}

window.MultilingualKeyboard = MultilingualKeyboard;

