/**
 * Main Application Orchestrator for Ganga AI Mascot UI
 * Connects Brain API, Web Speech STT, SpeechSynthesis TTS, RMS Lip-Sync, and Avatar Controller.
 */

document.addEventListener('DOMContentLoaded', () => {
  const mascot = new MascotController();

  // UI Elements
  const statusBadge = document.getElementById('statusBadge');
  const statusText = document.getElementById('statusText');
  const emotionBadge = document.getElementById('emotionBadge');
  const gestureBadge = document.getElementById('gestureBadge');
  const modeBadge = document.getElementById('modeBadge');
  const responseLangBadge = document.getElementById('responseLangBadge');
  const questionPromptView = document.getElementById('questionPromptView');
  const userQuestionText = document.getElementById('userQuestionText');
  const answerText = document.getElementById('answerText');
  const thinkingWave = document.getElementById('thinkingWave');
  const citationsList = document.getElementById('citationsList');
  const citationCount = document.getElementById('citationCount');
  const askForm = document.getElementById('askForm');
  const questionInput = document.getElementById('questionInput');
  const micBtn = document.getElementById('micBtn');
  const submitBtn = document.getElementById('submitBtn');
  const langHiBtn = document.getElementById('langHi');
  const langEnBtn = document.getElementById('langEn');
  const vizFill = document.getElementById('vizFill');
  const voiceStatusMsg = document.getElementById('voiceStatusMsg');

  let currentLanguage = 'hi';
  let currentState = 'IDLE';
  let speechSynth = window.speechSynthesis;
  let speechUtterance = null;
  let audioCtx = null;
  let isListening = false;
  let recognition = null;

  // Language selection handlers
  langHiBtn.addEventListener('click', () => setLanguage('hi'));
  langEnBtn.addEventListener('click', () => setLanguage('en'));

  function setLanguage(lang) {
    currentLanguage = lang;
    if (lang === 'hi') {
      langHiBtn.classList.add('active');
      langEnBtn.classList.remove('active');
      responseLangBadge.textContent = 'Lang: HI';
      questionInput.placeholder = 'गंगा नदी या नमामि गंगे से जुड़ा प्रश्न पूछें...';
    } else {
      langEnBtn.classList.add('active');
      langHiBtn.classList.remove('active');
      responseLangBadge.textContent = 'Lang: EN';
      questionInput.placeholder = 'Type your question about Ganga, GRBMP, or pollution...';
    }
  }

  // Update UI State Badges
  function setState(state) {
    currentState = state;
    statusBadge.className = `status-badge state-${state.toLowerCase()}`;
    statusText.textContent = state;

    if (state === 'THINKING' || state === 'PROCESSING') {
      thinkingWave.style.display = 'flex';
      submitBtn.disabled = true;
    } else {
      thinkingWave.style.display = 'none';
      submitBtn.disabled = false;
    }

    if (state === 'IDLE') {
      mascot.setGesture('idle');
      mascot.setEmotion('neutral');
    }
  }

  // Form Submission
  askForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    await processQuestion(question);
  });

  // Main Question Pipeline
  async function processQuestion(question) {
    if (currentState !== 'IDLE') return;

    // 1. Update UI to PROCESSING -> THINKING
    questionPromptView.style.display = 'block';
    userQuestionText.textContent = question;
    answerText.textContent = '';
    setState('PROCESSING');
    mascot.setGesture('thinking');
    mascot.setEmotion('thinking');
    setState('THINKING');

    try {
      // 2. Call Integration API endpoint (/api/integration/ask or fallback /ask)
      const response = await fetch('/api/integration/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question, language: currentLanguage })
      }).catch(async () => {
        // Fallback to direct Brain FastAPI /ask endpoint if integration endpoint isn't mounted
        return fetch('/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: question, language: currentLanguage })
        });
      });

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const data = await response.json();
      renderResponse(data);

    } catch (err) {
      console.error('[Frontend] Error querying Brain API:', err);
      setState('ERROR');
      answerText.textContent = "Sorry, I'm having trouble connecting to the Brain API server right now.";
      setTimeout(() => setState('IDLE'), 2500);
    }
  }

  // Render Response Payload & Start Speech / Lip-Sync
  function renderResponse(data) {
    const answer = data.answer || "No response received.";
    const mode = data.mode || "grounded";
    const emotion = data.emotion || "neutral";
    const gesture = data.gesture || "explaining";
    const citations = data.citations || [];

    // Display Text
    answerText.textContent = answer;
    
    // Update Mode & Mascot Tags
    modeBadge.textContent = `Mode: ${mode}`;
    modeBadge.className = `tag mode-tag ${mode === 'grounded' ? 'mode-grounded' : 'mode-insufficient'}`;
    emotionBadge.textContent = `Emotion: ${emotion}`;
    gestureBadge.textContent = `Gesture: ${gesture}`;

    mascot.setEmotion(emotion);
    mascot.setGesture(gesture);

    // Render Citations
    renderCitations(citations);

    // Trigger Speech & Lip-Sync
    speakText(answer, () => {
      setState('IDLE');
    });
  }

  // Render Provenance Citations
  function renderCitations(citations) {
    citationCount.textContent = citations.length;
    citationsList.innerHTML = '';

    if (!citations || citations.length === 0) {
      citationsList.innerHTML = '<div class="empty-citations">No explicit citations returned for this query.</div>';
      return;
    }

    citations.forEach(c => {
      const card = document.createElement('div');
      card.className = 'citation-card';
      card.innerHTML = `
        <div class="citation-source">${c.source || 'GRBMP Document'}</div>
        <div class="citation-meta">
          ${c.file_name ? `File: ${c.file_name}` : ''} 
          ${c.page ? `• Page ${c.page}` : ''} 
          ${c.section ? `• ${c.section}` : ''}
        </div>
      `;
      citationsList.appendChild(card);
    });
  }

  // Text-To-Speech with Real-Time Lip-Sync
  function speakText(text, onComplete) {
    if (!speechSynth) {
      setState('SPEAKING');
      setTimeout(onComplete, 3000);
      return;
    }

    // Cancel ongoing speech
    speechSynth.cancel();
    setState('SPEAKING');

    speechUtterance = new SpeechSynthesisUtterance(text);
    speechUtterance.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
    speechUtterance.rate = 1.0;
    speechUtterance.pitch = 1.0;

    // Simulate Lip-Sync mouth movement while speaking
    let lipSyncInterval = setInterval(() => {
      if (speechSynth.speaking) {
        // Generate simulated RMS aperture between 0.1 and 0.95
        const aperture = Math.sin(Date.now() / 80) * 0.4 + 0.5;
        mascot.setMouthAperture(aperture);
        vizFill.style.width = `${aperture * 100}%`;
      }
    }, 60);

    speechUtterance.onend = () => {
      clearInterval(lipSyncInterval);
      mascot.setMouthAperture(0);
      vizFill.style.width = '0%';
      if (onComplete) onComplete();
    };

    speechUtterance.onerror = (err) => {
      console.warn('[Frontend TTS] Speech error:', err);
      clearInterval(lipSyncInterval);
      mascot.setMouthAperture(0);
      vizFill.style.width = '0%';
      if (onComplete) onComplete();
    };

    speechSynth.speak(speechUtterance);
  }

  // Web Speech API Voice Recognition (STT)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('mic-listening');
      setState('LISTENING');
      voiceStatusMsg.textContent = 'Listening... Speak your question clearly.';
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      voiceStatusMsg.textContent = `Transcribed: "${transcript}"`;
      questionInput.value = transcript;
      processQuestion(transcript);
    };

    recognition.onerror = (event) => {
      console.warn('[Frontend STT] Speech recognition error:', event.error);
      voiceStatusMsg.textContent = `Voice input error: ${event.error}`;
      stopListening();
    };

    recognition.onend = () => {
      stopListening();
    };
  } else {
    micBtn.title = 'Web Speech API not supported in this browser';
  }

  micBtn.addEventListener('click', () => {
    if (!recognition) {
      alert('Speech recognition is not supported in this browser. Please type your question.');
      return;
    }
    if (isListening) {
      recognition.stop();
      stopListening();
    } else {
      recognition.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
      recognition.start();
    }
  });

  function stopListening() {
    isListening = false;
    micBtn.classList.remove('mic-listening');
    if (currentState === 'LISTENING') {
      setState('IDLE');
    }
  }
});
