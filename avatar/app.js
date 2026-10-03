/**
 * Main Application Orchestrator for Ganga AI Mascot UI
 * Production Integration: Chacha New 3D Avatar + Grounded RAG + Voice
 * 
 * Pipeline:
 * - User Question (Text/Voice) -> POST /api/integration/ask / /api/integration/stt
 * - Grounded RAG Brain -> EdgeTTS Audio -> Rhubarb Visemes Timeline
 * - MascotController: 28 Mixamo Skeletal Actions, Dynamic Viewport Framing, Zero T-Pose
 * - Audio Playback & Real-Time Lip-Sync Visualizer Synchronization
 */

document.addEventListener('DOMContentLoaded', () => {
  const mascot = new MascotController();

  // DOM Elements
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
  const inputLangHiBtn = document.getElementById('inputLangHi');
  const inputLangEnBtn = document.getElementById('inputLangEn');
  const outputLangHiBtn = document.getElementById('outputLangHi');
  const outputLangEnBtn = document.getElementById('outputLangEn');
  const vizFill = document.getElementById('vizFill');
  const vizLevel = document.getElementById('vizLevel');
  const voiceStatusMsg = document.getElementById('voiceStatusMsg');

  let currentInputLanguage = 'hi';
  let currentOutputLanguage = 'hi';
  let currentState = 'IDLE';

  // Audio Playback & Synchronization State
  let activeAudio = null;
  let lipSyncAnimationId = null;

  // Microphone Recording State (MediaRecorder)
  let mediaRecorder = null;
  let audioChunks = [];
  let isRecording = false;

  // Language selection handlers
  if (inputLangHiBtn && inputLangEnBtn) {
    inputLangHiBtn.addEventListener('click', () => setInputLanguage('hi'));
    inputLangEnBtn.addEventListener('click', () => setInputLanguage('en'));
  }
  if (outputLangHiBtn && outputLangEnBtn) {
    outputLangHiBtn.addEventListener('click', () => setOutputLanguage('hi'));
    outputLangEnBtn.addEventListener('click', () => setOutputLanguage('en'));
  }

  function setInputLanguage(lang) {
    currentInputLanguage = lang;
    if (lang === 'hi') {
      inputLangHiBtn.classList.add('active');
      inputLangEnBtn.classList.remove('active');
      questionInput.placeholder = 'गंगा नदी या नमामि गंगे से जुड़ा प्रश्न पूछें...';
    } else {
      inputLangEnBtn.classList.add('active');
      inputLangHiBtn.classList.remove('active');
      questionInput.placeholder = 'Type your question about Ganga, GRBMP, or pollution...';
    }
    updateLangBadge();
  }

  function setOutputLanguage(lang) {
    currentOutputLanguage = lang;
    if (lang === 'hi') {
      outputLangHiBtn.classList.add('active');
      outputLangEnBtn.classList.remove('active');
    } else {
      outputLangEnBtn.classList.add('active');
      outputLangHiBtn.classList.remove('active');
    }
    updateLangBadge();
  }

  function updateLangBadge() {
    if (responseLangBadge) {
      responseLangBadge.textContent = `In: ${currentInputLanguage.toUpperCase()} | Out: ${currentOutputLanguage.toUpperCase()}`;
    }
  }

  // Update UI State Badges & Synchronize Avatar State Machine
  function setState(state) {
    currentState = state;
    if (statusBadge) {
      statusBadge.className = `status-badge state-${state.toLowerCase()}`;
    }
    if (statusText) {
      statusText.textContent = state;
    }

    if (state === 'THINKING' || state === 'PROCESSING') {
      if (thinkingWave) thinkingWave.style.display = 'flex';
      if (submitBtn) submitBtn.disabled = true;
    } else {
      if (thinkingWave) thinkingWave.style.display = 'none';
      if (submitBtn) submitBtn.disabled = false;
    }

    // Forward state to Mascot 3D Engine
    if (mascot && mascot.setState) {
      mascot.setState(state);
    }
  }

  // Form Submission (Typed Question Pipeline)
  if (askForm) {
    askForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const question = questionInput.value.trim();
      if (!question) return;

      await processQuestion(question);
    });
  }

  // Main Question Pipeline (Typed Text)
  async function processQuestion(question) {
    if (currentState === 'SPEAKING' || currentState === 'THINKING') {
      stopCurrentSpeech();
    }

    // 1. Immediate visible reaction -> THINKING
    if (questionPromptView) questionPromptView.style.display = 'flex';
    if (userQuestionText) userQuestionText.textContent = question;
    if (answerText) {
      answerText.innerHTML = '<span class="progress-step searching">Consulting official GRBMP knowledge base...</span>';
    }
    setState('THINKING');

    const t_start = performance.now();

    // Progressive status update
    const progressTimer = setTimeout(() => {
      if (currentState === 'THINKING' && answerText) {
        answerText.innerHTML = '<span class="progress-step synthesizing">Synthesizing verified answer & neural voice...</span>';
      }
    }, 1500);

    try {
      // 2. Call Integration API endpoint (/api/integration/ask)
      const response = await fetch('/api/integration/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: question, 
          input_language: currentInputLanguage, 
          output_language: currentOutputLanguage 
        })
      });

      clearTimeout(progressTimer);

      if (!response.ok) {
        throw new Error(`Server returned status ${response.status}`);
      }

      const t_response = performance.now();
      const data = await response.json();
      renderResponse(data, t_start, t_response);

    } catch (err) {
      clearTimeout(progressTimer);
      console.error('[Frontend] Error querying Brain API:', err);
      setState('ERROR');
      if (answerText) {
        answerText.textContent = "Sorry, I am having trouble connecting to the Ganga AI Brain server right now. Please verify the backend service is running.";
      }
      setTimeout(() => setState('IDLE'), 2800);
    }
  }

  // Render Response Payload & Start Speech / Lip-Sync
  function renderResponse(data, t_start = null, t_response = null) {
    const answer = data.answer || data.text || "No response received.";
    const mode = data.mode || "grounded";
    const emotion = (data.emotion || "happy").toLowerCase();
    const gesture = (data.gesture || "explaining").toLowerCase();
    const citations = data.citations || [];

    // Display Answer Text
    if (answerText) {
      answerText.textContent = answer;
    }
    
    // Update Mode & Mascot Indicators
    if (modeBadge) {
      modeBadge.textContent = `Mode: ${mode.charAt(0).toUpperCase() + mode.slice(1)}`;
      modeBadge.className = `tag mode-tag ${mode === 'grounded' ? 'mode-grounded' : 'mode-insufficient'}`;
    }
    if (emotionBadge) {
      emotionBadge.textContent = `Emotion: ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}`;
    }
    if (gestureBadge) {
      gestureBadge.textContent = `Gesture: ${gesture}`;
    }

    // Synchronize deterministic state machine to SPEAKING with active emotion and gesture
    mascot.setState('SPEAKING', { emotion: emotion, gesture: gesture });

    // Render Citations
    renderCitations(citations);

    // Trigger Real Acoustic Audio & Rhubarb Lip-Sync Playback
    playProductionSpeech(data, answer, gesture, t_start, t_response);
  }

  // Render Provenance Citations
  function renderCitations(citations) {
    if (citationCount) citationCount.textContent = citations ? citations.length : 0;
    if (!citationsList) return;

    citationsList.innerHTML = '';

    if (!citations || citations.length === 0) {
      citationsList.innerHTML = '<div class="empty-citations">No citations returned for this query. Response synthesized from conversational context.</div>';
      return;
    }

    citations.forEach((c) => {
      const card = document.createElement('div');
      card.className = 'citation-card';
      card.innerHTML = `
        <div class="citation-source">${c.source || 'GRBMP Knowledge Document'}</div>
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

  function playProductionSpeech(data, fallbackText, initialGesture = 'nod', t_start = null, t_response = null) {
    // Cancel any previous speech playback cleanly
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

// One-shot gesture transitions to Talking loop via mascot mixer finished event

      activeAudio.onplay = () => {
        if (t_start) {
          const t_first_audio = performance.now();
          const backendMs = data.timing ? data.timing.total_backend_ms : (t_response ? (t_response - t_start).toFixed(1) : 'N/A');
          const t11Ms = t_response ? (t_response - t_start).toFixed(1) : 'N/A';
          const t12Ms = (t_first_audio - t_start).toFixed(1);
          console.log(`[LATENCY BREAKDOWN] T0->T10 Backend: ${backendMs}ms | T11 Browser Received: ${t11Ms}ms | T12 Time-to-First-Audio: ${t12Ms}ms`);
          if (data.timing) {
            console.log('[STAGE TIMESTAMPS]', data.timing);
          }
        }
        syncRhubarbLipSync(cues, data.rms_lip_sync);
      };

      activeAudio.onended = () => {
        stopCurrentSpeech();
        setState('IDLE');
        mascot.setState('IDLE');
      };

      activeAudio.onerror = (err) => {
        console.warn('[Frontend Audio] Error playing audio WAV, falling back to speech synthesis:', err);
        stopCurrentSpeech();
        fallbackBrowserTTS(fallbackText);
      };

      activeAudio.play().then(() => {
        console.log('[Frontend Audio] Neural voice audio playing successfully.');
      }).catch((err) => {
        console.warn('[Frontend Audio] Autoplay blocked, falling back to speech synthesis:', err);
        if (!activeAudio || activeAudio.paused) {
          fallbackBrowserTTS(fallbackText);
        }
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
      } else {
        // Syllabic speech cadence fallback (~4.5 Hz speech articulation rhythm)
        const cycle = Math.sin(currentTime * 16.0);
        if (cycle > 0.08) {
          matchedViseme = cycle > 0.60 ? 'Viseme_A' : 'Viseme_O';
        } else {
          matchedViseme = 'Viseme_Silence';
        }
      }

      // Forward to mascot controller
      mascot.setViseme(matchedViseme, 1.0);

      // 2. Real-Time RMS Audio Visualizer Update
      if (vizFill) {
        if (matchedViseme !== 'Viseme_Silence') {
          const simulatedLevel = 60 + Math.floor(Math.sin(currentTime * 18) * 25 + 10);
          vizFill.style.width = `${simulatedLevel}%`;
          if (vizLevel) vizLevel.textContent = `${simulatedLevel}%`;
          vizFill.style.backgroundColor = '#38bdf8';
        } else {
          vizFill.style.width = '8%';
          if (vizLevel) vizLevel.textContent = '8%';
          vizFill.style.backgroundColor = '#64748b';
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
    if (mascot) {
      mascot.clearViseme();
    }
    if (vizFill) {
      vizFill.style.width = '0%';
    }
    if (vizLevel) {
      vizLevel.textContent = '0%';
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
    mascot.playAction('Talking', 0.35);

    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = currentOutputLanguage === 'hi' ? 'hi-IN' : 'en-US';
    utter.rate = 1.0;

    let simInterval = setInterval(() => {
      if (window.speechSynthesis.speaking) {
        const ap = Math.sin(Date.now() / 90) * 0.4 + 0.5;
        mascot.setMouthAperture(ap);
        if (vizFill) vizFill.style.width = `${Math.round(ap * 100)}%`;
        if (vizLevel) vizLevel.textContent = `${Math.round(ap * 100)}%`;
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

  // =========================================================================
  // Production Hardware Microphone (MediaRecorder -> Backend Vosk STT)
  // =========================================================================

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
        if (voiceStatusMsg) voiceStatusMsg.textContent = 'Transcribing with local Vosk STT...';
        setState('THINKING');

        // Send to production backend STT endpoint
        await uploadAudioForSTT(audioBlob);
      };

      mediaRecorder.start();
      isRecording = true;
      micBtn.classList.add('mic-listening');
      setState('LISTENING');
      if (voiceStatusMsg) voiceStatusMsg.textContent = 'Listening... Speak clearly, click mic again to send.';

    } catch (err) {
      console.warn('[Frontend Mic] getUserMedia failed or denied. Falling back to Web Speech API:', err);
      startWebSpeechFallback();
    }
  }

  function stopMicrophoneRecording() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
      if (micBtn) micBtn.classList.remove('mic-listening');
    }
  }

  async function uploadAudioForSTT(blob) {
    try {
      const formData = new FormData();
      formData.append('file', blob, 'user_speech.webm');

      const response = await fetch(`/api/integration/stt?input_language=${currentInputLanguage}&output_language=${currentOutputLanguage}`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`STT server returned status ${response.status}`);
      }

      const data = await response.json();
      if (voiceStatusMsg) {
        voiceStatusMsg.textContent = data.question ? `Heard: "${data.question}"` : 'Transcription complete.';
      }
      if (data.question && questionInput) {
        questionInput.value = data.question;
      }
      if (data.question && userQuestionText) {
        userQuestionText.textContent = data.question;
      }
      renderResponse(data);

    } catch (err) {
      console.error('[Frontend STT] Failed to transcribe with backend Vosk:', err);
      if (voiceStatusMsg) voiceStatusMsg.textContent = 'STT transcription failed. Please try typing.';
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
    rec.lang = currentInputLanguage === 'hi' ? 'hi-IN' : 'en-US';

    rec.onstart = () => {
      if (micBtn) micBtn.classList.add('mic-listening');
      setState('LISTENING');
      if (voiceStatusMsg) voiceStatusMsg.textContent = 'Listening (Browser fallback)... Speak clearly.';
    };

    rec.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      if (voiceStatusMsg) voiceStatusMsg.textContent = `Transcribed: "${transcript}"`;
      if (questionInput) questionInput.value = transcript;
      if (micBtn) micBtn.classList.remove('mic-listening');
      processQuestion(transcript);
    };

    rec.onerror = (e) => {
      console.warn('[Frontend STT Fallback] Error:', e.error);
      if (micBtn) micBtn.classList.remove('mic-listening');
      setState('IDLE');
    };

    rec.onend = () => {
      if (micBtn) micBtn.classList.remove('mic-listening');
      if (currentState === 'LISTENING') {
        setState('IDLE');
      }
    };

    rec.start();
  }
});
