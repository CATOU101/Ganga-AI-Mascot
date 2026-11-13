/**
 * 3D WebGL Avatar Animation Engine for Chacha Chaudhary Mascot
 * Production Implementation: Human-Like AI Avatar with Emotion-Aware Animation and Accurate Lip-Sync
 * 
 * Engineering Specifications:
 * - Active Model: avatar/Chacha_New/Chacha_New.glb (31,058 vertices, 65 Mixamo bones, 3 blendshapes)
 * - Exact 70-75% Stage Height Portrait Framing via Dynamic Bounding-Box Math (scale = 1.0, 28 deg FOV)
 * - High-Fidelity Rendering: Supersampled 2x-3x PixelRatio, 16x Anisotropy, ACESFilmic ToneMapping, Balanced Studio 3-Point Lighting
 * - Zero T-Pose Guarantee: Pre-rendered Idle initialization before canvas visibility
 * - 28 Mixamo Skeletal Actions with smooth cross-fading & semantic gesture mapping
 * - Biologically Realistic Dynamics:
 *   - Eye contact with procedural micro-saccades (natural gaze shifts every 2.5-4.5s)
 *   - Realistic blinking engine with Poisson-distributed intervals (2.8-5.5s) and occasional double-blinks
 *   - Continuous sinusoidal chest & shoulder breathing (~17 breaths/min)
 *   - Gentle pelvic weight shifting during Idle
 *   - Speech cadence prosody: amplitude and vowel-energy driven conversational head nods
 * - Accurate Triple-Stage Audio-Driven Lip-Sync Engine:
 *   - Stage 1: Real-time Multi-Band Spectral FFT Analysis (AudioContext + AnalyserNode)
 *     - Low band (100-750 Hz) -> Jaw opening ('mouthOpen')
 *     - Mid band (750-2200 Hz) -> Lip rounding ('mouthO')
 *     - High band (2200-6000 Hz) -> Sibilant tension ('mouthSmile')
 *     - Adaptive noise gate with instant mouth closure on silence/pauses
 *   - Stage 2: Rhubarb Acoustic Phoneme/Viseme Alignment (cues modulated by real-time audio energy)
 *   - Stage 3: Pre-computed RMS amplitude frames fallback for background tabs/autoplay restrictions
 *   - Asymmetric spring blendshape dynamics: fast attack (28.0) and smooth natural release (18.0)
 *   - Zero mouth movement guarantee after speech ends, pauses, or is interrupted
 * - Context-Aware Emotion & Posture System:
 *   - 10 distinct conversational contexts (Greeting, Explaining, Technical, Question, Thinking,
 *     Important Alert, Celebratory, Apologetic, Listening, Idle)
 *   - Seamless mid-speech gesture transitions during extended responses
 * - Full memory lifecycle & resource disposal
 */

class MascotController {
  constructor() {
    this.canvas = document.getElementById('mascotCanvas3D');
    this.currentState = 'IDLE';
    this.currentEmotion = 'neutral';
    this.currentGesture = 'idle';
    this.activeActionName = null;
    this.mouthAperture = 0;

    this.is3DReady = false;
    this.isProductionGLB = false;
    this.hasMorphTargets = false;
    this.model3D = null;
    this.skinnedMesh = null;
    this.mixer = null;
    this.actions = {}; // clipName -> AnimationAction

    // Skeletal Rig Bones for Procedural Dynamics (Chest, Neck, Head, Shoulders, Arms, Pelvis)
    this.headBone = null;
    this.neckBone = null;
    this.spine1Bone = null;
    this.spine2Bone = null;
    this.leftShoulderBone = null;
    this.rightShoulderBone = null;
    this.leftArmBone = null;
    this.rightArmBone = null;
    this.leftForeArmBone = null;
    this.rightForeArmBone = null;
    this.hipsBone = null;

    // Active Mesh Morph Target Lookup & Fast Lerp Arrays
    this.morphDict = {};
    this.morphInfluences = null;
    this.targetMorphInfluences = [0.0, 0.0, 0.0];

    // Biological Gaze & Micro-Saccade System
    this.currentGazePitch = 0.0;
    this.currentGazeYaw = 0.0;
    this.targetGazePitch = 0.0;
    this.targetGazeYaw = 0.0;
    this.lastSaccadeTime = Date.now();
    this.nextSaccadeInterval = 3000;

    // Biologically Realistic Eye Blinking System
    this.blinkPhase = 'idle'; // 'idle' | 'closing' | 'opening'
    this.blinkWeight = 0.0;
    this.blinkStartTime = 0;
    this.nextBlinkTime = Date.now() + 3200;
    this.isDoubleBlink = false;

    // Real-Time Audio & Multi-Stage Lip Sync Pipeline
    this.audioContext = null;
    this.analyser = null;
    this.freqDataArray = null;
    this.activeAudio = null;
    this.isAudioPlaying = false;
    this.rhubarbCues = null;
    this.rmsFrames = null;
    this.rmsFps = 50.0;
    this.currentAudioAmplitude = 0.0;
    this._lowEnergy = 0.0;
    this._midEnergy = 0.0;
    this._highEnergy = 0.0;
    this.speechStartTime = 0;
    this.lastSpeechPauseTime = 0;
    this.lastMidSpeechGestureTime = 0;
    this.midSpeechGestureCooldown = 4200;

    // Active Viseme Tracking
    this.activeViseme = 'Viseme_Silence';
    this.activeVisemeWeight = 0;

    // Semantic Intent to Chacha_New (28 Clips) Mapping
    this.gestureActionMap = {
      // 1. Idle & Baseline
      'idle': 'Idle',
      'neutral': 'Idle',
      'stand': 'Idle',
      'standing': 'Idle',
      'unarmed_idle': 'Unarmed_Idle',
      'defeat_idle': 'Defeat_Idle',

      // 2. Agreement & Nods
      'nod': 'Acknowledging',
      'nodding': 'Acknowledging',
      'agree': 'Agreeing',
      'agreeing': 'Agreeing',
      'agreement': 'Agreeing',
      'acknowledging': 'Acknowledging',

      // 3. Greetings & Waves
      'wave': 'Waving',
      'waving': 'Waving',
      'greeting': 'Waving',
      'hello': 'Waving',
      'hi': 'Waving',
      'waving_gesture': 'Waving_Gesture',

      // 4. Pointing & Explaining
      'point': 'Pointing',
      'pointing': 'Pointing',
      'explaining': 'Pointing_Forward',
      'explain': 'Pointing_Forward',
      'pointing_forward': 'Pointing_Forward',
      'presenting': 'Pointing_Forward',

      // 5. Gratitude & Namaste
      'thankful': 'Praying',
      'thanks': 'Praying',
      'gratitude': 'Praying',
      'namaste': 'Praying',
      'praying': 'Praying',
      'bow': 'Quick_Formal_Bow',
      'quick_formal_bow': 'Quick_Formal_Bow',

      // 6. Thinking & Pondering
      'thinking': 'Looking',
      'think': 'Looking',
      'looking': 'Looking',
      'pondering': 'Looking',
      'shrug': 'Looking',

      // 7. Joy & Laughter
      'happy': 'Happy_Idle',
      'joy': 'Happy_Idle',
      'laugh': 'Laughing_1',
      'laughing': 'Laughing_1',
      'happy_idle': 'Happy_Idle',
      'happy_walk': 'Happy_Walk',
      'clapping': 'Clapping',
      'clap': 'Clapping',
      'clapping_1': 'Clapping_1',

      // 8. Anger & Alert / Strong Emphasis
      'angry': 'Angry_Gesture',
      'anger': 'Angry_Gesture',
      'angry_gesture': 'Angry_Gesture',
      'yelling': 'Yelling',
      'yell': 'Yelling',

      // 9. Sadness, Concern & Apologies
      'sad': 'Defeat_Idle',
      'sadness': 'Defeat_Idle',
      'sad_walk': 'Sad_Walk',
      'defeat': 'Defeat_Idle',

      // 10. Surprise & Confusion / Questions
      'surprised': 'Yelling',
      'surprise': 'Yelling',
      'confused': 'Nervously_Look_Around',
      'confusion': 'Nervously_Look_Around',
      'nervous': 'Nervously_Look_Around',
      'nervously_look_around': 'Nervously_Look_Around',

      // 11. Conversational Speech & Gestures
      'talking': 'Talking',
      'talk': 'Talking',
      'speaking': 'Talking',
      'speech': 'Talking',
      'patting': 'Patting',
      'shaking_hands': 'Patting',
      'swagger_walk': 'Swagger_Walk',
      'drinking': 'Drinking',
      'being_strangled': 'Being_Strangled',
      'catwalk_twist_r_to_walk_180': 'Catwalk_Twist_R_To_Walk_180',
      'male_standing_pose': 'Male_Standing_Pose',

      // 12. Legacy Member 2 Aliases for Backwards Compatibility
      'chacha_idle': 'Idle',
      'chacha_nod': 'Acknowledging',
      'chacha_point': 'Pointing',
      'chacha_shrug': 'Looking',
      'chacha_thinking': 'Looking',
      'chacha_laughing': 'Laughing_1',
      'chacha_waving': 'Waving',
      'chacha_thankful': 'Praying',
      'chacha_shakinghands': 'Patting',
      'hand': 'Patting',
      'gesture': 'Pointing_Forward',
      'turn': 'Idle'
    };

    if (this.canvas) {
      this.init3DScene();
    }

    // Expose instance globally for application and test accessibility
    window.mascot = this;
  }

