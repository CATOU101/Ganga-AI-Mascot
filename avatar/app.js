/**
 * Main Application Orchestrator for Ganga AI Mascot UI
 * Redesigned Premium White-Themed Dashboard & Multilingual Interaction
 * 
 * Pipeline:
 * - Independent Input Language (Auto Detect, Hindi, English, Bengali, Tamil, Telugu, Kannada, Malayalam, Gujarati, Punjabi, Odia, Marathi)
 * - Independent Output Language (Controls Brain translation & EdgeTTS neural voice)
 * - Multilingual Virtual On-Screen Keyboard with native script layouts
 * - Chacha Chaudhary 3D Avatar (28 Skeletal Animations, Pedestal, Automatic States & Lip-Sync)
 * - Modern AI Chat Stream with User bubbles, Assistant cards, Waveform Audio Player, and Verified Sources
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Initialize 3D Avatar Mascot Controller
  const mascot = new MascotController();

  // 2. DOM Elements
  const chatMessagesList = document.getElementById('chatMessagesList');
  const askForm = document.getElementById('askForm');
  const questionInput = document.getElementById('questionInput');
  const micBtn = document.getElementById('micBtn');
  const submitBtn = document.getElementById('submitBtn');
  const keyboardToggleBtn = document.getElementById('keyboardToggleBtn');
  const virtualKeyboardContainer = document.getElementById('virtualKeyboardContainer');

  const inputLangSelect = document.getElementById('inputLangSelect');
  const outputLangSelect = document.getElementById('outputLangSelect');
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

  // Quiz & Modals
  const quizView = document.getElementById('quiz');
  const quizNavButton = document.getElementById('quizNavButton');
  const infoModalOverlay = document.getElementById('infoModalOverlay');
  const modalTitle = document.getElementById('modalTitle');
  const modalContent = document.getElementById('modalContent');
  const modalCloseBtn = document.getElementById('modalCloseBtn');

  // 3. Application State (Default: English)
  let currentInputLanguage = 'en';
  let currentOutputLanguage = 'en';
  let currentState = 'IDLE';

  // Audio Playback & Synchronization State
  let activeAudio = null;
  let activeAudioPlayerBar = null;
  let lipSyncAnimationId = null;
  let lastAudioUrl = null;

  // Microphone Recording State (MediaRecorder)
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;

  // 4. Initialize Multilingual Virtual On-Screen Keyboard
  let virtualKeyboard = null;
  if (window.MultilingualKeyboard && virtualKeyboardContainer) {
    virtualKeyboard = new window.MultilingualKeyboard(questionInput, {
      container: virtualKeyboardContainer,
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

  // 5. Input Placeholders map
  const placeholders = {
    auto: 'Type your question here or speak (अपना प्रश्न यहाँ लिखें या बोलें)...',
    hi: 'गंगा नदी या नमामि गंगे से जुड़ा प्रश्न पूछें...',
    en: 'Type your question about Ganga, GRBMP, or water quality...',
    bn: 'গঙ্গা নদী বা দূষণ নিয়ন্ত্রণ সম্পর্কে আপনার প্রশ্ন লিখুন...',
    ta: 'கங்கை நதி அல்லது நமாமி கங்கை குறித்த உங்கள் கேள்வியைத் தட்டச்சு செய்க...',
    te: 'గంగా నది లేదా నమామి గంగే గురించి మీ ప్రశ్నను అడగండి...',
    kn: 'ಗಂಗಾ ನದಿ ಅಥವಾ ನಮಾಮಿ ಗಂಗೆ ಕುರಿತು ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ...',
    ml: 'ഗംഗാ നദിയെക്കുറിച്ചുള്ള ചോദ്യം ടൈപ്പ് ചെയ്യുക...',
    gu: 'ગંગા નદી અથવા જળ સંરક્ષણ વિશે તમારો પ્રશ્ન પૂછો...',
    pa: 'ਗੰਗਾ ਨਦੀ ਬਾਰੇ ਆਪਣਾ ਸਵਾਲ ਪੁੱਛੋ...',
    or: 'ଗଙ୍ଗା ନଦୀ ସମ୍ପର୍କରେ ଆପଣଙ୍କ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ...',
    mr: 'गंगा नदी किंवा नमामी गंगे संदर्भात प्रश्न विचारा...'
  };

  // 6. Independent Language Selectors
  if (inputLangSelect) {
    inputLangSelect.addEventListener('change', () => {
      currentInputLanguage = inputLangSelect.value;
      if (questionInput) {
        questionInput.placeholder = placeholders[currentInputLanguage] || placeholders.en;
      }
      // If user chose a specific script, also synchronize virtual keyboard
      if (virtualKeyboard && currentInputLanguage !== 'auto' && virtualKeyboard.layouts[currentInputLanguage]) {
        virtualKeyboard.setLanguage(currentInputLanguage);
      }
      updateLangBadge();
    });
  }

  if (outputLangSelect) {
    outputLangSelect.addEventListener('change', () => {
      currentOutputLanguage = outputLangSelect.value;
      updateLangBadge();
      updateChachaGreeting();
    });
  }

  function updateLangBadge() {
    if (responseLangBadge) {
      const inLabel = currentInputLanguage.toUpperCase();
      const outLabel = currentOutputLanguage.toUpperCase();
      responseLangBadge.textContent = `In: ${inLabel} | Out: ${outLabel}`;
    }
  }

  function updateChachaGreeting() {
    if (currentState === 'IDLE' && mascotSpeechBubble) {
      const greetings = {
        hi: "नमस्ते! मैं चाचा चौधरी हूँ। गंगा नदी व संरक्षण के बारे में सही जानकारी के लिए मुझसे पूछें!",
        en: "Namaste! I am Chacha Chaudhary. Ask me anything about River Ganga, conservation, and water quality!",
        bn: "নমস্কার! আমি চাচা চৌধুরী। গঙ্গা নদী এবং সংরক্ষণ সম্পর্কিত তথ্যের জন্য আমাকে জিজ্ঞাসা করুন!",
        ta: "வணக்கம்! நான் சாச்சா சவுத்ரி. கங்கை நதி மற்றும் பாதுகாப்பு பற்றிய விவரங்களுக்கு என்னைக் கேளுங்கள்!",
        te: "నమస్కారం! నేను చాచా చౌదరి. గంగా నది పరిరక్షణ గురించి సమాచారం కోసం నన్ను అడగండి!",
        kn: "ನಮಸ್ಕಾರ! ನಾನು ಚಾಚಾ ಚೌಧರಿ. ಗಂಗಾ ನದಿ ಸಂರಕ್ಷಣೆ ಕುರಿತು ಮಾಹಿತಿಗಾಗಿ ನನ್ನನ್ನು ಕೇಳಿ!",
        ml: "നമസ്കാരം! ഞാൻ ചാച്ചാ ചൗധരി. ഗംഗാ നദീ സംരക്ഷണത്തെക്കുറിച്ചുള്ള ചോദ്യങ്ങൾക്ക് എന്നോട് ചോദിക്കൂ!",
        gu: "નમસ્તે! હું ચાચા ચૌધરી છું. ગંગા નદીના સંરક્ષણ માટે મને કોઈ પણ પ્રશ્ન પૂછો!",
        pa: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਚਾਚਾ ਚੌਧਰੀ ਹਾਂ। ਗੰਗਾ ਨਦੀ ਬਾਰੇ ਜਾਣਕਾਰੀ ਲਈ ਮੈਨੂੰ ਪੁੱਛੋ!",
        or: "ନମସ୍କାର! ମୁଁ ଚାଚା ଚୌଧୁରୀ। ଗଙ୍ଗା ନଦୀ ସଂରକ୍ଷଣ ସମ୍ପର୍କରେ ମୋତେ ପ୍ରଶ୍ନ ପଚାରନ୍ତୁ!",
        mr: "नमस्ते! मी चाचा चौधरी. गंगा नदी संरक्षणाविषयी माहितीसाठी मला प्रश्न विचारा!"
      };
      mascotSpeechBubble.textContent = greetings[currentOutputLanguage] || greetings.en;
    }
  }

  // 7. Synchronize Avatar State Machine & Status Indicator Pills
  function setState(state, options = {}) {
    currentState = state;

    if (statePillIdle) statePillIdle.classList.toggle('active', state === 'IDLE');
    if (statePillListening) statePillListening.classList.toggle('active', state === 'LISTENING');
    if (statePillThinking) statePillThinking.classList.toggle('active', state === 'THINKING' || state === 'PROCESSING');
    if (statePillSpeaking) statePillSpeaking.classList.toggle('active', state === 'SPEAKING');

    // Update Live State Indicator Badge in Avatar Header
    const liveStatusText = document.getElementById('liveStatusText');
    const liveStatusDot = document.getElementById('liveStatusDot');
    if (liveStatusText) {
      const labels = {
        'IDLE': 'Idle',
        'LISTENING': 'Listening...',
        'THINKING': 'Thinking...',
        'PROCESSING': 'Analyzing...',
        'SPEAKING': 'Speaking...',
        'ERROR': 'Error'
      };
      liveStatusText.textContent = labels[state] || state;
    }
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
      const prompt = pill.dataset.prompt;
      if (prompt) {
        processQuestion(prompt);
      }
    }
  });

  // 9. Main Question Pipeline (Question -> User Bubble -> RAG Brain -> Assistant Card)
  async function processQuestion(question) {
    if (currentState === 'SPEAKING' || currentState === 'THINKING') {
      stopCurrentSpeech();
    }

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
          input_language: currentInputLanguage === 'auto' ? null : currentInputLanguage,
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

      // Replace Loading card with full formatted Assistant Message Card
      replaceLoadingWithResponse(loadingCardId, data, t_start, t_response);

    } catch (err) {
      console.error('[Frontend] Error querying Brain API:', err);
      setState('ERROR');
      replaceLoadingWithError(loadingCardId, err.message || "Could not retrieve response from Ganga Brain.");
      setTimeout(() => setState('IDLE'), 2500);
    }
  }

  // 10. Message Stream Helpers
  function getFormattedTime() {
    const now = new Date();
    return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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
        <img src="08_Final/validation_renders/Face_Thinking.png" alt="Chacha Thinking" class="chacha-thumb-img" onerror="this.onerror=null;this.src='08_Final/validation_renders/Face_Happy.png';" />
      </div>
      <div class="message-bubble assistant-card">
        <div class="bubble-header-bar">
          <div class="assistant-meta-left">
            <span class="assistant-name">Chacha Chaudhary</span>
            <span class="verified-tag">Analyzing Corpus</span>
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
            <span class="thinking-msg-text">Consulting verified GRBMP knowledge base...</span>
          </div>
        </div>
      </div>
    `;
    chatMessagesList.appendChild(row);
  }

  function replaceLoadingWithResponse(cardId, data, t_start = null, t_response = null) {
    const cardRow = document.getElementById(cardId);
    if (!cardRow) return;

    const answer = data.answer || data.text || "No response received.";
    const mode = data.mode || "grounded";
    const emotion = (data.emotion || "happy").toLowerCase();
    const gesture = (data.gesture || "explaining").toLowerCase();
    const citations = data.citations || [];
    const tables = data.tables || [];

    // Format text with clean bullet list if multiple sentences or points
    const formattedHtml = formatAnswerHtml(answer, tables);

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
            <span class="verified-tag">${mode === 'grounded' ? 'Verified RAG' : 'Ganga Guide'}</span>
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
      playProductionSpeech(data, audioSrc, answer, gesture, t_start, t_response, cardRow);
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
      <div class="message-bubble assistant-card" style="border-color: #FCA5A5;">
        <div class="bubble-header-bar">
          <span class="assistant-name" style="color: #DC2626;">Chacha Chaudhary</span>
          <span class="verified-tag" style="background-color: #FEF2F2; color: #DC2626;">Notice</span>
        </div>
        <div class="bubble-content-text" style="color: #991B1B;">
          ${escapeHtml(errorMessage)}
        </div>
      </div>
    `;
    scrollToBottom();
  }

  function formatAnswerHtml(answer, tables = []) {
    let clean = escapeHtml(answer);
    
    // Convert numbered lists or bullet sentences to stylized clean list items
    const lines = clean.split('\n').filter(l => l.trim().length > 0);
    if (lines.length > 2) {
      let html = `<p>${lines[0]}</p><ul>`;
      for (let i = 1; i < lines.length; i++) {
        let line = lines[i].replace(/^[-•*]|\d+\.\s*/, '').trim();
        html += `<li>${line}</li>`;
      }
      html += `</ul>`;
      return html;
    } else {
      return `<p>${clean}</p>`;
    }
  }

  function renderCitationsAccordion(citations) {
    if (!citations || citations.length === 0) {
      return '';
    }

    return `
      <div class="sources-accordion">
        <button type="button" class="sources-toggle-btn" aria-expanded="false">
          <span>📚 Verified Sources (${citations.length})</span>
          <span class="sources-chevron" aria-hidden="true">▾</span>
        </button>
        <div class="sources-list">
          ${citations.map(c => `
            <div class="source-item-card">
              <span class="source-pdf-badge">PDF</span>
              <span class="source-title-text">${escapeHtml(c.source || c.file_name || 'GRBMP Document')}</span>
              <span class="source-meta-text">${c.page ? `p. ${c.page}` : ''}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  function renderAudioPlayerBar(audioSrc) {
    return `
      <div class="audio-player-bar" data-audio-src="${audioSrc}">
        <button type="button" class="audio-play-circle-btn" title="Play Voice Audio">
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
        <button type="button" class="audio-tool-btn audio-download-btn" title="Download WAV">
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

  // 11. Production Audio & Real-Time Dual-Stage Lip-Sync Player
  function playProductionSpeech(data, audioSrc, fallbackText, gesture = 'explaining', t_start = null, t_response = null, cardRow = null) {
    stopCurrentSpeech();

    if (!audioSrc) {
      fallbackBrowserTTS(fallbackText);
      return;
    }

    activeAudio = new Audio(audioSrc);
    lastAudioUrl = audioSrc;

    if (cardRow) {
      activeAudioPlayerBar = cardRow.querySelector('.audio-player-bar');
    }

    // Context-Aware State, Emotion & Gesture Classification
    const answer = (data.answer || fallbackText || '').toLowerCase();
    let detectedState = 'SPEAKING';
    let detectedGesture = gesture || 'talking';
    let detectedEmotion = data.emotion || 'neutral';

    if (/namaste|hello|hi|welcome|नमस्ते|प्रणाम|स्वागत/i.test(answer)) {
      detectedState = 'GREETING';
      detectedGesture = 'waving';
      detectedEmotion = 'happy';
    } else if (/important|note|warning|guideline|must|alert|ध्यातव्य|महत्वपूर्ण|नियम/i.test(answer)) {
      detectedState = 'EXPLAINING';
      detectedGesture = 'pointing_forward';
      detectedEmotion = 'neutral';
    } else if (/thank|great|wonderful|delighted|happy|congratulations|धन्यवाद|सराहनीय|उत्कृष्ट/i.test(answer)) {
      detectedState = 'HAPPY';
      detectedGesture = 'happy_idle';
      detectedEmotion = 'happy';
    } else if (/sorry|not found|clarify|माफ़|स्पष्ट/i.test(answer)) {
      detectedState = 'CONFUSED';
      detectedGesture = 'nervously_look_around';
      detectedEmotion = 'confused';
    }

    setState(detectedState, { emotion: detectedEmotion, gesture: detectedGesture });

    if (activeAudioPlayerBar) {
      activeAudioPlayerBar.classList.add('playing');
      const btn = activeAudioPlayerBar.querySelector('.audio-play-circle-btn');
      if (btn) btn.textContent = '⏸';
    }

    activeAudio.onplay = () => {
      // Connect audio element to 3D Mascot Dual-Stage Lip-Sync System
      if (mascot && mascot.startAudioLipSync) {
        mascot.startAudioLipSync(activeAudio, data);
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
      stopCurrentSpeech();
      setState('IDLE');
    };

    activeAudio.onerror = (err) => {
      console.warn('[Frontend Audio] Error playing audio WAV, falling back to Web Speech:', err);
      stopCurrentSpeech();
      fallbackBrowserTTS(fallbackText);
    };

    activeAudio.play().then(() => {
      console.log('[Frontend Audio] Neural EdgeTTS audio playing with 3D Lip-Sync.');
    }).catch((err) => {
      console.warn('[Frontend Audio] Autoplay interrupted or blocked:', err);
    });
  }

  function stopCurrentSpeech() {
    if (lipSyncAnimationId) {
      cancelAnimationFrame(lipSyncAnimationId);
      lipSyncAnimationId = null;
    }
    if (mascot && mascot.stopAudioLipSync) {
      mascot.stopAudioLipSync();
    }
    if (activeAudio) {
      activeAudio.pause();
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
  function fallbackBrowserTTS(text) {
    if (!window.speechSynthesis) {
      setState('IDLE');
      return;
    }
    window.speechSynthesis.cancel();
    setState('SPEAKING', { gesture: 'talking' });

    const utter = new SpeechSynthesisUtterance(text);
    const locales = {
      en: 'en-IN', hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN',
      te: 'te-IN', kn: 'kn-IN', ml: 'ml-IN', gu: 'gu-IN',
      mr: 'mr-IN', pa: 'pa-IN', ur: 'ur-IN'
    };
    utter.lang = locales[currentOutputLanguage] || 'en-IN';
    utter.rate = 1.0;

    let simInterval = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        const ap = Math.sin(Date.now() / 90) * 0.4 + 0.5;
        mascot.setMouthAperture(ap);
        if (vizFill) vizFill.style.width = `${Math.round(ap * 100)}%`;
      }
    }, 60);

    utter.onend = () => {
      clearInterval(simInterval);
      stopCurrentSpeech();
      setState('IDLE');
    };
    utter.onerror = () => {
      clearInterval(simInterval);
      stopCurrentSpeech();
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
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        if (voiceStatusMsg) voiceStatusMsg.textContent = 'Transcribing with local STT...';
        setState('THINKING');
        await uploadAudioForSTT(audioBlob);
      };

      mediaRecorder.start();
      isRecording = true;
      micBtn.classList.add('recording');
      setState('LISTENING');
      if (voiceStatusMsg) voiceStatusMsg.textContent = 'Listening... Speak clearly, click mic again to send.';

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

      const response = await fetch(`/api/integration/stt?input_language=${currentInputLanguage === 'auto' ? 'en' : currentInputLanguage}&output_language=${currentOutputLanguage}`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`STT server returned status ${response.status}`);
      }

      const data = await response.json();
      if (voiceStatusMsg) {
        voiceStatusMsg.textContent = data.question ? `Heard: "${data.question}"` : 'Speech transcribed.';
      }
      if (data.question) {
        await processQuestion(data.question);
      }

    } catch (err) {
      console.warn('[Frontend STT] Backend STT failed, trying Web Speech API:', err);
      if (voiceStatusMsg) voiceStatusMsg.textContent = 'STT unavailable, please type question.';
      setState('IDLE');
    }
  }

  function startWebSpeechFallback() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      if (voiceStatusMsg) voiceStatusMsg.textContent = 'Microphone speech recognition not supported in this browser.';
      return;
    }

    const recognition = new SpeechRec();
    const locales = {
      en: 'en-IN', hi: 'hi-IN', bn: 'bn-IN', ta: 'ta-IN',
      te: 'te-IN', kn: 'kn-IN', ml: 'ml-IN', gu: 'gu-IN',
      mr: 'mr-IN', pa: 'pa-IN', ur: 'ur-IN'
    };
    recognition.lang = locales[currentInputLanguage] || 'en-IN';
    recognition.interimResults = false;

    recognition.onstart = () => {
      isRecording = true;
      if (micBtn) micBtn.classList.add('recording');
      setState('LISTENING');
      if (voiceStatusMsg) voiceStatusMsg.textContent = 'Listening via browser speech recognition...';
    };

    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      if (voiceStatusMsg) voiceStatusMsg.textContent = `Heard: "${transcript}"`;
      processQuestion(transcript);
    };

    recognition.onerror = (e) => {
      console.warn('[Web Speech API] Error:', e.error);
      if (voiceStatusMsg) voiceStatusMsg.textContent = `Speech recognition error: ${e.error}`;
      stopMicrophoneRecording();
      setState('IDLE');
    };

    recognition.onend = () => {
      stopMicrophoneRecording();
    };

    recognition.start();
  }

  // 14. Sidebar Navigation Modals
  const sidebarData = {
    resources: {
      title: "Ganga Resources & Knowledge Base",
      content: `
        <p>The Ganga AI Mascot is built on the complete <strong>Ganga River Basin Management Plan (GRBMP)</strong> prepared by the Consortium of 7 Indian Institutes of Technology (IITs).</p>
        <br/>
        <ul>
          <li><strong>Corpus Size:</strong> 86 Verified GRBMP Reports, 4,609 pages, 4,085 indexed semantic chunks.</li>
          <li><strong>Key Documents:</strong> Mission 1 (Aviral Dhara), Mission 2 (Nirmal Dhara), Mission 3 (Geological Safeguards), Mission 4 (Ecological Restoration), Mission 5 (Gyan Ganga).</li>
          <li><strong>Storage:</strong> Deterministic SQLite metadata index + 384-dimensional ONNX vector store.</li>
        </ul>
      `
    },
    initiatives: {
      title: "Namami Gange Key Initiatives",
      content: `
        <p><strong>Namami Gange</strong> is an Integrated Conservation Mission approved as a 'Flagship Programme' by the Union Government with four primary pillars:</p>
        <br/>
        <ul>
          <li><strong>Nirmal Dhara (Unpolluted Flow):</strong> Zero untreated domestic sewage and industrial effluents entering the river through decentralized STPs and sewage networks.</li>
          <li><strong>Aviral Dhara (Continuous Flow):</strong> Environmental-flow management, basin water budgeting, and barrage water regulation.</li>
          <li><strong>Jan Ganga (People-River Connect):</strong> Community participation, ghat cleanliness, riverfront development, and educational mascots like Chacha Chaudhary.</li>
          <li><strong>Gyan Ganga (Knowledge & Ecology):</strong> Biodiversity monitoring, river dolphin conservation, and AI-enabled GIS mapping.</li>
        </ul>
      `
    },
    awareness: {
      title: "Water Quality & Conservation Awareness",
      content: `
        <p>Real-Time Water Quality Monitoring System (RTWQMS) stations track Ganga water safety parameters against <strong>CPCB Designated Best Use Criteria (Class B - Outdoor Bathing)</strong>:</p>
        <br/>
        <ul>
          <li><strong>Dissolved Oxygen (DO):</strong> ≥ 5.0 mg/L (Critical for aquatic life).</li>
          <li><strong>Biochemical Oxygen Demand (BOD):</strong> ≤ 3.0 mg/L (Indicates organic purity).</li>
          <li><strong>pH:</strong> 6.5 to 8.5 (Healthy aquatic balance).</li>
          <li><strong>Faecal Coliforms:</strong> ≤ 2500 MPN/100 mL desirable limit.</li>
        </ul>
      `
    },
    about: {
      title: "About PRJ_316 Ganga AI Mascot",
      content: `
        <p><strong>Project ID:</strong> PRJ_316<br/>
        <strong>Official Title:</strong> Development of AI, ML and Chatbot-powered Interactive Robot Mascot (Chacha Chaudhary) and Digital Avatar to Strengthen the River People Connect Component of Namami Gange.</p>
        <br/>
        <p>Brings together a real-time 3D Three.js Chacha Chaudhary avatar (28 skeletal actions, viseme morphs), retrieval-augmented Brain service, Neural EdgeTTS speech, and multi-language support across Indian languages.</p>
      `
    },
    settings: {
      title: "Settings & System Info",
      content: `
        <p><strong>Voice Synthesizer:</strong> Neural EdgeTTS (Indian Regional Voices) with Windows SAPI fallback.</p>
        <p><strong>Speech Lip-Sync:</strong> Phonetic Acoustic Rhubarb viseme alignment.</p>
        <p><strong>3D Model:</strong> Chacha_New (65 bones, Mixamo armature, PBR shaders).</p>
        <p><strong>Server Host:</strong> Localhost / Unified FastAPI backend (port 8080).</p>
      `
    }
  };

  document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const navKey = item.dataset.nav;
      document.querySelectorAll('.sidebar-nav .nav-item').forEach(b => b.classList.remove('active'));
      item.classList.add('active');

      if (navKey === 'home' || navKey === 'chat') {
        if (quizView) quizView.hidden = true;
        closeInfoModal();
      } else if (sidebarData[navKey]) {
        openInfoModal(sidebarData[navKey].title, sidebarData[navKey].content);
      }
    });
  });

  function openInfoModal(title, html) {
    if (modalTitle) modalTitle.textContent = title;
    if (modalContent) modalContent.innerHTML = html;
    if (infoModalOverlay) infoModalOverlay.style.display = 'flex';
  }

  function closeInfoModal() {
    if (infoModalOverlay) infoModalOverlay.style.display = 'none';
    const homeBtn = document.querySelector('.sidebar-nav .nav-item[data-nav="home"]');
    if (homeBtn) homeBtn.classList.add('active');
  }

  if (modalCloseBtn) modalCloseBtn.addEventListener('click', closeInfoModal);
  if (infoModalOverlay) {
    infoModalOverlay.addEventListener('click', (e) => {
      if (e.target === infoModalOverlay) closeInfoModal();
    });
  }

  // 15. Quiz Integration (Preserved)
  if (window.GangaQuiz) {
    window.GangaQuiz.createQuizController({
      document,
      questions: window.GangaQuizQuestions,
      getMascot: () => mascot
    });
  }

  function updateActiveView(moveFocus = false) {
    const showQuiz = window.location.hash === '#quiz';
    if (quizView) quizView.hidden = !showQuiz;
    if (quizNavButton) quizNavButton.setAttribute('aria-pressed', String(showQuiz));
    if (moveFocus && showQuiz) {
      document.getElementById('quizTitle')?.focus();
    }
  }

  window.addEventListener('hashchange', () => updateActiveView(true));
  updateActiveView();

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
});
