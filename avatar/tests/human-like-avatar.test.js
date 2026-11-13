const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

// Extract classifyResponseContext directly from app.js for direct isolated testing
const appJsPath = path.join(__dirname, '..', 'app.js');
const appJsContent = fs.readFileSync(appJsPath, 'utf8');

// Isolate classifyResponseContext
const fnMatch = appJsContent.match(/function classifyResponseContext\s*\([\s\S]*?\n  \}/);
if (!fnMatch) {
  throw new Error('classifyResponseContext function not found in app.js');
}

const classifyResponseContext = new Function(`
  ${fnMatch[0]}
  return classifyResponseContext;
`)();

// 1. Context-Aware Avatar Behaviour Tests (Phase 2)
test('classifyResponseContext accurately categorizes Greetings in English and Indic scripts', () => {
  const enGreeting = classifyResponseContext('Namaste! I am Chacha Chaudhary, your official Ganga guide.');
  assert.equal(enGreeting.state, 'GREETING');
  assert.equal(enGreeting.emotion, 'happy');
  assert.equal(enGreeting.gesture, 'Praying');

  const enHello = classifyResponseContext('Hello and welcome to Ganga AI Mascot!');
  assert.equal(enHello.state, 'GREETING');
  assert.equal(enHello.emotion, 'happy');
  assert.equal(enHello.gesture, 'Waving');

  const hiGreeting = classifyResponseContext('नमस्ते! मैं चाचा चौधरी हूँ। गंगा नदी के बारे में पूछें।');
  assert.equal(hiGreeting.state, 'GREETING');
  assert.equal(hiGreeting.emotion, 'happy');
  assert.equal(hiGreeting.gesture, 'Praying');

  const hiPranam = classifyResponseContext('प्रणाम! स्वागत है आपका।');
  assert.equal(hiPranam.state, 'GREETING');
  assert.equal(hiPranam.emotion, 'happy');
  assert.equal(hiPranam.gesture, 'Praying');
});

test('classifyResponseContext identifies Critical Warnings, Alerts and Pollution Advisories', () => {
  const alert = classifyResponseContext('Warning: Critical pollution levels detected at downstream discharge point. Prohibited activities carry penalties.');
  assert.equal(alert.state, 'IMPORTANT_ALERT');
  assert.equal(alert.emotion, 'surprised');
  assert.equal(alert.gesture, 'Pointing_Forward');

  const hiAlert = classifyResponseContext('चेतावनी: गंगा जल में अपशिष्ट बहाना प्रतिबंधित और दंडनीय है। सावधान रहें।');
  assert.equal(hiAlert.state, 'IMPORTANT_ALERT');
  assert.equal(hiAlert.emotion, 'surprised');
  assert.equal(hiAlert.gesture, 'Pointing_Forward');
});

test('classifyResponseContext recognizes Celebratory, Joyful and Positive Milestones', () => {
  const happy = classifyResponseContext('Congratulations! The water quality at Rishikesh is pristine and purest along the stretch.');
  assert.equal(happy.state, 'HAPPY');
  assert.equal(happy.emotion, 'happy');
  assert.equal(happy.gesture, 'Happy_Idle');

  const hiHappy = classifyResponseContext('शानदार! गंगा स्वच्छता अभियान के तहत बहुत सराहनीय सफलता प्राप्त हुई है।');
  assert.equal(hiHappy.state, 'HAPPY');
  assert.equal(hiHappy.emotion, 'happy');
  assert.equal(hiHappy.gesture, 'Happy_Idle');
});

test('classifyResponseContext identifies Apologetic and Insufficient Evidence responses', () => {
  const sorry = classifyResponseContext('I apologize, but there is insufficient evidence in the knowledge base regarding this question.', '', { mode: 'insufficient-evidence' });
  assert.equal(sorry.state, 'APOLOGETIC');
  assert.equal(sorry.emotion, 'confused');
  assert.equal(sorry.gesture, 'Defeat_Idle');

  const hiSorry = classifyResponseContext('माफ़ कीजिए, इस विषय पर अभी अभिलेख उपलब्ध नहीं हैं।');
  assert.equal(hiSorry.state, 'APOLOGETIC');
  assert.equal(hiSorry.emotion, 'confused');
  assert.equal(hiSorry.gesture, 'Defeat_Idle');
});