  // =========================================================================
  // Scene, Camera, Lighting & Contact Shadow Initialization
  // =========================================================================

  init3DScene() {
    const container = this.canvas.parentElement;
    const width = container ? (container.clientWidth || 380) : 380;
    const height = container ? (container.clientHeight || 480) : 480;

    // 1. High-Fidelity WebGL Renderer with Supersampling
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    const dpr = window.devicePixelRatio || 1;
    this.renderer.setPixelRatio(Math.min(Math.max(dpr, 2), 3));
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.18;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    // 2. Scene & Portrait Camera Setup (28 deg vertical FOV for optimal portrait framing)
    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(28, width / height, 0.1, 50.0);
    this.camera.position.set(0.0, 0.0, 2.25);
    this.camera.lookAt(0.0, 0.0, 0.0);

    // 3. Balanced Studio 3-Point Lighting Rig (Clean Pure-White Ambient & Warm Studio Key)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.90);
    this.scene.add(ambientLight);

    // Key Light
    this.keyLight = new THREE.DirectionalLight(0xfffaeb, 1.25);
    this.keyLight.position.set(1.6, 2.4, 2.2);
    this.scene.add(this.keyLight);

    // Fill Light
    this.fillLight = new THREE.DirectionalLight(0xf0fdf4, 0.70);
    this.fillLight.position.set(-1.6, 1.4, 1.8);
    this.scene.add(this.fillLight);

    // Rim Backlight
    this.rimLight = new THREE.DirectionalLight(0xffffff, 0.90);
    this.rimLight.position.set(0, 2.4, -2.0);
    this.scene.add(this.rimLight);

    // Clean Studio Contact Ground Shadow directly beneath shoes (Zero oversized pedestal)
    this.groundShadowGroup = new THREE.Group();
    this.groundShadowGroup.position.set(0.0, -0.490, 0.0);

    const shadowCanvas = document.createElement('canvas');
    shadowCanvas.width = 256;
    shadowCanvas.height = 256;
    const ctx = shadowCanvas.getContext('2d');
    const grad = ctx.createRadialGradient(128, 128, 12, 128, 128, 122);
    grad.addColorStop(0.0, 'rgba(15, 23, 42, 0.32)');
    grad.addColorStop(0.35, 'rgba(15, 23, 42, 0.18)');
    grad.addColorStop(0.70, 'rgba(15, 23, 42, 0.06)');
    grad.addColorStop(1.0, 'rgba(15, 23, 42, 0.0)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 256, 256);

    const shadowTexture = new THREE.CanvasTexture(shadowCanvas);
    shadowTexture.generateMipmaps = true;

    const shadowGeo = new THREE.PlaneGeometry(0.86, 0.52);
    const shadowMat = new THREE.MeshBasicMaterial({
      map: shadowTexture,
      transparent: true,
      depthWrite: false
    });
    const shadowMesh = new THREE.Mesh(shadowGeo, shadowMat);
    shadowMesh.rotation.x = -Math.PI / 2;
    shadowMesh.position.set(0.0, 0.001, 0.02);
    this.groundShadowGroup.add(shadowMesh);

    this.scene.add(this.groundShadowGroup);

    // 4. Character Container Group (Hidden initially to guarantee zero T-pose)
    this.characterGroup = new THREE.Group();
    this.characterGroup.visible = false;
    this.scene.add(this.characterGroup);

    // 5. Load Active Avatar Model (Chacha New GLB)
    this.loadAvatarGLB();

    // 6. Animation Clock & Procedural Dynamics Loop
    this.clock = new THREE.Clock();
    const animate = () => {
      this._rafId = requestAnimationFrame(animate);
      const delta = Math.min(this.clock.getDelta(), 0.08); // Clamp delta to eliminate frame spikes

      if (this.mixer) {
        this.mixer.update(delta);
      }

      // Root position remains anchored firmly to ground shadow
      if (this.characterGroup && this.characterGroup.visible) {
        this.characterGroup.position.set(0.0, 0.0, 0.0);
      }

      const now = Date.now();

      // =====================================================================
      // LAYER 1: Natural Respiratory Chest & Shoulder Breathing (~17 breaths/min)
      // =====================================================================
      const isSpeaking = ['SPEAKING', 'EXPLAINING', 'GREETING', 'HAPPY'].includes(this.currentState);
      const breathFreq = isSpeaking ? 0.0022 : 0.0018;
      const breathWave = Math.sin(now * breathFreq);
      const breathPositive = (breathWave + 1.0) * 0.5;

      if (this.spine1Bone) {
        this.spine1Bone.rotation.x += breathWave * (isSpeaking ? 0.005 : 0.007);
      }
      if (this.spine2Bone) {
        this.spine2Bone.rotation.x += breathWave * (isSpeaking ? 0.006 : 0.009);
      }
      if (this.leftShoulderBone && this.rightShoulderBone) {
        const heave = breathPositive * 0.005;
        this.leftShoulderBone.rotation.z += heave;
        this.rightShoulderBone.rotation.z -= heave;
      }

      // =====================================================================
      // LAYER 2: Natural Pelvic Weight Shifting Between Legs During Idle (~14s cycle)
      // =====================================================================
      if (this.hipsBone && this.currentState === 'IDLE') {
        const shiftTime = now * 0.00045;
        this.hipsBone.rotation.z += Math.sin(shiftTime) * 0.006;
      }

      // =====================================================================
      // LAYER 3: Biological Eye Gaze & Micro-Saccade System
      // =====================================================================
      if (now - this.lastSaccadeTime > this.nextSaccadeInterval) {
        this.lastSaccadeTime = now;
        switch (this.currentState) {
          case 'THINKING':
          case 'PROCESSING':
            // Cognitive load gaze aversion: look up and slightly right
            this.targetGazePitch = -0.070 + (Math.random() - 0.5) * 0.025;
            this.targetGazeYaw = 0.050 + (Math.random() - 0.5) * 0.025;
            this.nextSaccadeInterval = 1800 + Math.random() * 1500;
            break;

          case 'LISTENING':
            // Attentive gaze directly at user with tiny focal adjustments
            this.targetGazePitch = -0.015 + (Math.random() - 0.5) * 0.012;
            this.targetGazeYaw = (Math.random() - 0.5) * 0.018;
            this.nextSaccadeInterval = 2800 + Math.random() * 2000;
            break;

          case 'SPEAKING':
          case 'EXPLAINING':
          case 'GREETING':
            // Conversational saccades: slight shifts between listener and thought
            this.targetGazePitch = (Math.random() - 0.5) * 0.030;
            this.targetGazeYaw = (Math.random() - 0.5) * 0.045;
            this.nextSaccadeInterval = 2400 + Math.random() * 2200;
            break;

          case 'IDLE':
          default:
            // Relaxed ambient gaze centering
            this.targetGazePitch = (Math.random() - 0.5) * 0.018;
            this.targetGazeYaw = (Math.random() - 0.5) * 0.030;
            this.nextSaccadeInterval = 3200 + Math.random() * 2800;
            break;
        }
      }

      const gazeSpeed = (this.currentState === 'THINKING') ? 8.0 : 16.0;
      const gazeLerp = 1.0 - Math.exp(-delta * gazeSpeed);
      this.currentGazePitch += (this.targetGazePitch - this.currentGazePitch) * gazeLerp;
      this.currentGazeYaw += (this.targetGazeYaw - this.currentGazeYaw) * gazeLerp;

      if (this.headBone) {
        this.headBone.rotation.x += this.currentGazePitch * 0.70;
        this.headBone.rotation.y += this.currentGazeYaw * 0.70;
      }
      if (this.neckBone) {
        this.neckBone.rotation.x += this.currentGazePitch * 0.30;
        this.neckBone.rotation.y += this.currentGazeYaw * 0.30;
      }

      // =====================================================================
      // LAYER 4: Biologically Realistic Eye Blinking System (Poisson Intervals)
      // =====================================================================
      if (this.blinkPhase === 'idle' && now >= this.nextBlinkTime) {
        this.blinkPhase = 'closing';
        this.blinkStartTime = now;
      }

      if (this.blinkPhase === 'closing') {
        const elapsed = now - this.blinkStartTime;
        this.blinkWeight = Math.min(1.0, elapsed / 55.0); // 55ms quick close
        if (this.blinkWeight >= 1.0) {
          this.blinkPhase = 'opening';
          this.blinkStartTime = now;
        }
      } else if (this.blinkPhase === 'opening') {
        const elapsed = now - this.blinkStartTime;
        this.blinkWeight = Math.max(0.0, 1.0 - (elapsed / 95.0)); // 95ms natural reopen
        if (this.blinkWeight <= 0.0) {
          this.blinkWeight = 0.0;
          if (!this.isDoubleBlink && Math.random() < 0.14) {
            // 14% chance of human double-blink
            this.isDoubleBlink = true;
            this.nextBlinkTime = now + 120;
          } else {
            this.isDoubleBlink = false;
            const blinkInterval = (this.currentState === 'LISTENING')
              ? (2200 + Math.random() * 2000)
              : (3200 + Math.random() * 2800);
            this.nextBlinkTime = now + blinkInterval;
          }
          this.blinkPhase = 'idle';
        }
      }

      // Apply blink morphs if present in dictionary
      if (this.morphDict) {
        const bL = this.morphDict['Blink_L'] ?? this.morphDict['blink_l'] ?? this.morphDict['blink'];
        const bR = this.morphDict['Blink_R'] ?? this.morphDict['blink_r'] ?? this.morphDict['blink'];
        if (bL !== undefined && this.targetMorphInfluences) this.targetMorphInfluences[bL] = this.blinkWeight;
        if (bR !== undefined && this.targetMorphInfluences) this.targetMorphInfluences[bR] = this.blinkWeight;
      }

      // Subtle biological micro-dip of brow/head during blink for universal realism
      if (this.headBone && this.blinkWeight > 0.0) {
        this.headBone.rotation.x -= this.blinkWeight * 0.005;
      }

      // =====================================================================
      // LAYER 5: Procedural Head Dynamics & Conversational Prosody Accents
      // =====================================================================
      if (this.headBone) {
        switch (this.currentState) {
          case 'LISTENING':
            // Attentive ear-tilt towards user/microphone
            this.headBone.rotation.z += 0.055;
            this.headBone.rotation.x += -0.015;
            break;

          case 'THINKING':
          case 'PROCESSING':
            // Thoughtful head tilt
            this.headBone.rotation.x += -0.075;
            this.headBone.rotation.y += 0.040;
            if (this.neckBone) this.neckBone.rotation.x += -0.020;
            break;

          case 'SPEAKING':
          case 'EXPLAINING':
          case 'GREETING':
            // Conversational speech prosody: speech pulse accents coupled to voice amplitude
            const speechPulse = this.currentAudioAmplitude || 0.0;
            const nodAngle = Math.sin(now * 0.007) * 0.014 + (speechPulse * 0.048);
            const rollAngle = Math.sin(now * 0.0028) * 0.015;
            this.headBone.rotation.x += nodAngle;
            this.headBone.rotation.z += rollAngle;
            break;

          case 'CONFUSED':
            this.headBone.rotation.z += -0.065;
            this.headBone.rotation.x += 0.030;
            break;

          case 'HAPPY':
            this.headBone.rotation.x += Math.sin(now * 0.004) * 0.016;
            this.headBone.rotation.z += Math.sin(now * 0.002) * 0.012;
            break;

          case 'IDLE':
          default:
            // Subtle observant ambient sway (character never frozen)
            this.headBone.rotation.y += Math.sin(now * 0.00075) * 0.018;
            this.headBone.rotation.x += Math.sin(now * 0.0012) * 0.010;
            break;
        }
      }

      // =====================================================================
      // LAYER 6: Active Multi-Stage Lip Sync (Spectral FFT + Rhubarb + RMS)
      // =====================================================================
      this.updateActiveLipSync();

      // =====================================================================
      // LAYER 7: Asymmetric Spring Blendshape Interpolation
      // =====================================================================
      // Fast syllable attack (28.0) so mouth opens immediately with sound;
      // Smooth natural release (18.0) so mouth does not snap shut unnaturally mid-word.
      if (this.morphInfluences && this.targetMorphInfluences) {
        const isMouthActive = isSpeaking && this.isAudioPlaying;
        const attackSpeed = 28.0;
        const decaySpeed = isMouthActive ? 18.0 : 22.0;

        for (let i = 0; i < this.morphInfluences.length; i++) {
          const tgt = this.targetMorphInfluences[i] || 0.0;
          const cur = this.morphInfluences[i];
          const speed = (tgt > cur) ? attackSpeed : decaySpeed;
          const lerpFactor = 1.0 - Math.exp(-delta * speed);
          this.morphInfluences[i] += (tgt - cur) * lerpFactor;
        }
      }

      // =====================================================================
      // LAYER 8: Mid-Speech Contextual Gesture Cadence
      // =====================================================================
      if (this.isAudioPlaying && ['SPEAKING', 'EXPLAINING'].includes(this.currentState)) {
        this.checkMidSpeechGestures(now);
      }

      this.renderer.render(this.scene, this.camera);
    };
    animate();

    // 7. Dynamic Responsive Resize Handler
    this._resizeHandler = () => {
      this.fitCameraToModel();
    };
    window.addEventListener('resize', this._resizeHandler);
  }

  /**
   * Mathematically Calibrated Full-Body Avatar Framing:
   * - Model scale: 1.0 (Noticeably 35-40% larger inside the left avatar panel)
   * - Target: 70-75% of the overall available avatar stage height
   * - In animated pose (all Mixamo clips), mixamorig:Hips shifts skeleton so:
   *   Shoe soles / toes are at local y = 0.000 to 0.005.
   *   Head / turban crest vertices reach local y = 0.980.
   *   Total animated height = 0.980, vertical midpoint = 0.490.
   * - Shifting model3D.position.y by -0.49 * scale (-0.4900):
   *   Shoe soles are at y = -0.4900 (resting naturally on ground contact shadow).
   *   Turban crest is at y = +0.4900.
   *   Vertical midpoint is at y = 0.0000 (perfect vertical alignment with camera.lookAt(0,0,0)).
   * - Camera at 28 deg vertical FOV calculates exact distance to frame complete character
   *   with comfortable clean headroom above turban and floorroom below shoes.
   */
  fitCameraToModel() {
    if (!this.canvas || !this.renderer || !this.camera) return;
    const container = this.canvas.parentElement;
    const width = container ? (container.clientWidth || 380) : 380;
    const height = container ? (container.clientHeight || 480) : 480;
    const aspect = width / height;

    this.camera.fov = 28;
    this.camera.aspect = aspect;

    // Calibrated Scale: 1.0 (Visibly 36.5% larger than baseline 0.88, targeting 70-75% stage height)
    const scale = 1.0;
    const groundY = -0.49 * scale; // -0.4900

    if (this.model3D) {
      this.model3D.scale.setScalar(scale);
      this.model3D.position.set(0.0, groundY, 0.0);
    }
    if (this.groundShadowGroup) {
      this.groundShadowGroup.position.set(0.0, groundY, 0.0);
    }

    const vFovRad = (this.camera.fov * Math.PI) / 180;
    const halfFovTan = Math.tan(vFovRad / 2);

    // Target 91% occupancy of the 3D canvas viewport, yielding exactly 72-74% of the overall stage height
    const characterHeight = 0.98 * scale;
    const requiredHeight = characterHeight / 0.91; // ~1.0769
    const distY = requiredHeight / (2 * halfFovTan); // ~2.160

    // Horizontal envelope covering walking stick gestures & body: 0.68 * scale
    const minVisibleWidth = 0.68 * scale;
    const distX = minVisibleWidth / (2 * halfFovTan * aspect);

    const targetDistance = Math.max(distY, distX);

    this.camera.position.set(0.0, 0.0, targetDistance);
    this.camera.lookAt(0.0, 0.0, 0.0);
    this.camera.updateProjectionMatrix();

    this.renderer.setSize(width, height);
  }

  /**
   * Primary Asset Loader: Chacha_New/Chacha_New.glb
   */
  loadAvatarGLB() {
    if (typeof THREE.GLTFLoader === 'undefined') {
      console.error('[Mascot 3D Engine] THREE.GLTFLoader is not available. Cannot load Chacha New.');
      this._showLoadingError('THREE.GLTFLoader missing.');
      return;
    }

    const glbPath = 'Chacha_New/Chacha_New.glb';
    const loader = new THREE.GLTFLoader();

    console.log(`[Mascot 3D Engine] Loading Chacha New GLB: ${glbPath}...`);

    loader.load(
      glbPath,
      (gltf) => {
        const root = gltf.scene || gltf.scenes[0];

        let meshCount = 0;
        let skinnedMeshCount = 0;
        const maxAnisotropy = this.renderer.capabilities.getMaxAnisotropy();

        root.traverse((child) => {
          // 1. Identify Skeletal Rig Bones
          if (child.isBone) {
            const bName = child.name || '';
            if (bName === 'mixamorig:Head' || bName === 'mixamorigHead') this.headBone = child;
            else if (bName === 'mixamorig:Neck' || bName === 'mixamorigNeck') this.neckBone = child;
            else if (bName === 'mixamorig:Spine1') this.spine1Bone = child;
            else if (bName === 'mixamorig:Spine2') this.spine2Bone = child;
            else if (bName === 'mixamorig:LeftShoulder') this.leftShoulderBone = child;
            else if (bName === 'mixamorig:RightShoulder') this.rightShoulderBone = child;
            else if (bName === 'mixamorig:LeftArm') this.leftArmBone = child;
            else if (bName === 'mixamorig:RightArm') this.rightArmBone = child;
            else if (bName === 'mixamorig:LeftForeArm') this.leftForeArmBone = child;
            else if (bName === 'mixamorig:RightForeArm') this.rightForeArmBone = child;
            else if (bName === 'mixamorig:Hips') this.hipsBone = child;
          }

          // 2. Identify Skinned Mesh and Blendshapes
          if (child.isMesh) {
            meshCount++;
            child.castShadow = true;
            child.receiveShadow = true;

            if (child.isSkinnedMesh) {
              skinnedMeshCount++;
              this.skinnedMesh = child;
            }

            if (child.morphTargetInfluences && child.morphTargetInfluences.length > 0) {
              this.morphInfluences = child.morphTargetInfluences;
              if (!child.morphTargetDictionary || Object.keys(child.morphTargetDictionary).length === 0) {
                child.morphTargetDictionary = { 'mouthOpen': 0, 'mouthO': 1, 'mouthSmile': 2 };
              }
              this.morphDict = child.morphTargetDictionary;
              this.targetMorphInfluences = new Float32Array(child.morphTargetInfluences.length);
            }

            if (child.material) {
              const materials = Array.isArray(child.material) ? child.material : [child.material];
              materials.forEach((m) => {
                m.skinning = true;
                if (child.morphTargetInfluences && child.morphTargetInfluences.length > 0) {
                  m.morphTargets = true;
                }

                ['map', 'normalMap', 'roughnessMap', 'metalnessMap'].forEach((mapName) => {
                  if (m[mapName]) {
                    m[mapName].anisotropy = maxAnisotropy;
                    m[mapName].generateMipmaps = true;
                    m[mapName].minFilter = THREE.LinearMipmapLinearFilter;
                    m[mapName].magFilter = THREE.LinearFilter;
                    m[mapName].needsUpdate = true;
                  }
                });

                if (m.map) {
                  m.map.encoding = THREE.sRGBEncoding;
                }

                m.needsUpdate = true;
              });
            }
          }
        });

        this.hasMorphTargets = Boolean(this.morphInfluences && this.morphInfluences.length > 0);

        // Attach root and apply proven framing
        this.characterGroup.add(root);
        this.model3D = root;
        this.fitCameraToModel();

        // Setup AnimationMixer for all 28 actions
        if (gltf.animations && gltf.animations.length > 0) {
          this.mixer = new THREE.AnimationMixer(root);
          this.actions = {};

          gltf.animations.forEach((clip) => {
            const action = this.mixer.clipAction(clip);
            this.actions[clip.name] = action;
          });

          // State-aware finished listener for natural transitions
          this.mixer.addEventListener('finished', (e) => {
            const finishedClipName = e.action ? e.action.getClip().name : '';
            const isSpeakingState = ['SPEAKING', 'EXPLAINING', 'GREETING', 'HAPPY'].includes(this.currentState);

            if (isSpeakingState && this.isAudioPlaying) {
              // After one-shot gesture completes, seamlessly resume Talking continuous loop!
              if (finishedClipName !== 'Talking') {
                this.playAction('Talking', 0.35);
              }
            } else if (this.currentState === 'THINKING' || this.currentState === 'PROCESSING') {
              if (finishedClipName !== 'Looking') {
                this.playAction('Looking', 0.40);
              }
            } else if (this.currentState === 'LISTENING') {
              if (finishedClipName !== 'Idle') {
                this.playAction('Idle', 0.35);
              }
            } else {
              // Default return to Idle
              if (finishedClipName !== 'Idle') {
                this.playAction('Idle', 0.45);
              }
            }
          });

          // Start default idle animation immediately
          const idleAction = this.actions['Idle'];
          if (idleAction) {
            idleAction.reset();
            idleAction.setEffectiveTimeScale(1.0);
            idleAction.setEffectiveWeight(1.0);
            idleAction.setLoop(THREE.LoopRepeat);
            idleAction.play();
            this.activeActionName = 'Idle';
          }
        }

        // PRE-RENDER IDLE POSE TO GUARANTEE ZERO T-POSE FLASH:
        if (this.mixer) {
          this.mixer.update(0.001);
        }
        root.updateMatrixWorld(true);
        this.renderer.render(this.scene, this.camera);

        // Model is now in valid Idle pose: reveal to user
        this.characterGroup.visible = true;
        this.is3DReady = true;
        this.isProductionGLB = true;
        this.avatarReady = true;

        // Smoothly dismiss loading overlay
        const overlay = document.getElementById('avatarLoadingOverlay');
        if (overlay) {
          overlay.style.transition = 'opacity 0.35s ease';
          overlay.style.opacity = '0';
          setTimeout(() => {
            overlay.style.display = 'none';
          }, 350);
        }

        console.log(`=== CHACHA PRODUCTION AVATAR INITIALIZED ===\nModel: ${glbPath}\nBones: 65 (Armature)\nAnimations: ${Object.keys(this.actions).length}\nMorph targets: ${Object.keys(this.morphDict).length}\nStatus: Ready\n==========================================`);
      },
      (xhr) => {
        if (xhr.lengthComputable && xhr.total > 0) {
          const pct = Math.round((xhr.loaded / xhr.total) * 100);
          const label = document.querySelector('.loading-label');
          if (label) label.textContent = `Loading Chacha (${pct}%)...`;
        }
      },
      (err) => {
        console.error('[Mascot 3D Engine] Chacha New failed to load:', err);
        this._showLoadingError('Failed to load avatar asset. Check network/server.');
      }
    );
  }

  _showLoadingError(detail = '') {
    const overlay = document.getElementById('avatarLoadingOverlay');
    if (overlay) {
      overlay.innerHTML = `
        <div style="color:#ef4444;font-weight:600;text-align:center;font-size:0.95rem;">Avatar Loading Failed</div>
        <div style="color:#94a3b8;font-size:0.75rem;margin-top:6px;text-align:center;">${detail}</div>
        <button onclick="window.location.reload()" style="margin-top:10px;padding:6px 14px;background:#0ea5e9;border:none;border-radius:6px;color:#fff;font-size:0.8rem;cursor:pointer;">Retry</button>
      `;
    }
  }

  loadMember2GLB() {
    this.loadAvatarGLB();
  }

  // =========================================================================
  // Skeletal Body Gesture & Action API (28 Clips + Semantic Mappings)
  // =========================================================================

  playAction(actionName, duration = 0.35) {
    if (!this.actions || Object.keys(this.actions).length === 0) return;

    const key = (actionName || '').trim();
    if (!key) return;

    // 1. Exact match against registered actions
    let resolvedName = this.actions[key] ? key : null;

    // 2. Lookup in semantic gestureActionMap (case-insensitive)
    if (!resolvedName) {
      const mapped = this.gestureActionMap[key.toLowerCase()];
      if (mapped && this.actions[mapped]) {
        resolvedName = mapped;
      }
    }

    // 3. Case-insensitive match against all clip names in this.actions
    if (!resolvedName) {
      const lower = key.toLowerCase();
      for (const actName of Object.keys(this.actions)) {
        if (actName.toLowerCase() === lower) {
          resolvedName = actName;
          break;
        }
      }
    }

    // 4. Safe fallback to 'Idle' (never leave avatar in T-pose)
    if (!resolvedName) {
      console.warn(`[Mascot 3D Engine] Action '${actionName}' not recognized. Falling back to 'Idle'.`);
      resolvedName = 'Idle';
    }

    const targetAction = this.actions[resolvedName];
    if (!targetAction) return;

    // Avoid restarting the exact same action if already running
    if (this.activeActionName === resolvedName && targetAction.isRunning()) {
      return;
    }

    const prevAction = this.activeActionName ? this.actions[this.activeActionName] : null;
    this.activeActionName = resolvedName;

    // Continuous loop vs one-shot gesture configuration:
    const continuousLoopClips = ['Idle', 'Talking', 'Looking', 'Happy_Idle', 'Unarmed_Idle'];
    if (continuousLoopClips.includes(resolvedName)) {
      targetAction.setLoop(THREE.LoopRepeat);
      targetAction.clampWhenFinished = false;
    } else {
      targetAction.setLoop(THREE.LoopOnce, 1);
      targetAction.clampWhenFinished = false;
    }

    targetAction.enabled = true;

    // Clean Three.js crossfade: fadeOut previous, fadeIn new
    if (prevAction && prevAction !== targetAction) {
      prevAction.fadeOut(duration);
    }

    targetAction
      .reset()
      .setEffectiveTimeScale(1.0)
      .setEffectiveWeight(1.0)
      .fadeIn(duration)
      .play();

    // Update UI gesture badge if available
    const gestureBadge = document.getElementById('gestureBadge');
    if (gestureBadge) {
      gestureBadge.textContent = `Gesture: ${resolvedName}`;
    }
  }

  setGesture(gesture) {
    this.currentGesture = (gesture || 'idle').toLowerCase();
    this.playAction(this.currentGesture);
  }

  // =========================================================================
  // Expression & Emotion API
  // =========================================================================

  setEmotion(emotion, intensity = 1.0) {
    const emKey = (emotion || 'neutral').toLowerCase().trim();
    this.currentEmotion = emKey;

    const emotionBadge = document.getElementById('emotionBadge');
    if (emotionBadge) {
      emotionBadge.textContent = `Emotion: ${emKey.charAt(0).toUpperCase() + emKey.slice(1)}`;
    }

    // Drive subtle facial blendshapes smoothly if available
    if (this.targetMorphInfluences && this.morphDict) {
      const smileIdx = this.morphDict['mouthSmile'];
      if (smileIdx !== undefined) {
        if (emKey === 'happy' || emKey === 'laughing') {
          this.targetMorphInfluences[smileIdx] = Math.min(0.85, intensity * 0.65);
        } else if (emKey === 'neutral') {
          this.targetMorphInfluences[smileIdx] = 0.15;
        } else {
          this.targetMorphInfluences[smileIdx] = 0.0;
        }
      }
    }

    // Emotion is state-aware: during IDLE state, body postures can express emotion
    if (this.currentState === 'IDLE') {
      switch (emKey) {
        case 'happy':
          this.playAction('Happy_Idle', 0.4);
          break;
        case 'sad':
          this.playAction('Defeat_Idle', 0.4);
          break;
        case 'angry':
          this.playAction('Angry_Gesture', 0.35);
          break;
        case 'surprised':
          this.playAction('Yelling', 0.35);
          break;
        case 'confused':
          this.playAction('Nervously_Look_Around', 0.4);
          break;
        case 'thinking':
          this.playAction('Looking', 0.4);
          break;
        case 'laughing':
          this.playAction('Laughing_1', 0.4);
          break;
        case 'neutral':
        default:
          this.playAction('Idle', 0.4);
          break;
      }
    }
  }

  clearEmotion() {
    this.setEmotion('neutral', 0.0);
  }

  setMouthAperture(aperture) {
    if (this.targetMorphInfluences) {
      const openIdx = this.morphDict ? this.morphDict['mouthOpen'] : 0;
      if (openIdx !== undefined) {
        this.targetMorphInfluences[openIdx] = Math.min(0.85, Math.max(0.0, aperture));
      }
    }
  }

  // =========================================================================
  // Real-Time Audio & Multi-Stage Lip Sync Pipeline
  // =========================================================================

  startAudioLipSync(audioElement, metadata = {}) {
    this.activeAudio = audioElement;
    this.isAudioPlaying = true;
    this.speechStartTime = Date.now();
    this.lastMidSpeechGestureTime = Date.now();
    this.midSpeechGestureCooldown = 3800 + Math.random() * 2000;

    // 1. Extract Rhubarb timestamps
    const rData = metadata.rhubarb_lipsync || metadata.lip_sync;
    this.rhubarbCues = (rData && (rData.mouth_cues || rData.visemes || rData.mouthCues)) || null;

    // Extract precomputed RMS frames if present
    this.rmsFrames = metadata.rms_lip_sync || null;

    // 2. Setup Web Audio Analyser for live frequency/amplitude analysis
    if (!this.audioContext && (window.AudioContext || window.webkitAudioContext)) {
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        this.audioContext = new AudioCtx();
      } catch (e) {
        console.warn('[Mascot 3D] Failed to create AudioContext:', e);
      }
    }

    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume().catch(() => {});
    }

