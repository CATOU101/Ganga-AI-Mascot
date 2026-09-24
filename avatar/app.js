/**
 * Main Application Orchestrator for Ganga AI Mascot UI
 * Production Integration: Member 2 Digital Avatar + Voice System
 * 
 * Pipeline:
 * - Typed Question -> POST /api/integration/ask -> Brain -> EdgeTTS -> Rhubarb -> Three.js GLB
 * - Microphone -> MediaRecorder -> POST /api/integration/stt -> Vosk STT -> Brain -> EdgeTTS -> Rhubarb -> Three.js GLB
 * - Full 35 Morph Targets + 9 Mixamo Actions + Procedural Blinking
 * - Preserves Web Speech API and SpeechSynthesis as emergency fallbacks
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

  // Audio Playback & Synchronization State
  let activeAudio = null;
  let lipSyncAnimationId = null;

  // Microphone Recording State (MediaRecorder)
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;

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

  // Update UI State Badges & Synchronize Avatar State Machine
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

    // Forward state to Member 2 avatar state machine
    if (mascot && mascot.setState) {
      mascot.setState(state);
    }
  }

  // Form Submission (Typed Question Pipeline)
  askForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    await processQuestion(question);
  });

  // Main Question Pipeline (Typed Text)
  async function processQuestion(question) {
    if (currentState === 'SPEAKING' || currentState === 'THINKING') return;

    // 1. Update UI to PROCESSING -> THINKING
    questionPromptView.style.display = 'block';
    userQuestionText.textContent = question;
    answerText.textContent = '';
    setState('THINKING');

    try {
      // 2. Call Integration API endpoint (/api/integration/ask)
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
    const answer = data.answer || data.text || "No response received.";
    const mode = data.mode || "grounded";
    const emotion = data.emotion || "happy";
    const gesture = data.gesture || "nod";
    const citations = data.citations || [];

    // Display Text
    answerText.textContent = answer;
    
    // Update Mode & Mascot Tags
    modeBadge.textContent = `Mode: ${mode}`;
    modeBadge.className = `tag mode-tag ${mode === 'grounded' ? 'mode-grounded' : 'mode-insufficient'}`;
    emotionBadge.textContent = `Emotion: ${emotion}`;
    gestureBadge.textContent = `Gesture: ${gesture}`;

    // Apply Member 2 composite emotion & body gesture
    mascot.setEmotion(emotion, 0.85);
    mascot.setGesture(gesture);

    // Render Citations
    renderCitations(citations);

    // Trigger Real Member 2 Acoustic Audio & Lip-Sync Playback
    playProductionSpeech(data, answer);
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

  // =========================================================================
  // Production Audio & Rhubarb Lip-Sync Player
  // =========================================================================

  function playProductionSpeech(data, fallbackText) {
    // Cancel any previous speech playback
    stopCurrentSpeech();

    let src = null;
    if (data.audio_data_base64) {
      src = `data:audio/wav;base64,${data.audio_data_base64}`;
    } else if (data.audio) {
      if (data.audio.startsWith('data:') || data.audio.startsWith('http') || data.audio.startsWith('/')) {
        src = data.audio;
      } else {
        src = `data:audio/wav;base64,${data.audio}`;
      }
    } else if (data.audio_url) {
      src = data.audio_url;
    }
    const rhubarbData = data.rhubarb_lipsync || data.lip_sync;

    if (src) {
      activeAudio = new Audio(src);

      // Extract Rhubarb cues
      const cues = (rhubarbData && (rhubarbData.mouth_cues || rhubarbData.visemes)) || [];

      setState('SPEAKING');

      activeAudio.onplay = () => {
        syncRhubarbLipSync(cues, data.rms_lip_sync);
      };

      activeAudio.onended = () => {
        stopCurrentSpeech();
        setState('IDLE');
      };

      activeAudio.onerror = (err) => {
        console.warn('[Frontend Audio] Error playing audio WAV, falling back to speech synthesis:', err);
        fallbackBrowserTTS(fallbackText);
      };

      activeAudio.play().catch((err) => {
        console.warn('[Frontend Audio] Autoplay blocked or failed, using fallback:', err);
        fallbackBrowserTTS(fallbackText);
      });

    } else {
      // Audio payload absent: fallback to browser TTS
      fallbackBrowserTTS(fallbackText);
    }
  }

  function syncRhubarbLipSync(cues, rmsFrames) {
    if (!activeAudio) return;

    const updateFrame = () => {
      if (!activeAudio || activeAudio.paused || activeAudio.ended) {
        return;
      }

      const currentTime = activeAudio.currentTime;

      // 1. Acoustic Rhubarb Phonetic Alignment
      let matchedViseme = 'Viseme_Silence';
      if (cues && cues.length > 0) {
        const activeCue = cues.find((c) => currentTime >= c.start && currentTime <= c.end);
        if (activeCue) {
          matchedViseme = activeCue.viseme || activeCue.value || 'Viseme_A';
        }
      }

      // Apply to 35 Morph Targets
      mascot.setViseme(matchedViseme, 1.0);

      // Update Visualizer
      if (vizFill) {
        if (matchedViseme !== 'Viseme_Silence') {
          vizFill.style.width = '75%';
          vizFill.style.backgroundColor = '#38bdf8';
        } else {
          vizFill.style.width = '10%';
          vizFill.style.backgroundColor = '#94a3b8';
        }
      }

      lipSyncAnimationId = requestAnimationFrame(updateFrame);
    };

    lipSyncAnimationId = requestAnimationFrame(updateFrame);
  }

  function stopCurrentSpeech() {
    if (lipSyncAnimationId) {
      cancelAnimationFrame(lipSyncAnimationId);
      lipSyncAnimationId = null;
    }
    if (activeAudio) {
      activeAudio.pause();
      activeAudio.currentTime = 0;
      activeAudio = null;
    }
    mascot.clearViseme();
    if (vizFill) {
      vizFill.style.width = '0%';
    }
  }

  // Emergency Browser SpeechSynthesis Fallback
  function fallbackBrowserTTS(text) {
    if (!window.speechSynthesis) {
      setState('IDLE');
      return;
    }
    window.speechSynthesis.cancel();
    setState('SPEAKING');

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';
    utter.rate = 1.0;

    let simInterval = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        const ap = Math.sin(Date.now() / 90) * 0.4 + 0.5;
        mascot.setMouthAperture(ap);
        if (vizFill) vizFill.style.width = `${ap * 100}%`;
      }
    }, 60);

    utter.onend = () => {
      clearInterval(simInterval);
      mascot.clearViseme();
      if (vizFill) vizFill.style.width = '0%';
      setState('IDLE');
    };

    utter.onerror = () => {
      clearInterval(simInterval);
      mascot.clearViseme();
      if (vizFill) vizFill.style.width = '0%';
      setState('IDLE');
    };

    window.speechSynthesis.speak(utter);
  }

  // =========================================================================
  // Production Hardware Microphone (MediaRecorder -> Backend Vosk STT)
  // =========================================================================

  micBtn.addEventListener('click', async () => {
    if (isRecording) {
      stopMicrophoneRecording();
    } else {
      await startMicrophoneRecording();
    }
  });

  async function startMicrophoneRecording() {
    if (currentState === 'SPEAKING' || currentState === 'THINKING') return;

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn('[Frontend Mic] MediaDevices API not supported, trying Web Speech API fallback.');
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
        // Stop audio tracks
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        voiceStatusMsg.textContent = 'Transcribing with local Vosk STT...';
        setState('THINKING');

        // Send to production backend STT endpoint
        await uploadAudioForSTT(audioBlob);
      };

      mediaRecorder.start();
      isRecording = true;
      micBtn.classList.add('mic-listening');
      setState('LISTENING');
      voiceStatusMsg.textContent = 'Listening (Member 2 Vosk)... Click mic again to send.';

    } catch (err) {
      console.warn('[Frontend Mic] getUserMedia failed or denied. Falling back to Web Speech API:', err);
      startWebSpeechFallback();
    }
  }

  function stopMicrophoneRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      micBtn.classList.remove('mic-listening');
    }
  }

  async function uploadAudioForSTT(blob) {
    try {
      const formData = new FormData();
      formData.append('file', blob, 'user_speech.webm');

      const response = await fetch(`/api/integration/stt?language=${currentLanguage}`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`STT server returned status ${response.status}`);
      }

      const data = await response.json();
      voiceStatusMsg.textContent = data.question ? `Heard: "${data.question}"` : 'Transcription complete.';
      if (data.question) {
        questionInput.value = data.question;
        userQuestionText.textContent = data.question;
      }
      renderResponse(data);

    } catch (err) {
      console.error('[Frontend STT] Failed to transcribe with backend Vosk:', err);
      voiceStatusMsg.textContent = 'STT transcription failed. Please try typing.';
      setState('ERROR');
      setTimeout(() => setState('IDLE'), 2000);
    }
  }

  // Emergency Web Speech API Fallback
  function startWebSpeechFallback() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) {
      alert('Microphone input is not available in this browser. Please type your question.');
      return;
    }

    const rec = new SpeechRec();
    rec.continuous = false;
    rec.interimResults = false;
    rec.lang = currentLanguage === 'hi' ? 'hi-IN' : 'en-US';

    rec.onstart = () => {
      micBtn.classList.add('mic-listening');
      setState('LISTENING');
      voiceStatusMsg.textContent = 'Listening (Browser fallback)... Speak clearly.';
    };

    rec.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      voiceStatusMsg.textContent = `Transcribed: "${transcript}"`;
      questionInput.value = transcript;
      micBtn.classList.remove('mic-listening');
      processQuestion(transcript);
    };

    rec.onerror = (e) => {
      console.warn('[Frontend STT Fallback] Error:', e.error);
      micBtn.classList.remove('mic-listening');
      setState('IDLE');
    };

    rec.onend = () => {
      micBtn.classList.remove('mic-listening');
      if (currentState === 'LISTENING') {
        setState('IDLE');
      }
    };

    rec.start();
  }
});