test('classifyResponseContext recognizes Inquisitive and Clarification questions', () => {
  const q = classifyResponseContext('Could you please clarify whether you mean the Upper Ganga or Lower Ganga stretch?');
  assert.equal(q.state, 'QUESTION');
  assert.equal(q.emotion, 'thinking');
  assert.equal(q.gesture, 'Looking');

  const questionMark = classifyResponseContext('Would you like to know more about the six headstreams?');
  assert.equal(questionMark.state, 'QUESTION');
  assert.equal(questionMark.emotion, 'thinking');
  assert.equal(questionMark.gesture, 'Looking');
});

test('classifyResponseContext identifies Technical, CPCB, and Water Quality metrics', () => {
  const tech = classifyResponseContext('According to CPCB monitoring, the Dissolved Oxygen (DO) is 7.5 mg/L and Biochemical Oxygen Demand (BOD) is 2.1 mg/L.');
  assert.equal(tech.state, 'TECHNICAL');
  assert.equal(tech.emotion, 'neutral');
  assert.equal(tech.gesture, 'Acknowledging');

  const tableData = classifyResponseContext('Here is the water quality data:', '', { tables: [{ title: 'CPCB', columns: ['pH', 'DO'], rows: [['7.2', '6.8']] }] });
  assert.equal(tableData.state, 'TECHNICAL');
  assert.equal(tableData.gesture, 'Acknowledging');
});

test('classifyResponseContext identifies Long Explanations and Factual Multi-Point Answers', () => {
  const explanation = classifyResponseContext('River Ganga originates from Gangotri Glacier as Bhagirathi and meets Alaknanda at Devprayag to form Ganga. The river basin covers multiple states and supports millions.');
  assert.equal(explanation.state, 'EXPLAINING');
  assert.equal(explanation.gesture, 'Pointing_Forward');
});

// 2. Accurate Lip-Sync Architecture & Viseme Tests (Phase 4)
test('mascot.js defines full semantic gesture action mappings matching 28 actions', () => {
  const mascotJsPath = path.join(__dirname, '..', 'mascot.js');
  const mascotContent = fs.readFileSync(mascotJsPath, 'utf8');

  // Must contain core semantic mappings
  assert.equal(mascotContent.includes("'idle': 'Idle'"), true);
  assert.equal(mascotContent.includes("'nod': 'Acknowledging'"), true);
  assert.equal(mascotContent.includes("'point': 'Pointing'"), true);
  assert.equal(mascotContent.includes("'explaining': 'Pointing_Forward'"), true);
  assert.equal(mascotContent.includes("'waving': 'Waving'"), true);
  assert.equal(mascotContent.includes("'thankful': 'Praying'"), true);
  assert.equal(mascotContent.includes("'laughing': 'Laughing_1'"), true);
  assert.equal(mascotContent.includes("'thinking': 'Looking'"), true);
  assert.equal(mascotContent.includes("'shaking_hands': 'Patting'"), true);

  // Must contain biological dynamics (saccades, blinks, prosody, asymmetric lerp)
  assert.equal(mascotContent.includes('currentGazePitch'), true);
  assert.equal(mascotContent.includes('blinkPhase'), true);
  assert.equal(mascotContent.includes('isDoubleBlink'), true);
  assert.equal(mascotContent.includes('speechPulse'), true);
  assert.equal(mascotContent.includes('stopAudioLipSync'), true);
});

test('mascot.js implements multi-stage lip-sync with noise gate and silence clamp', () => {
  const mascotJsPath = path.join(__dirname, '..', 'mascot.js');
  const mascotContent = fs.readFileSync(mascotJsPath, 'utf8');

  // Verify Spectral FFT Multi-band extraction
  assert.equal(mascotContent.includes('lowSum'), true);
  assert.equal(mascotContent.includes('midSum'), true);
  assert.equal(mascotContent.includes('highSum'), true);

  // Verify strict noise gate and silence clamp
  assert.equal(mascotContent.includes('amplitude < 0.038'), true);
  assert.equal(mascotContent.includes('this.targetMorphInfluences[openIdx] = 0.0'), true);
  assert.equal(mascotContent.includes('this.targetMorphInfluences[oIdx] = 0.0'), true);

  // Verify asymmetric spring blendshape interpolation
  assert.equal(mascotContent.includes('attackSpeed = 28.0'), true);
});

// 3. Centralized Event Controller Tests (Phase 5)
test('app.js integrates centralized avatarEventBus with lifecycle events', () => {
  assert.equal(appJsContent.includes('window.avatarEventBus = avatarEventBus'), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('response_started'"), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('response_completed'"), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('speech_started'"), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('speech_completed'"), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('listening_started'"), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('listening_completed'"), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('emotion_detected'"), true);
  assert.equal(appJsContent.includes("avatarEventBus.emit('interruption'"), true);
});