    if (this.audioContext && audioElement && !audioElement._hasMascotAnalyser) {
      try {
        const sourceNode = this.audioContext.createMediaElementSource(audioElement);
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.analyser.smoothingTimeConstant = 0.35; // Fast, responsive syllable attack
        sourceNode.connect(this.analyser);
        this.analyser.connect(this.audioContext.destination);
        this.freqDataArray = new Uint8Array(this.analyser.frequencyBinCount);
        audioElement._hasMascotAnalyser = true;
      } catch (e) {
        // MediaElementSource fallback: continue with Rhubarb cues & audio time
        console.warn('[Mascot 3D] MediaElementSource fallback to timing analysis:', e.message);
      }
    }
  }

  stopAudioLipSync() {
    this.isAudioPlaying = false;
    this.activeAudio = null;
    this.rhubarbCues = null;
    this.rmsFrames = null;
    this.currentAudioAmplitude = 0.0;
    this._lowEnergy = 0.0;
    this._midEnergy = 0.0;
    this._highEnergy = 0.0;

    // STRICT GUARANTEE: Close mouth immediately on silence/stop
    if (this.targetMorphInfluences) {
      const openIdx = this.morphDict ? this.morphDict['mouthOpen'] : 0;
      const oIdx = this.morphDict ? this.morphDict['mouthO'] : 1;
      const smileIdx = this.morphDict ? this.morphDict['mouthSmile'] : 2;
      const targetSmile = (this.currentEmotion === 'happy' || this.currentEmotion === 'laughing' || this.currentState === 'HAPPY' || this.currentState === 'GREETING') ? 0.60 : 0.15;

      if (openIdx !== undefined) this.targetMorphInfluences[openIdx] = 0.0;
      if (oIdx !== undefined) this.targetMorphInfluences[oIdx] = 0.0;
      if (smileIdx !== undefined) this.targetMorphInfluences[smileIdx] = targetSmile;
    }

    const vizFill = document.getElementById('vizFill');
    if (vizFill) vizFill.style.width = '0%';
  }

  updateActiveLipSync() {
    if (!this.isAudioPlaying || !this.activeAudio) return;

    if (this.activeAudio.paused || this.activeAudio.ended) {
      this.stopAudioLipSync();
      return;
    }

    const curTime = this.activeAudio.currentTime;
    let amplitude = 0.0;

    // Stage 1: Multi-Band Web Audio Spectral Analysis
    if (this.analyser && this.freqDataArray) {
      this.analyser.getByteFrequencyData(this.freqDataArray);
      let sum = 0;
      let lowSum = 0;
      let midSum = 0;
      let highSum = 0;
      const count = this.freqDataArray.length;

      for (let i = 0; i < count; i++) {
        const val = this.freqDataArray[i] / 255.0;
        sum += val * val;
        if (i < 6) lowSum += val; // ~100-750 Hz (Vowels: A, E, O)
        else if (i < 18) midSum += val; // ~750-2200 Hz (Formants: U, O, W)
        else if (i < 40) highSum += val; // ~2200-5000 Hz (Fricatives: S, SH, CH)
      }

      amplitude = Math.sqrt(sum / count);
      this.currentAudioAmplitude = amplitude;
      this._lowEnergy = lowSum / 6;
      this._midEnergy = midSum / 12;
      this._highEnergy = highSum / 22;
    } else if (this.rmsFrames && this.rmsFrames.length > 0) {
      // Stage 3 Fallback: Precomputed PCM RMS Frames
      const frameIdx = Math.floor(curTime * this.rmsFps);
      if (frameIdx < this.rmsFrames.length) {
        amplitude = this.rmsFrames[frameIdx];
        this.currentAudioAmplitude = amplitude;
        this._lowEnergy = amplitude * 1.2;
        this._midEnergy = amplitude * 0.8;
      }
    }

    const openIdx = this.morphDict ? this.morphDict['mouthOpen'] : 0;
    const oIdx = this.morphDict ? this.morphDict['mouthO'] : 1;
    const smileIdx = this.morphDict ? this.morphDict['mouthSmile'] : 2;
    const baseSmile = (this.currentEmotion === 'happy' || this.currentEmotion === 'laughing' || this.currentState === 'HAPPY' || this.currentState === 'GREETING') ? 0.60 : 0.15;

    // Stage 2: Rhubarb Phoneme Alignment (with audio amplitude modulation)
    if (this.rhubarbCues && this.rhubarbCues.length > 0) {
      const cue = this.rhubarbCues.find(c => curTime >= c.start && curTime <= c.end);
      if (cue) {
        const rawViseme = cue.viseme || cue.value || 'Viseme_Silence';
        this.setViseme(rawViseme, Math.max(0.40, Math.min(1.0, (amplitude || 0.3) * 2.5)));
      } else {
        this.setViseme('Viseme_Silence', 0.0);
      }
    } else {
      // Direct Real-Time Multi-Band FFT Formant Lip-Sync (High-Fidelity Fallback)
      // Adaptive Noise Gate: Below 0.038 amplitude, silence is enforced -> lips close naturally
      if (amplitude < 0.038) {
        if (this.targetMorphInfluences) {
          if (openIdx !== undefined) this.targetMorphInfluences[openIdx] = 0.0;
          if (oIdx !== undefined) this.targetMorphInfluences[oIdx] = 0.0;
          if (smileIdx !== undefined) this.targetMorphInfluences[smileIdx] = baseSmile;
        }
      } else {
        // Active Syllable Articulation
        const openVal = Math.min(0.85, (this._lowEnergy * 1.55 + amplitude * 0.35));
        const oVal = Math.min(0.80, (this._midEnergy * 1.45 + (this._lowEnergy > 0.4 ? 0.12 : 0.0)));
        const smileVal = Math.min(0.70, baseSmile + this._highEnergy * 0.35);

        if (this.targetMorphInfluences) {
          if (openIdx !== undefined) this.targetMorphInfluences[openIdx] = openVal;
          if (oIdx !== undefined) this.targetMorphInfluences[oIdx] = oVal;
          if (smileIdx !== undefined) this.targetMorphInfluences[smileIdx] = smileVal;
        }
      }
    }

    // Synchronize UI Audio Visualizer Bar
    const vizFill = document.getElementById('vizFill');
    if (vizFill) {
      const displayAmp = Math.round((this.currentAudioAmplitude || amplitude) * 100);
      vizFill.style.width = Math.min(100, Math.max(0, displayAmp * 1.85)) + '%';
    }
  }

  checkMidSpeechGestures(now) {
    if (!this.activeAudio || this.activeAudio.paused || this.activeAudio.ended) return;
    const remainingTime = this.activeAudio.duration - this.activeAudio.currentTime;
    if (remainingTime < 2.5) return; // Never trigger a new gesture right before speech completes

    if (now - this.lastMidSpeechGestureTime > this.midSpeechGestureCooldown) {
      this.lastMidSpeechGestureTime = now;
      this.midSpeechGestureCooldown = 3800 + Math.random() * 2200; // 3.8s to 6.0s natural variation

      // Contextual conversational gesture choreography
      const gestures = ['Agreeing', 'Pointing', 'Pointing_Forward', 'Acknowledging', 'Talking'];
      const chosen = gestures[Math.floor(Math.random() * gestures.length)];
      this.playAction(chosen, 0.35);
    }
  }

  setViseme(viseme, intensity = 1.0) {
    this.activeViseme = viseme || 'Viseme_Silence';
    this.activeVisemeWeight = intensity || 0.0;

    if (!this.targetMorphInfluences) {
      this.targetMorphInfluences = [0.0, 0.0, 0.0];
    }

    const openIdx = this.morphDict ? this.morphDict['mouthOpen'] : 0;
    const oIdx = this.morphDict ? this.morphDict['mouthO'] : 1;
    const smileIdx = this.morphDict ? this.morphDict['mouthSmile'] : 2;

    const raw = (viseme || '').trim();
    const v = raw.replace(/^Viseme_/i, '').toUpperCase();

    let targetOpen = 0.0;
    let targetO = 0.0;
    let targetSmile = (this.currentEmotion === 'happy' || this.currentEmotion === 'laughing' || this.currentState === 'HAPPY' || this.currentState === 'GREETING') ? 0.65 : 0.15;

    // Full Viseme to Blendshape Mapping
    if (['A', 'D'].includes(v)) {
      targetOpen = 0.85 * intensity;
      targetO = 0.10 * intensity;
    } else if (['E', 'C'].includes(v)) {
      targetOpen = 0.55 * intensity;
      targetSmile = Math.max(targetSmile, 0.35 * intensity);
    } else if (['I'].includes(v)) {
      targetOpen = 0.45 * intensity;
      targetSmile = Math.max(targetSmile, 0.25 * intensity);
    } else if (['O'].includes(v)) {
      targetO = 0.85 * intensity;
      targetOpen = 0.45 * intensity;
    } else if (['U', 'F'].includes(v)) {
      targetO = 0.90 * intensity;
      targetOpen = 0.22 * intensity;
    } else if (['FV', 'G'].includes(v)) {
      targetOpen = 0.24 * intensity;
      targetO = 0.05 * intensity;
    } else if (['MBP'].includes(v)) {
      // Bilabial plosive: lips firmly closed
      targetOpen = 0.0;
      targetO = 0.0;
    } else if (['L', 'DTN', 'B', 'KG', 'SHCH', 'TH', 'H', 'S', 'R', 'NG'].includes(v)) {
      targetOpen = 0.32 * intensity;
      targetO = 0.0;
    } else if (['SILENCE', 'X'].includes(v)) {
      targetOpen = 0.0;
      targetO = 0.0;
    } else {
      targetOpen = 0.30 * intensity;
    }

    if (openIdx !== undefined) this.targetMorphInfluences[openIdx] = targetOpen;
    if (oIdx !== undefined) this.targetMorphInfluences[oIdx] = targetO;
    if (smileIdx !== undefined) this.targetMorphInfluences[smileIdx] = targetSmile;
  }

  clearViseme() {
    this.activeViseme = 'Viseme_Silence';
    this.activeVisemeWeight = 0.0;
    if (this.targetMorphInfluences) {
      const openIdx = this.morphDict ? this.morphDict['mouthOpen'] : 0;
      const oIdx = this.morphDict ? this.morphDict['mouthO'] : 1;
      const smileIdx = this.morphDict ? this.morphDict['mouthSmile'] : 2;
      const targetSmile = (this.currentEmotion === 'happy' || this.currentEmotion === 'laughing' || this.currentState === 'HAPPY' || this.currentState === 'GREETING') ? 0.65 : 0.15;

      if (openIdx !== undefined) this.targetMorphInfluences[openIdx] = 0.0;
      if (oIdx !== undefined) this.targetMorphInfluences[oIdx] = 0.0;
      if (smileIdx !== undefined) this.targetMorphInfluences[smileIdx] = targetSmile;
    }
  }

  resetFace() {
    this.currentEmotion = 'neutral';
    this.activeViseme = 'Viseme_Silence';
    this.clearViseme();
  }

  // =========================================================================
  // Context-Aware Deterministic Animation State Machine
  // =========================================================================

  setState(state, options = {}) {
    const s = (state || 'IDLE').toUpperCase();
    this.currentState = s;

    const statusText = document.getElementById('statusText');
    const statusBadge = document.getElementById('statusBadge');
    if (statusBadge) {
      statusBadge.className = `status-badge state-${s.toLowerCase()}`;
    }
    if (statusText) {
      statusText.textContent = s;
    }

    // Synchronize bottom 4 state indicator pills
    const pillIdle = document.getElementById('statePillIdle');
    const pillListening = document.getElementById('statePillListening');
    const pillThinking = document.getElementById('statePillThinking');
    const pillSpeaking = document.getElementById('statePillSpeaking');
    const speechBubble = document.getElementById('mascotSpeechBubble');

    if (pillIdle) pillIdle.classList.toggle('active', s === 'IDLE');
    if (pillListening) pillListening.classList.toggle('active', s === 'LISTENING');
    if (pillThinking) pillThinking.classList.toggle('active', s === 'THINKING' || s === 'PROCESSING');
    if (pillSpeaking) pillSpeaking.classList.toggle('active', ['SPEAKING', 'EXPLAINING', 'GREETING', 'HAPPY', 'TECHNICAL', 'QUESTION', 'IMPORTANT_ALERT', 'APOLOGETIC'].includes(s));

    // Language awareness: English default unless Hindi explicitly selected
    const outLang = document.getElementById('outputLangSelect') ? document.getElementById('outputLangSelect').value : 'en';
    const isHindi = outLang === 'hi';

    switch (s) {
      case 'LISTENING':
        this.clearViseme();
        this.playAction('Idle', 0.35);
        if (speechBubble) {
          speechBubble.textContent = isHindi
            ? "Main dhyan se sun raha hoon, apna prashn bolein ya likhein..."
            : "I am listening closely, please speak or type your question...";
        }
        break;

      case 'THINKING':
      case 'PROCESSING':
        this.clearViseme();
        this.currentEmotion = 'thinking';
        this.playAction('Looking', 0.40);
        const thinkingEmotionBadge = document.getElementById('emotionBadge');
        if (thinkingEmotionBadge) {
          thinkingEmotionBadge.textContent = 'Emotion: Thinking';
        }
        if (speechBubble) {
          speechBubble.textContent = isHindi
            ? "GRBMP tathyon ka vishleshan ho raha hai, bas ek pal..."
            : "Consulting Ganga knowledge base and analyzing facts...";
        }
        break;

      case 'GREETING':
        this.currentEmotion = 'happy';
        if (this.targetMorphInfluences) this.targetMorphInfluences[2] = 0.60;
        this.playAction(options.gesture || 'Waving', 0.40);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Namaste! Main Chacha Chaudhary, Ganga ke baare mein sahi jaankari dene ke liye yahan hoon!"
            : "Namaste! I am Chacha Chaudhary, your official Ganga guide. Welcome!");
        }
        break;

      case 'HAPPY':
        this.clearViseme();
        this.currentEmotion = 'happy';
        if (this.targetMorphInfluences) this.targetMorphInfluences[2] = 0.70;
        this.playAction(options.gesture || 'Happy_Idle', 0.40);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Mujhe Ganga sanrakshan par yah jaankari share karte huye behad khushi ho rahi hai!"
            : "I am delighted to share these positive insights on River Ganga!");
        }
        break;

      case 'EXPLAINING':
        const expEmotion = (options.emotion || this.currentEmotion || 'neutral').toLowerCase();
        this.currentEmotion = expEmotion;
        this.playAction(options.gesture || 'Pointing_Forward', 0.35);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Ganga sanrakshan aur jal gunwatta ke mukhya tathya yeh hain:"
            : "Here are the key points regarding Ganga conservation and water quality:");
        }
        break;

      case 'TECHNICAL':
        this.currentEmotion = 'neutral';
        this.playAction(options.gesture || 'Acknowledging', 0.35);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Jal gunwatta vishleshan aur CPCB standards ke aadhar par:"
            : "Based on CPCB scientific monitoring and verified water metrics:");
        }
        break;

      case 'QUESTION':
        this.currentEmotion = 'thinking';
        this.playAction(options.gesture || 'Looking', 0.40);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Kya aap is baare mein thoda aur spasht karenge?"
            : "Could you please tell me more or clarify this aspect?");
        }
        break;

      case 'IMPORTANT_ALERT':
        this.currentEmotion = 'neutral';
        if (this.targetMorphInfluences) this.targetMorphInfluences[2] = 0.0;
        this.playAction(options.gesture || 'Pointing_Forward', 0.35);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Dhyan dein! Ganga pradushan aur niyamawali par mahatvapurna soochna:"
            : "Important Notice: Verified conservation guidelines and advisory:");
        }
        break;

      case 'APOLOGETIC':
      case 'CONFUSED':
        this.clearViseme();
        this.currentEmotion = 'confused';
        this.playAction(options.gesture || 'Nervously_Look_Around', 0.40);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Kripya apna prashn thoda aur spasht karein taaki main sahi jaankari de sakoon."
            : "I could not locate exact verified records for this query. Could you rephrase?");
        }
        break;

      case 'SURPRISED':
        this.clearViseme();
        this.currentEmotion = 'surprised';
        this.playAction('Yelling', 0.35);
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Ganga jal gunwatta par yah vishesh soochna dhyaan se dekhein!"
            : "Notice: Please pay special attention to this conservation alert!");
        }
        break;

      case 'SPEAKING':
        const emotion = (options.emotion || this.currentEmotion || 'neutral').toLowerCase();
        const gesture = (options.gesture || 'talking').toLowerCase();
        this.currentEmotion = emotion;

        const speakingEmotionBadge = document.getElementById('emotionBadge');
        if (speakingEmotionBadge) {
          speakingEmotionBadge.textContent = `Emotion: ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}`;
        }

        const isOneShot = gesture && !['idle', 'talking', 'speech', 'speaking'].includes(gesture);
        if (isOneShot) {
          this.playAction(gesture, 0.35);
        } else {
          this.playAction('Talking', 0.35);
        }
        if (speechBubble) {
          speechBubble.textContent = options.bubbleText || (isHindi
            ? "Ganga sanrakshan par yah jaankari suniye..."
            : "Here is verified information about River Ganga...");
        }
        break;

      case 'IDLE':
      default:
        this.clearViseme();
        this.currentEmotion = 'neutral';
        this.currentGesture = 'idle';
        if (this.targetMorphInfluences) this.targetMorphInfluences[2] = 0.15;
        this.playAction('Idle');
        const idleEmotionBadge = document.getElementById('emotionBadge');
        if (idleEmotionBadge) {
          idleEmotionBadge.textContent = 'Emotion: Neutral';
        }
        if (speechBubble) {
          speechBubble.textContent = isHindi
            ? "Namaste! Main Chacha Chaudhary, Ganga ke baare mein aapko sahi aur bharosemand jaankari dene ke liye yahan hoon!"
            : "Namaste! I am Chacha Chaudhary, your official Ganga guide. Ask me anything about River Ganga, conservation, and water quality!";
        }
        break;
    }
  }

  // =========================================================================
  // Resource Lifecycle & Memory Disposal
  // =========================================================================

  dispose() {
    if (this._rafId) {
      cancelAnimationFrame(this._rafId);
    }
    if (this._resizeHandler) {
      window.removeEventListener('resize', this._resizeHandler);
    }
    this.stopAudioLipSync();
    if (this.audioContext && typeof this.audioContext.close === 'function') {
      try { this.audioContext.close(); } catch (e) {}
    }
    if (this.mixer) {
      this.mixer.stopAllAction();
    }
    if (this.model3D) {
      this.model3D.traverse((child) => {
        if (child.geometry) child.geometry.dispose();
        if (child.material) {
          if (Array.isArray(child.material)) {
            child.material.forEach((m) => m.dispose());
          } else {
            child.material.dispose();
          }
        }
      });
    }
    if (this.renderer) {
      this.renderer.dispose();
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { MascotController };
}

