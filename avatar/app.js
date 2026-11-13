/**
 * Main Application Orchestrator for Ganga AI Mascot UI
 * Redesigned Premium White-Themed Dashboard & Multilingual Interaction
 * 
 * Pipeline:
 * - Automatic typed-input language detection and selectable output language
 * - Output languages: English and 12 Indian languages
 * - Multilingual Virtual On-Screen Keyboard with native script layouts
 * - Chacha Chaudhary 3D Avatar (28 Skeletal Animations, Pedestal, Automatic States & Lip-Sync)
 * - Modern AI Chat Stream with User bubbles, Assistant cards, Waveform Audio Player, and Verified Sources
 */

document.addEventListener('DOMContentLoaded', () => {
  const uiI18n = window.GangaUII18n;
  const t = (key, values = {}) => uiI18n ? uiI18n.t(key, values) : key;
  const setUiText = (element, key, values = {}) => {
    if (!element) return;
    if (uiI18n) uiI18n.setText(element, key, values);
    else element.textContent = t(key, values);
  };
  const clearUiText = (element) => {
    if (!element) return;
    element.textContent = '';
    element.removeAttribute('data-i18n');
    element.removeAttribute('data-i18n-values');
  };
  // 1. Initialize 3D Avatar Mascot Controller
  const mascot = new MascotController();

  // Centralized Event Bus for Human-Like Conversation & Animation Coordination (Phase 5)
  const avatarEventBus = {
    listeners: {},
    on(event, callback) {
      if (!this.listeners[event]) this.listeners[event] = [];
      this.listeners[event].push(callback);
    },
    emit(event, payload) {
      const list = this.listeners[event] || [];
      for (const cb of list) {
        try { cb(payload); } catch (e) { console.warn(`[EventBus] Error in ${event} listener:`, e); }
      }
    }
  };
  window.avatarEventBus = avatarEventBus;

  // 2. DOM Elements
  const chatMessagesList = document.getElementById('chatMessagesList');
  const askForm = document.getElementById('askForm');
  const questionInput = document.getElementById('questionInput');
  const micBtn = document.getElementById('micBtn');
  const submitBtn = document.getElementById('submitBtn');
  const keyboardToggleBtn = document.getElementById('keyboardToggleBtn');
  const virtualKeyboardContainer = document.getElementById('virtualKeyboardContainer');

  const outputLangSelect = document.getElementById('outputLangSelect');
  const voiceInputLangSelect = document.getElementById('voiceInputLangSelect');
  const settingsOutputLangSelect = document.getElementById('settingsOutputLangSelect');
  const settingsVoiceInputLangSelect = document.getElementById('settingsVoiceInputLangSelect');
  const responseLangBadge = document.getElementById('responseLangBadge');
  const modeBadge = document.getElementById('modeBadge');
  const thinkingWave = document.getElementById('thinkingWave');
  const voiceStatusMsg = document.getElementById('voiceStatusMsg');
  const vizFill = document.getElementById('vizFill');
  const mascotSpeechBubble = document.getElementById('mascotSpeechBubble');

  // Status Indicator Pills
  const statePillIdle = document.getElementById('statePillIdle');
  const statePillListening = document.getElementById('statePillListening');
  const statePillThinking = document.getElementById('statePillThinking');
  const statePillSpeaking = document.getElementById('statePillSpeaking');

  // Quiz and page views
  const chatView = document.getElementById('chatView');
  const quizView = document.getElementById('quiz');
  const quizNavButton = document.getElementById('quizNavButton');

  // 3. Application State (Default: English)
  const supportedOutputLanguages = new Set(['en', 'hi', 'kn', 'ta', 'te', 'bn', 'mr', 'gu', 'ml', 'pa', 'ur', 'or', 'as']);
  let currentOutputLanguage = 'en';
  let currentVoiceInputLanguage = 'en';
  let detectedTextLanguage = 'auto';
  try {
    const savedOutputLanguage = localStorage.getItem('gangaOutputLanguage');
    if (supportedOutputLanguages.has(savedOutputLanguage)) currentOutputLanguage = savedOutputLanguage;
  } catch (_) {}
  try {
    const savedVoiceLanguage = localStorage.getItem('gangaVoiceInputLanguage');
    if (supportedOutputLanguages.has(savedVoiceLanguage)) currentVoiceInputLanguage = savedVoiceLanguage;
  } catch (_) {}
  let currentState = 'IDLE';

  // Audio Playback & Synchronization State
  let activeAudio = null;
  let activeAudioPlayerBar = null;
  let lipSyncAnimationId = null;
  let lastAudioUrl = null;
  let speechAttemptId = 0;

  // Microphone Recording State (MediaRecorder)
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;

  // 4. Initialize Multilingual Virtual On-Screen Keyboard
  let virtualKeyboard = null;
  if (window.MultilingualKeyboard && virtualKeyboardContainer) {
    virtualKeyboard = new window.MultilingualKeyboard(questionInput, {
      container: virtualKeyboardContainer,
      drawer: document.getElementById('multilingualKeyboardDrawer'),
      toggleButton: keyboardToggleBtn,
      defaultLanguage: 'en',
      onEnter: () => {
        if (askForm) {
          if (typeof askForm.requestSubmit === 'function') {
            askForm.requestSubmit();
          } else {
            askForm.dispatchEvent(new Event('submit', { cancelable: true, bubbles: true }));
          }
        }
      }
    });

    if (keyboardToggleBtn) {
      keyboardToggleBtn.addEventListener('click', () => {
        virtualKeyboard.toggle();
      });
    }
  }

  // Typed queries are script-detected by the backend; the keyboard locale is independent.
  const outputLanguageControls = [outputLangSelect, settingsOutputLangSelect].filter(Boolean);
  outputLanguageControls.forEach(control => {
    control.value = currentOutputLanguage;
    control.addEventListener('change', () => {
      currentOutputLanguage = supportedOutputLanguages.has(control.value) ? control.value : 'en';
      outputLanguageControls.forEach(item => { item.value = currentOutputLanguage; });
      try { localStorage.setItem('gangaOutputLanguage', currentOutputLanguage); } catch (_) {}
      updateLangBadge();
      updateChachaGreeting();
    });
  });

  const voiceLanguageControls = [voiceInputLangSelect, settingsVoiceInputLangSelect].filter(Boolean);
  voiceLanguageControls.forEach(control => {
    control.value = currentVoiceInputLanguage;
    control.addEventListener('change', () => {
      currentVoiceInputLanguage = supportedOutputLanguages.has(control.value) ? control.value : 'en';
      voiceLanguageControls.forEach(item => { item.value = currentVoiceInputLanguage; });
      try { localStorage.setItem('gangaVoiceInputLanguage', currentVoiceInputLanguage); } catch (_) {}
    });
  });

  function updateLangBadge() {
    if (responseLangBadge) {
      const outLabel = currentOutputLanguage.toUpperCase();
      setUiText(responseLangBadge, 'chat.typedOutput', {
        input: detectedTextLanguage.toUpperCase(), output: outLabel
      });
    }
  }

  function updateChachaGreeting() {
    if (currentState === 'IDLE' && mascotSpeechBubble) {
      const greetings = {
        hi: "नमस्ते! मैं चाचा चौधरी हूँ। गंगा नदी व संरक्षण के बारे में सही जानकारी के लिए मुझसे पूछें!",
        en: "Namaste! I am Chacha Chaudhary. Ask me anything about River Ganga, conservation, and water quality!",
        ta: "வணக்கம்! நான் சாச்சா சவுத்ரி. கங்கை நதி மற்றும் பாதுகாப்பு பற்றிய விவரங்களுக்கு என்னைக் கேளுங்கள்!",
        kn: "ನಮಸ್ಕಾರ! ನಾನು ಚಾಚಾ ಚೌಧರಿ. ಗಂಗಾ ನದಿ ಸಂರಕ್ಷಣೆ ಕುರಿತು ಮಾಹಿತಿಗಾಗಿ ನನ್ನನ್ನು ಕೇಳಿ!",
        te: "నమస్కారం! గంగా నది మరియు పరిరక్షణ గురించి నన్ను అడగండి!",
        bn: "নমস্কার! গঙ্গা নদী ও সংরক্ষণ সম্পর্কে আমাকে জিজ্ঞাসা করুন!",
        mr: "नमस्कार! गंगा नदी आणि संवर्धनाबद्दल मला विचारा!",
        gu: "નમસ્તે! ગંગા નદી અને સંરક્ષણ વિશે મને પૂછો!",
        ml: "നമസ്കാരം! ഗംഗാ നദിയെയും സംരക്ഷണത്തെയും കുറിച്ച് ചോദിക്കൂ!",
        pa: "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਗੰਗਾ ਨਦੀ ਅਤੇ ਸੰਭਾਲ ਬਾਰੇ ਮੈਨੂੰ ਪੁੱਛੋ!",
        ur: "السلام علیکم! دریائے گنگا اور اس کے تحفظ کے بارے میں پوچھیں!",
        or: "ନମସ୍କାର! ଗଙ୍ଗା ନଦୀ ଓ ସଂରକ୍ଷଣ ବିଷୟରେ ପଚାରନ୍ତୁ!",
        as: "নমস্কাৰ! গংগা নদী আৰু সংৰক্ষণৰ বিষয়ে সুধক!",
      };
      mascotSpeechBubble.textContent = greetings[currentOutputLanguage] || greetings.en;
    }
  }

  // 7. Synchronize Avatar State Machine & Status Indicator Pills
  function updateLiveStatusLabel(state) {
    const liveStatusText = document.getElementById('liveStatusText');
    const keys = {
      IDLE: 'status.idle', LISTENING: 'status.listening', THINKING: 'status.thinking',
      PROCESSING: 'status.analyzing', SPEAKING: 'status.speaking', ERROR: 'status.error'
    };
    if (liveStatusText) setUiText(liveStatusText, keys[state] || 'status.idle');
  }

  function setState(state, options = {}) {
    currentState = state;

    if (statePillIdle) statePillIdle.classList.toggle('active', state === 'IDLE');
    if (statePillListening) statePillListening.classList.toggle('active', state === 'LISTENING');
    if (statePillThinking) statePillThinking.classList.toggle('active', state === 'THINKING' || state === 'PROCESSING');
    if (statePillSpeaking) statePillSpeaking.classList.toggle('active', state === 'SPEAKING');

    // Update Live State Indicator Badge in Avatar Header
    const liveStatusText = document.getElementById('liveStatusText');
    const liveStatusDot = document.getElementById('liveStatusDot');
    updateLiveStatusLabel(state);
    if (liveStatusDot) {
      liveStatusDot.className = 'live-status-dot dot-' + state.toLowerCase();
    }

    if (state === 'THINKING' || state === 'PROCESSING') {
      if (thinkingWave) thinkingWave.style.display = 'flex';
      if (submitBtn) submitBtn.disabled = true;
    } else {
      if (thinkingWave) thinkingWave.style.display = 'none';
      if (submitBtn) submitBtn.disabled = false;
    }

    // Forward state to 3D Mascot Controller
    if (mascot && mascot.setState) {
      mascot.setState(state, options);
    }
  }

  // Interactive Clicks on State Indicator Pills
  if (statePillIdle) statePillIdle.addEventListener('click', () => { stopCurrentSpeech(); setState('IDLE'); });
  if (statePillListening) statePillListening.addEventListener('click', () => {
    if (isRecording) stopMicrophoneRecording();
    else startMicrophoneRecording();
  });
  if (statePillThinking) statePillThinking.addEventListener('click', () => {
    stopCurrentSpeech();
    setState('THINKING');
    setTimeout(() => { if (currentState === 'THINKING') setState('IDLE'); }, 2500);
  });
  if (statePillSpeaking) statePillSpeaking.addEventListener('click', () => {
    if (activeAudio) {
      activeAudio.currentTime = 0;
      activeAudio.play();
      setState('SPEAKING', { gesture: 'talking' });
    } else {
      setState('SPEAKING', { gesture: 'talking' });
      setTimeout(() => setState('IDLE'), 2000);
    }
  });

  // 8. Form Submission (Typed Question Pipeline)
  if (askForm) {
    askForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = questionInput.value.trim();
      if (!question) return;

      questionInput.value = '';
      if (virtualKeyboard && window.innerWidth < 768) {
        virtualKeyboard.close();
      }

      await processQuestion(question);
    });
  }

  // Click on Sample Question Pills
  document.addEventListener('click', (e) => {
    const pill = e.target.closest('.sample-prompt-pill');
    if (pill) {
      const prompt = pill.dataset.promptKey ? t(pill.dataset.promptKey) : pill.dataset.prompt;
      if (prompt) {
        processQuestion(prompt);
      }
    }
  });

  // 9. Main Question Pipeline (Question -> User Bubble -> RAG Brain -> Assistant Card)
  async function processQuestion(question, inputLanguage = null) {
    if (currentState === 'SPEAKING' || currentState === 'THINKING') {
      stopCurrentSpeech();
    }

    avatarEventBus.emit('response_started', { question, inputLanguage });

    // Append User Message Bubble to stream
    appendUserMessage(question);

    // Append Temporary Assistant Loading Card
    const loadingCardId = 'loadingCard_' + Date.now();
    appendLoadingAssistantCard(loadingCardId);

    setState('THINKING');
    scrollToBottom();

    const t_start = performance.now();

    try {
      // Call Integration Server /api/integration/ask
      const response = await fetch('/api/integration/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: question,
          input_language: inputLanguage,
          output_language: currentOutputLanguage
        })
      });

      if (!response.ok) {
        let detail = `Server returned status ${response.status}`;
        try {
          const errorBody = await response.json();
          if (typeof errorBody.detail === 'string') detail = errorBody.detail;
        } catch (_) {}
        throw new Error(detail);
      }

      const t_response = performance.now();
      const data = await response.json();
      avatarEventBus.emit('response_completed', { data, latencyMs: t_response - t_start });
      detectedTextLanguage = data.input_language || 'auto';
      updateLangBadge();

      // Replace Loading card with full formatted Assistant Message Card
      replaceLoadingWithResponse(loadingCardId, data, t_start, t_response);

    } catch (err) {
      console.error('[Frontend] Error querying Brain API:', err);
      setState('ERROR');
      replaceLoadingWithError(loadingCardId, t('chat.requestFailed'));
      setTimeout(() => setState('IDLE'), 2500);
    }
  }

  // 10. Message Stream Helpers
  function getFormattedTime() {
    const now = new Date();
    const locale = { en: 'en-IN', hi: 'hi-IN', kn: 'kn-IN', ta: 'ta-IN' }[uiI18n?.getLanguage?.()] || 'en-IN';
    return now.toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit' });
  }

  function appendUserMessage(text) {
    if (!chatMessagesList) return;

    const row = document.createElement('div');
    row.className = 'message-row user-row';
    row.innerHTML = `
      <div class="user-thumb-box" aria-hidden="true">👤</div>
      <div class="message-bubble user-bubble">
        <div class="bubble-text-body">${escapeHtml(text)}</div>
        <span class="bubble-timestamp">${getFormattedTime()}</span>
      </div>
    `;
    chatMessagesList.appendChild(row);
  }

  function appendLoadingAssistantCard(cardId) {
    if (!chatMessagesList) return;

    const row = document.createElement('div');
    row.className = 'message-row assistant-row';
    row.id = cardId;
    row.innerHTML = `
      <div class="avatar-thumb-box">
        <img src="08_Final/validation_renders/Face_Thinking.png" alt="Chacha Thinking" data-i18n-alt="avatar.thinkingTitle" class="chacha-thumb-img" onerror="this.onerror=null;this.src='08_Final/validation_renders/Face_Happy.png';" />
      </div>
      <div class="message-bubble assistant-card">
        <div class="bubble-header-bar">
          <div class="assistant-meta-left">
            <span class="assistant-name">Chacha Chaudhary</span>
            <span class="verified-tag" data-i18n="status.analyzing">Analyzing Corpus</span>
          </div>
          <span class="bubble-timestamp">${getFormattedTime()}</span>
        </div>
        <div class="bubble-content-text">
          <div class="thinking-loader-row">
            <div class="thinking-dots">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
            <span class="thinking-msg-text" data-i18n="chat.consulting">Consulting verified GRBMP knowledge base...</span>
          </div>
        </div>
      </div>
    `;
    chatMessagesList.appendChild(row);
    uiI18n?.applySubtree(row);
  }

  function replaceLoadingWithResponse(cardId, data, t_start = null, t_response = null) {
    const cardRow = document.getElementById(cardId);
    if (!cardRow) return;

    const answer = data.answer || data.text || t('chat.noResponse');
    const mode = data.mode || "grounded";
    const emotion = (data.emotion || "happy").toLowerCase();
    const gesture = (data.gesture || "explaining").toLowerCase();
    const citations = data.citations || [];
    const tables = data.tables || [];

    // Format text with clean bullet list if multiple sentences or points
    const formattedHtml = formatAnswerHtml(answer);

    // Audio payload check
    let audioSrc = null;
    if (data.audio_data_base64) {
      audioSrc = `data:audio/wav;base64,${data.audio_data_base64}`;
    } else if (data.audio) {
      audioSrc = (data.audio.startsWith('data:') || data.audio.startsWith('http') || data.audio.startsWith('/')) 
        ? data.audio 
        : `data:audio/wav;base64,${data.audio}`;
    }

    cardRow.innerHTML = `
      <div class="avatar-thumb-box">
        <img src="08_Final/validation_renders/Face_Happy.png" alt="Chacha Avatar" class="chacha-thumb-img" onerror="this.onerror=null;this.src='08_Final/validation_renders/Face_Happy.png';" />
      </div>
      <div class="message-bubble assistant-card">
        <div class="bubble-header-bar">
          <div class="assistant-meta-left">
            <span class="assistant-name">Chacha Chaudhary</span>
            <span class="verified-tag" data-i18n="${mode === 'grounded' ? 'chat.verifiedRag' : 'chat.gangaGuide'}">${escapeHtml(t(mode === 'grounded' ? 'chat.verifiedRag' : 'chat.gangaGuide'))}</span>
          </div>
          <span class="bubble-timestamp">${getFormattedTime()}</span>
        </div>
        <div class="bubble-content-text">
          ${formattedHtml}
        </div>

        <!-- Verified Sources Collapsible Accordion -->
        ${renderCitationsAccordion(citations)}

        <!-- In-Bubble Neural Audio Player Bar -->
        ${audioSrc ? renderAudioPlayerBar(audioSrc) : ''}
      </div>
    `;

    uiI18n?.applySubtree(cardRow);

    // Structured CPCB data belongs to the visible assistant message.
    if (window.appendAssistantTables) {
      window.appendAssistantTables(cardRow, tables, document, window.renderCpcbTables);
    }

    // Attach Citations Toggle Listener
    const accordion = cardRow.querySelector('.sources-accordion');
    if (accordion) {
      const toggleBtn = accordion.querySelector('.sources-toggle-btn');
      if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
          accordion.classList.toggle('open');
        });
      }
    }

    // Attach Audio Player Listeners
    if (audioSrc) {
      attachAudioPlayerControls(cardRow, audioSrc, data, gesture, t_start, t_response);
    }

    // Synchronize 3D Mascot State
    mascot.setState('SPEAKING', { emotion: emotion, gesture: gesture });

    // Autoplay Speech & Rhubarb Lip-Sync
    if (audioSrc) {
      playProductionSpeech(data, audioSrc, data.spoken_text || answer, gesture, t_start, t_response, cardRow);
    } else if (voiceStatusMsg && data.spoken_text) {
      playProductionSpeech(data, null, data.spoken_text || answer, gesture, t_start, t_response, cardRow);
    }

    scrollToBottom();
  }

  function replaceLoadingWithError(cardId, errorMessage) {
    const cardRow = document.getElementById(cardId);
    if (!cardRow) return;

    cardRow.innerHTML = `
      <div class="avatar-thumb-box">
        <img src="08_Final/validation_renders/Face_SadConfused.png" alt="Chacha Confused" class="chacha-thumb-img" onerror="this.onerror=null;this.src='08_Final/validation_renders/Face_Happy.png';" />
      </div>
      <div class="message-bubble assistant-card" style="border-color: var(--danger-border);">
        <div class="bubble-header-bar">
          <span class="assistant-name" style="color: var(--text-danger);">Chacha Chaudhary</span>
          <span class="verified-tag" data-i18n="chat.notice" style="background-color: var(--danger-bg); color: var(--text-danger);">${escapeHtml(t('chat.notice'))}</span>
        </div>
        <div class="bubble-content-text" data-i18n="chat.requestFailed" style="color: var(--text-danger);">
          ${escapeHtml(errorMessage)}
        </div>
      </div>
    `;
    uiI18n?.applySubtree(cardRow);
    scrollToBottom();
  }

  function formatAnswerHtml(answer) {
    return window.formatAssistantAnswer
      ? window.formatAssistantAnswer(answer)
      : `<p>${escapeHtml(answer).replace(/\n/g, '<br>')}</p>`;
  }

  function renderCitationsAccordion(citations) {
    if (!citations || citations.length === 0) {
      return '';
    }

    return `
      <div class="sources-accordion">
        <button type="button" class="sources-toggle-btn" aria-expanded="false">
          <span>📚 <span data-i18n="${citations.some((item) => item.source_type === 'external') ? 'chat.sources' : 'chat.verifiedSources'}">${escapeHtml(t(citations.some((item) => item.source_type === 'external') ? 'chat.sources' : 'chat.verifiedSources'))}</span> (${citations.length})</span>
          <span class="sources-chevron" aria-hidden="true">▾</span>
        </button>
        <div class="sources-list">
          ${citations.map(c => {
            const externalUrl = c.source_type === 'external' && typeof c.url === 'string' && /^https:\/\/[a-z0-9.-]+\.wikipedia\.org\//i.test(c.url);
            return `
            <div class="source-item-card">
              <span class="source-pdf-badge">${c.source_type === 'external' ? 'WEB' : 'PDF'}</span>
              ${externalUrl ? `<a class="source-title-text" href="${escapeHtml(c.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(c.source || t('chat.externalSource'))}</a>` : `<span class="source-title-text">${escapeHtml(c.source || c.file_name || t('chat.grbmpDocument'))}</span>`}
              <span class="source-meta-text">${c.page ? `p. ${c.page}` : ''}</span>
              ${c.license ? `<span class="source-meta-text">${escapeHtml(c.license)}</span>` : ''}
            </div>
          `;
          }).join('')}
        </div>
      </div>
    `;
  }

  function renderAudioPlayerBar(audioSrc) {
    return `
      <div class="audio-player-bar" data-audio-src="${audioSrc}">
        <button type="button" class="audio-play-circle-btn" title="Play Voice Audio" data-i18n-title="chat.playAudio">
          ▶
        </button>
        <div class="audio-waveform-canvas">
          <span class="wave-bar" style="height: 12px;"></span>
          <span class="wave-bar" style="height: 18px;"></span>
          <span class="wave-bar" style="height: 8px;"></span>
          <span class="wave-bar" style="height: 22px;"></span>
          <span class="wave-bar" style="height: 14px;"></span>
          <span class="wave-bar" style="height: 20px;"></span>
          <span class="wave-bar" style="height: 10px;"></span>
          <span class="wave-bar" style="height: 16px;"></span>
          <span class="wave-bar" style="height: 22px;"></span>
          <span class="wave-bar" style="height: 14px;"></span>
          <span class="wave-bar" style="height: 18px;"></span>
          <span class="wave-bar" style="height: 10px;"></span>
        </div>
        <span class="audio-time-label">0:00 / 0:12</span>
        <button type="button" class="audio-tool-btn audio-download-btn" title="Download WAV" data-i18n-title="chat.downloadAudio">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        </button>
      </div>
    `;
  }

  function attachAudioPlayerControls(cardRow, audioSrc, data, gesture, t_start, t_response) {
    const playerBar = cardRow.querySelector('.audio-player-bar');
    if (!playerBar) return;

    const playBtn = playerBar.querySelector('.audio-play-circle-btn');
    const downloadBtn = playerBar.querySelector('.audio-download-btn');

    if (playBtn) {
      playBtn.addEventListener('click', () => {
        if (activeAudio && !activeAudio.paused && activeAudioPlayerBar === playerBar) {
          activeAudio.pause();
          playBtn.textContent = '▶';
          playerBar.classList.remove('playing');
          if (mascot && mascot.stopAudioLipSync) mascot.stopAudioLipSync();
          setState('IDLE');
        } else {
          playProductionSpeech(data, audioSrc, data.answer, gesture, t_start, t_response, cardRow);
        }
      });
    }

    if (downloadBtn) {
      downloadBtn.addEventListener('click', () => {
        const a = document.createElement('a');
        a.href = audioSrc;
        a.download = `chacha_ganga_audio_${Date.now()}.wav`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      });
    }
  }

  // Context-Aware Intent, Sentiment & Tone Classifier (Phase 2 & Phase 5)
  function classifyResponseContext(answerText, questionText = '', serverData = {}) {
    const text = String(answerText || '').toLowerCase();
    const qText = String(questionText || '').toLowerCase();
    const mode = String(serverData.mode || 'grounded').toLowerCase();

    // 1. GREETING (English & Indic scripts)
    if (/^(namaste|hello|hi|welcome|greetings|pranam|good (morning|afternoon|evening)|नमस्ते|नमस्कार|प्रणाम|स्वागत|सत श्री अकाल|வணக்கம்|నమస్కారం|ನಮಸ್ಕಾರ|নমস্কার|سلام)/i.test(text) ||
        /^(hi|hello|namaste|hey|नमस्ते|प्रणाम|வணக்கம்|నమస్కారం)/i.test(qText)) {
      const isNamaste = /namaste|pranam|नमस्ते|प्रणाम|வணக்கம்|నమస్కారం|ನಮಸ್ಕಾರ/i.test(text) || /namaste|pranam|नमस्ते|प्रणाम/i.test(qText);
      return {
        state: 'GREETING',
        emotion: 'happy',
        gesture: isNamaste ? 'Praying' : 'Waving',
        contextType: 'greeting',
        bubbleText: null
      };
    }

    // 2. CRITICAL ALERT / POLLUTION WARNING / MANDATORY ADVISORY
    if (/warning|critical|alert|danger|prohibited|violation|severely polluted|hazardous|penalty|dhyan dein|savdhaan|chetavni|asurakshit|चेतावनी|सावधान|प्रतिबंधित/i.test(text)) {
      return {
        state: 'IMPORTANT_ALERT',
        emotion: 'surprised',
        gesture: 'Pointing_Forward',
        contextType: 'important_alert',
        bubbleText: null
      };
    }

    // 3. CELEBRATORY / EXCELLENT PROGRESS / DELIGHT
    if (/congratulations|excellent|fantastic|wonderful|delighted|pure|cleanest|achievement|pristine|badhai|shandaar|sarahniya|safal|बधाई|शानदार|सराहनीय|उत्कृष्ट/i.test(text)) {
      return {
        state: 'HAPPY',
        emotion: 'happy',
        gesture: 'Happy_Idle',
        contextType: 'celebratory',
        bubbleText: null
      };
    }

    // 4. APOLOGETIC / OUT OF SCOPE / INSUFFICIENT EVIDENCE
    if (mode === 'insufficient-evidence' || mode === 'general-unavailable' ||
        /sorry|apologize|not found|insufficient evidence|cannot find|out of scope|kshama|maaf|माफ़|क्षमा|उपलब्ध नहीं/i.test(text)) {
      return {
        state: 'APOLOGETIC',
        emotion: 'confused',
        gesture: 'Defeat_Idle',
        contextType: 'apologetic',
        bubbleText: null
      };
    }

    // 5. INQUISITIVE / ASKING QUESTION / CLARIFYING
    if (/\?$/.test(text.trim()) || /could you (please )?(clarify|tell|rephrase)|did you know|would you like to know|kya aap|kripya spasht|क्या आप/i.test(text)) {
      return {
        state: 'QUESTION',
        emotion: 'thinking',
        gesture: 'Looking',
        contextType: 'question',
        bubbleText: null
      };
    }

    // 6. TECHNICAL / WATER QUALITY / SCIENTIFIC DATA
    if (/bod|do|ph|cod|mg\/l|coliform|cpcb|monitoring station|dissolved oxygen|conductivity|turbidity|standards|biochemical|जल गुणवत्ता|मानक/i.test(text) ||
        (serverData.tables && serverData.tables.length > 0)) {
      return {
        state: 'TECHNICAL',
        emotion: 'neutral',
        gesture: 'Acknowledging',
        contextType: 'technical',
        bubbleText: null
      };
    }

    // 7. INFORMATIVE / EXPLAINING (Default for multi-point factual responses)
    if (text.length > 120 || /\n[-*•]|\d+\./.test(answerText) || mode === 'grounded') {
      return {
        state: 'EXPLAINING',
        emotion: 'neutral',
        gesture: 'Pointing_Forward',
        contextType: 'explaining',
        bubbleText: null
      };
    }

    // 8. GENERAL SPEAKING
    return {
      state: 'SPEAKING',
      emotion: 'neutral',
      gesture: 'Talking',
      contextType: 'general',
      bubbleText: null
    };
  }

  // 11. Production Audio & Real-Time Multi-Stage Lip-Sync Player
  function playProductionSpeech(data, audioSrc, fallbackText, gesture = 'explaining', t_start = null, t_response = null, cardRow = null) {
    stopCurrentSpeech();
    const attemptId = speechAttemptId;
    clearUiText(voiceStatusMsg);

    if (!audioSrc) {
      fallbackBrowserTTS(fallbackText, attemptId);
      return;
    }

    activeAudio = new Audio(audioSrc);
    lastAudioUrl = audioSrc;

    if (cardRow) {
      activeAudioPlayerBar = cardRow.querySelector('.audio-player-bar');
    }

    // Context-Aware State, Emotion & Gesture Classification
    const context = classifyResponseContext(data.answer || fallbackText || '', data.question || '', data);
    const detectedState = context.state;
    const detectedGesture = context.gesture || gesture || 'talking';
    const detectedEmotion = context.emotion || data.emotion || 'neutral';

    avatarEventBus.emit('emotion_detected', { emotion: detectedEmotion, contextType: context.contextType });
    setState(detectedState, {
      emotion: detectedEmotion,
      gesture: detectedGesture,
      bubbleText: context.bubbleText
    });

    if (activeAudioPlayerBar) {
      activeAudioPlayerBar.classList.add('playing');
      const btn = activeAudioPlayerBar.querySelector('.audio-play-circle-btn');
      if (btn) btn.textContent = '⏸';
    }

    activeAudio.onplay = () => {
      clearUiText(voiceStatusMsg);
      avatarEventBus.emit('speech_started', { audio: activeAudio, data });
      // Connect audio element to 3D Mascot Multi-Stage Lip-Sync System
      if (mascot && mascot.startAudioLipSync) {
        mascot.startAudioLipSync(activeAudio, data);
      }
    };

    activeAudio.onpause = () => {
      avatarEventBus.emit('speech_paused');
      if (mascot && mascot.stopAudioLipSync) {
        mascot.stopAudioLipSync();
      }
    };

    activeAudio.ontimeupdate = () => {
      if (activeAudioPlayerBar && activeAudio.duration) {
        const cur = formatAudioTime(activeAudio.currentTime);
        const dur = formatAudioTime(activeAudio.duration);
        const label = activeAudioPlayerBar.querySelector('.audio-time-label');
        if (label) label.textContent = `${cur} / ${dur}`;
      }
    };

    activeAudio.onended = () => {
      avatarEventBus.emit('speech_completed');
      stopCurrentSpeech();
      setState('IDLE');
    };

    activeAudio.onerror = (err) => {
      console.warn('[Frontend Audio] Error playing audio WAV, falling back to Web Speech:', err);
      stopCurrentSpeech();
      fallbackBrowserTTS(fallbackText);
    };

    activeAudio.play().then(() => {
      clearUiText(voiceStatusMsg);
      console.log('[Frontend Audio] Neural EdgeTTS audio playing with 3D Lip-Sync.');
    }).catch((err) => {
      console.warn('[Frontend Audio] Autoplay interrupted or blocked:', err);
      setUiText(voiceStatusMsg, 'voice.audioFailed');
    });
  }

  function stopCurrentSpeech() {
    speechAttemptId += 1;
    avatarEventBus.emit('interruption');
    if (lipSyncAnimationId) {
      cancelAnimationFrame(lipSyncAnimationId);
      lipSyncAnimationId = null;
    }
    if (mascot && mascot.stopAudioLipSync) {
      mascot.stopAudioLipSync();
    }
    if (activeAudio) {
      activeAudio.pause();
      activeAudio.currentTime = 0;
      activeAudio = null;
    }
    if (activeAudioPlayerBar) {
      activeAudioPlayerBar.classList.remove('playing');
      const btn = activeAudioPlayerBar.querySelector('.audio-play-circle-btn');
      if (btn) btn.textContent = '▶';
      activeAudioPlayerBar = null;
    }
    if (mascot) {
      mascot.clearViseme();
    }
    if (vizFill) {
      vizFill.style.width = '0%';
    }
  }

  function formatAudioTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  }

  // 12. Fallback Browser TTS
  async function fallbackBrowserTTS(text, attemptId = speechAttemptId) {
    if (!window.speechSynthesis) {
      setUiText(voiceStatusMsg, 'voice.browserUnavailable');
      setState('IDLE');
      return;
    }
    window.speechSynthesis.cancel();
    setState('SPEAKING', { gesture: 'talking' });

    const utter = new SpeechSynthesisUtterance(text);
    const locales = {
      en: 'en-IN', hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN',
      te: 'te-IN', kn: 'kn-IN', ml: 'ml-IN', gu: 'gu-IN',
      mr: 'mr-IN', pa: 'pa-IN', ur: 'ur-IN', or: 'or-IN', as: 'as-IN'
    };
    utter.lang = locales[currentOutputLanguage] || 'en-IN';
    const selectedVoice = window.GangaBrowserSpeech
      ? await window.GangaBrowserSpeech.resolveVoice(window.speechSynthesis, utter.lang)
      : window.speechSynthesis.getVoices().find(
        (voice) => voice.lang.toLowerCase() === utter.lang.toLowerCase()
      );
    if (attemptId !== speechAttemptId) return;
    if (!selectedVoice) {
      setUiText(voiceStatusMsg, 'voice.noVoice', { locale: utter.lang });
      setState('IDLE');
      return;
    }
    clearUiText(voiceStatusMsg);
    utter.voice = selectedVoice;
    utter.rate = 1.0;

    let simInterval = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        const ap = Math.sin(Date.now() / 90) * 0.4 + 0.5;
        mascot.setMouthAperture(ap);
        if (vizFill) vizFill.style.width = `${Math.round(ap * 100)}%`;
      }
    }, 60);

    utter.onend = () => {
      if (attemptId !== speechAttemptId) return;
      clearInterval(simInterval);
      stopCurrentSpeech();
      setState('IDLE');
    };
    utter.onerror = (event) => {
      clearInterval(simInterval);
      if (['canceled', 'interrupted'].includes(event && event.error)) return;
      if (attemptId !== speechAttemptId) return;
      stopCurrentSpeech();
      if (voiceStatusMsg) {
        setUiText(voiceStatusMsg, 'voice.playbackFailed');
      }
      setState('IDLE');
    };

    window.speechSynthesis.speak(utter);
  }

  // 13. Microphone Recording (MediaRecorder -> Backend Vosk STT)
  if (micBtn) {
    micBtn.addEventListener('click', async () => {
      if (isRecording) {
        stopMicrophoneRecording();
      } else {
        await startMicrophoneRecording();
      }
    });
  }

  async function startMicrophoneRecording() {
    if (currentState === 'SPEAKING' || currentState === 'THINKING') {
      stopCurrentSpeech();
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      startWebSpeechFallback();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunks = [];
      mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunks.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        avatarEventBus.emit('listening_completed');
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        setUiText(voiceStatusMsg, 'voice.transcribing');
        setState('THINKING');
        await uploadAudioForSTT(audioBlob);
      };

      mediaRecorder.start();
      isRecording = true;
      micBtn.classList.add('recording');
      avatarEventBus.emit('listening_started');
      setState('LISTENING');
      setUiText(voiceStatusMsg, 'voice.listeningSend');

    } catch (err) {
      console.warn('[Frontend Mic] MediaRecorder not accessible, falling back to Web Speech API:', err);
      startWebSpeechFallback();
    }
  }

  function stopMicrophoneRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      if (micBtn) micBtn.classList.remove('recording');
    }
  }

  async function uploadAudioForSTT(blob) {
    try {
      const formData = new FormData();
      formData.append('file', blob, 'user_speech.webm');

      const response = await fetch(`/api/integration/stt?input_language=${encodeURIComponent(currentVoiceInputLanguage)}&output_language=${encodeURIComponent(currentOutputLanguage)}`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        let detail = `STT server returned status ${response.status}`;
        try { detail = (await response.json()).detail || detail; } catch (_) {}
        throw new Error(detail);
      }

      const data = await response.json();
      if (voiceStatusMsg) {
        if (data.question) setUiText(voiceStatusMsg, 'voice.heard', { text: data.question });
        else setUiText(voiceStatusMsg, 'voice.transcribed');
      }
      if (data.question && data.answer) {
        renderCompletedResponse(data.question, data);
      } else if (data.question) {
        await processQuestion(data.question, currentVoiceInputLanguage);
      }

    } catch (err) {
      console.warn('[Frontend STT] Backend STT failed, trying Web Speech API:', err);
      setState('IDLE');
      if (window.SpeechRecognition || window.webkitSpeechRecognition) {
        setUiText(voiceStatusMsg, 'voice.backendFallback');
        startWebSpeechFallback();
      } else if (voiceStatusMsg) {
        setUiText(voiceStatusMsg, 'voice.recognitionFailedWithError', { error: err.message || t('voice.noRecognition') });
      }
    }
  }

  function renderCompletedResponse(question, data) {
    appendUserMessage(question);
    const loadingCardId = 'loadingCard_' + Date.now();
    appendLoadingAssistantCard(loadingCardId);
    setState('THINKING');
    const receivedAt = performance.now();
    detectedTextLanguage = data.input_language || currentVoiceInputLanguage;
    updateLangBadge();
    replaceLoadingWithResponse(loadingCardId, data, receivedAt, receivedAt);
  }

  function startWebSpeechFallback() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      setUiText(voiceStatusMsg, 'voice.micUnsupported');
      return;
    }

    const recognition = new SpeechRec();
    const locales = {
      en: 'en-IN', hi: 'hi-IN', kn: 'kn-IN', ta: 'ta-IN', te: 'te-IN',
      bn: 'bn-IN', mr: 'mr-IN', gu: 'gu-IN', ml: 'ml-IN', pa: 'pa-IN',
      ur: 'ur-IN', or: 'or-IN', as: 'as-IN'
    };
    recognition.lang = locales[currentVoiceInputLanguage] || 'en-IN';
    recognition.interimResults = false;

    recognition.onstart = () => {
      isRecording = true;
      if (micBtn) micBtn.classList.add('recording');
      setState('LISTENING');
      setUiText(voiceStatusMsg, 'voice.browserListening');
    };

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setUiText(voiceStatusMsg, 'voice.heard', { text: transcript });
      processQuestion(transcript, currentVoiceInputLanguage);
    };

    recognition.onerror = (e) => {
      console.warn('[Web Speech API] Error:', e.error);
      setUiText(voiceStatusMsg, 'voice.recognitionError', { error: e.error });
      stopMicrophoneRecording();
      setState('IDLE');
    };

    recognition.onend = () => {
      stopMicrophoneRecording();
    };

    recognition.start();
  }

  // 15. Quiz Integration (Preserved)
  if (window.GangaQuiz) {
    window.GangaQuiz.createQuizController({
      document,
      questions: window.GangaQuizQuestions,
      getMascot: () => mascot
    });
  }

  const fetchPage = window.fetch.bind(window);
  const resourcesPage = window.GangaResources?.create({ document, fetch: fetchPage });
  const awarenessPage = window.GangaAwareness?.create({
    document,
    fetch: fetchPage,
    openResource: (fileName, section, pageStart) => {
      window.location.hash = `#resources`;
      requestAnimationFrame(() => resourcesPage?.openSection(fileName, section, pageStart));
    }
  });
  window.GangaNavigation?.create({
    document,
    window,
    onViewChange: (view) => {
      if (view === 'resources') resourcesPage?.show();
      if (view === 'awareness') awarenessPage?.show();
    },
    onQuizChange: (show) => {
      if (quizView) quizView.hidden = !show;
      if (chatView) chatView.hidden = show;
      if (quizNavButton) quizNavButton.setAttribute('aria-pressed', String(show));
    }
  });

  // Utility helpers
  function scrollToBottom() {
    if (chatMessagesList) {
      setTimeout(() => {
        chatMessagesList.scrollTop = chatMessagesList.scrollHeight;
      }, 50);
    }
  }

  function escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Initialize
  updateLangBadge();
  updateChachaGreeting();
  setState('IDLE');
  window.addEventListener('ganga-website-language-change', () => {
    updateLangBadge();
    updateLiveStatusLabel(currentState);
    uiI18n?.applySubtree(chatMessagesList);
    uiI18n?.applySubtree(voiceStatusMsg);
  });
});
