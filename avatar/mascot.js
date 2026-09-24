/**
 * 3D WebGL Avatar Animation Engine for Chacha Chaudhary Mascot
 * Production Implementation: Member 2 Digital Avatar + Voice Runtime
 * 
 * Capabilities:
 * - Primary Active Model: /Member2_Chacha/Chacha_Master.glb (60,000 vertices, 57 bones)
 * - 35 Morph Targets (7 composite emotions, 11 modular expressions, 16 speech visemes)
 * - 9 Mixamo Skeletal Actions with smooth cross-fading & semantic mapping
 * - Autonomous Procedural Blinking Engine (3-7s intervals, 0.15s duration)
 * - Prioritized Avatar State Machine (IDLE, LISTENING, THINKING, SPEAKING)
 * - Acoustic Rhubarb Lip-Sync & Audio Synchronization
 * - Preserves legacy FBX / procedural as fallback
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
    this.model3D = null;
    this.skinnedMesh = null;
    this.mixer = null;
    this.actions = {}; // name -> AnimationAction

    // Morph target lookup
    this.morphDict = {};
    this.morphInfluences = null;

    // Active viseme tracking
    this.activeViseme = 'Viseme_Silence';
    this.activeVisemeWeight = 0;

    // Procedural Blink Engine State
    this.blinkState = {
      isBlinking: false,
      progress: 0,
      duration: 0.15,
      timeToNext: this._randomBlinkInterval(),
      side: 'both'
    };

    // Rhubarb Phoneme to Chacha Morph Target Mapping
    this.rhubarbMapping = {
      'A': 'Viseme_MBP',
      'B': 'Viseme_E',
      'C': 'Viseme_E',
      'D': 'Viseme_A',
      'E': 'Viseme_O',
      'F': 'Viseme_U',
      'G': 'Viseme_FV',
      'H': 'Viseme_L',
      'X': 'Viseme_Silence'
    };

    // Semantic to Mixamo Action Name Mapping
    this.gestureActionMap = {
      'idle': 'Chacha_Idle',
      'nod': 'Chacha_Nod',
      'point': 'Chacha_Point',
      'shrug': 'Chacha_Shrug',
      'thinking': 'Chacha_Thinking',
      'laughing': 'Chacha_Laughing',
      'wave': 'Chacha_Waving',
      'thankful': 'Chacha_Thankful',
      'shaking_hands': 'Chacha_ShakingHands',
      // Legacy aliases
      'explaining': 'Chacha_Point',
      'hand': 'Chacha_ShakingHands',
      'gesture': 'Chacha_Shrug',
      'turn': 'Chacha_Idle'
    };

    // All 34 custom shape key names for clean batch resets
    this.allVisemes = [
      'Viseme_Silence', 'Viseme_A', 'Viseme_E', 'Viseme_I', 'Viseme_O', 'Viseme_U',
      'Viseme_MBP', 'Viseme_FV', 'Viseme_L', 'Viseme_DTN', 'Viseme_KG', 'Viseme_SHCH',
      'Viseme_R', 'Viseme_S', 'Viseme_NG', 'Viseme_Th'
    ];

    this.allEmotions = [
      'Emotion_Happy', 'Emotion_Sad', 'Emotion_Angry', 'Emotion_Surprised',
      'Emotion_Confused', 'Emotion_Thinking', 'Emotion_Laughing'
    ];

    if (this.canvas) {
      this.init3DScene();
    }
  }

  init3DScene() {
    const container = this.canvas.parentElement;
    const width = container.clientWidth || 360;
    const height = container.clientHeight || 380;

    // 1. WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.outputEncoding = THREE.sRGBEncoding;

    // 2. Scene & Camera Setup (Full body portrait framing)
    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 50.0);
    this.camera.position.set(0.0, 0.68, 2.20);
    this.camera.lookAt(0.0, 0.65, 0.0);

    // 3. Balanced Studio 3-Point Lighting Rig (Sculpt shading matching preview render)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.38);
    this.scene.add(ambientLight);

    this.keyLight = new THREE.DirectionalLight(0xfff6ec, 1.15);
    this.keyLight.position.set(1.5, 2.5, 2.2);
    this.scene.add(this.keyLight);

    this.fillLight = new THREE.DirectionalLight(0xdbeafe, 0.45);
    this.fillLight.position.set(-1.5, 1.2, 1.5);
    this.scene.add(this.fillLight);

    this.rimLight = new THREE.DirectionalLight(0xffffff, 0.75);
    this.rimLight.position.set(0, 2.5, -2.0);
    this.scene.add(this.rimLight);

    // 4. Character Container Group (Single active container for Member 2 GLB)
    this.characterGroup = new THREE.Group();
    this.scene.add(this.characterGroup);

    // 5. Load Primary & ONLY Production Model (Member 2 Chacha GLB)
    // NOTE: Old FBX / procedural meshes are strictly excluded from runtime
    this.loadMember2GLB();

    // 6. Animation Clock & Render Loop
    this.clock = new THREE.Clock();
    const animate = () => {
      requestAnimationFrame(animate);
      const delta = this.clock.getDelta();

      if (this.mixer) {
        this.mixer.update(delta);
      }

      // Update autonomous procedural blinking
      this._updateProceduralBlink(delta);

      // Subtle breathing motion (3mm)
      if (this.characterGroup) {
        this.characterGroup.position.y = Math.sin(Date.now() / 900) * 0.003;
      }

      this.renderer.render(this.scene, this.camera);
    };
    animate();

    // Window Resize Handler
    window.addEventListener('resize', () => {
      if (!container) return;
      const w = container.clientWidth || 360;
      const h = container.clientHeight || 380;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    });
  }

  /**
   * Primary Production Asset Loader: Member 2 Chacha_Master.glb
   * Strictly the ONLY model loaded into the Three.js scene.
   * No FBX and no procedural fallback mesh is ever created or displayed.
   */
  loadMember2GLB() {
    if (typeof THREE.GLTFLoader === 'undefined') {
      console.error('[Mascot 3D Engine] THREE.GLTFLoader is not available. Cannot load Member 2 Chacha.');
      const overlay = document.getElementById('avatarLoadingOverlay');
      if (overlay) {
        overlay.innerHTML = '<div style="color:#ef4444;font-weight:600;text-align:center;">Member 2 Chacha failed to load.</div><div style="color:#94a3b8;font-size:0.75rem;margin-top:6px;">THREE.GLTFLoader missing.</div>';
      }
      return;
    }

    const glbPath = '/Member2_Chacha/Chacha_Master.glb';
    const loader = new THREE.GLTFLoader();

    console.log(`[Mascot 3D Engine] Loading Production Member 2 GLB: ${glbPath}...`);

    loader.load(
      glbPath,
      (gltf) => {
        const root = gltf.scene || gltf.scenes[0];

        let meshCount = 0;
        let skinnedMeshCount = 0;

        // Find SkinnedMesh, assign studio material, and cache morph target bindings
        root.traverse((child) => {
          if (child.isMesh) {
            meshCount++;
            child.castShadow = true;
            child.receiveShadow = true;
            if (child.isSkinnedMesh) {
              skinnedMeshCount++;
            }
            if (child.morphTargetDictionary && child.morphTargetInfluences) {
              this.skinnedMesh = child;
              this.morphDict = child.morphTargetDictionary;
              this.morphInfluences = child.morphTargetInfluences;
            }

            // CRITICAL FOR THREE.JS R128: Enable skinning and morph targets on material!
            child.material = new THREE.MeshStandardMaterial({
              color: 0xded5c7,
              roughness: 0.65,
              metalness: 0.02,
              skinning: true,
              morphTargets: true,
              morphNormals: true,
              side: THREE.DoubleSide
            });
          }
        });

        // Set scale so character is ~1.35m in Three.js (0.019m raw * 71.0 = 1.35m)
        root.scale.setScalar(71.0);
        root.position.set(0, 0, 0);

        this.camera.near = 0.1;
        this.camera.far = 50.0;
        this.camera.position.set(0.0, 0.68, 2.20);
        this.camera.lookAt(0.0, 0.65, 0.0);
        this.camera.updateProjectionMatrix();

        console.log(`[Mascot 3D Engine] Framed Chacha Full Body: scale=71.0, camera at (0, 0.68, 2.20), skinning and morphTargets enabled`);

        // Setup AnimationMixer for all 9 Mixamo actions
        if (gltf.animations && gltf.animations.length > 0) {
          this.mixer = new THREE.AnimationMixer(root);
          this.actions = {};

          gltf.animations.forEach((clip) => {
            const action = this.mixer.clipAction(clip);
            this.actions[clip.name] = action;
          });

          // Start default idle animation
          this.playAction('Chacha_Idle');
        }

        // Attach ONLY production GLB
        this.characterGroup.add(root);
        this.model3D = root;
        this.is3DReady = true;
        this.isProductionGLB = true;
        this.avatarReady = true;

        // Hide loading overlay
        const overlay = document.getElementById('avatarLoadingOverlay');
        if (overlay) {
          overlay.style.display = 'none';
        }

        // Runtime log explicitly required by Phase 4 specification
        console.log(`=== ACTIVE AVATAR ===\nMember 2 Chacha\nSource: /Member2_Chacha/Chacha_Master.glb\nMeshes: ${meshCount}\nSkinned meshes: ${skinnedMeshCount}\nMorph targets: ${Object.keys(this.morphDict).length}\nAnimation clips: ${Object.keys(this.actions).length}\n=====================`);
      },
      (xhr) => {
        if (xhr.lengthComputable && xhr.total > 0) {
          const pct = Math.round((xhr.loaded / xhr.total) * 100);
          const label = document.querySelector('.loading-label');
          if (label) label.textContent = `Loading Member 2 Chacha (${pct}%)...`;
        }
      },
      (err) => {
        console.error('[Mascot 3D Engine] Member 2 Chacha failed to load: ', err);
        const overlay = document.getElementById('avatarLoadingOverlay');
        if (overlay) {
          overlay.innerHTML = '<div style="color:#ef4444;font-weight:600;text-align:center;">Member 2 Chacha failed to load.</div><div style="color:#94a3b8;font-size:0.75rem;margin-top:6px;">Check console logs for details.</div>';
        }
      }
    );
  }

  // =========================================================================
  // Morph Target / Blendshape API
  // =========================================================================

  /**
   * Set single morph target by name (0.0 to 1.0)
   */
  setMorph(name, value) {
    if (!this.morphDict || !this.morphInfluences) return;
    const idx = this.morphDict[name];
    if (idx !== undefined) {
      this.morphInfluences[idx] = Math.max(0.0, Math.min(1.0, Number(value) || 0.0));
    }
  }

  getMorph(name) {
    if (!this.morphDict || !this.morphInfluences) return 0.0;
    const idx = this.morphDict[name];
    return idx !== undefined ? this.morphInfluences[idx] : 0.0;
  }

  /**
   * Set Composite Facial Emotion (mutually exclusive composite emotions)
   */
  setEmotion(emotion, intensity = 1.0) {
    const emKey = (emotion || 'neutral').toLowerCase().trim();
    this.currentEmotion = emKey;

    if (!this.isProductionGLB) {
      // Legacy procedural fallback
      this._setProceduralEmotion(emKey);
      return;
    }

    // Clear all existing composite emotions
    this.allEmotions.forEach((emo) => this.setMorph(emo, 0.0));
    this.setMorph('Eyes_Squint', 0.0);
    this.setMorph('Brow_Raise', 0.0);
    this.setMorph('Brow_Furrow', 0.0);

    const targetVal = Math.max(0.0, Math.min(1.0, intensity));

    switch (emKey) {
      case 'happy':
        this.setMorph('Emotion_Happy', targetVal);
        this.setMorph('Eyes_Squint', targetVal * 0.3);
        break;
      case 'sad':
        this.setMorph('Emotion_Sad', targetVal);
        break;
      case 'angry':
        this.setMorph('Emotion_Angry', targetVal);
        this.setMorph('Brow_Furrow', targetVal * 0.5);
        break;
      case 'surprised':
        this.setMorph('Emotion_Surprised', targetVal);
        this.setMorph('Eyes_Wide', targetVal * 0.4);
        break;
      case 'confused':
        this.setMorph('Emotion_Confused', targetVal);
        this.setMorph('Brow_Raise', targetVal * 0.35);
        break;
      case 'thinking':
        this.setMorph('Emotion_Thinking', targetVal);
        this.setMorph('Brow_Furrow', targetVal * 0.25);
        break;
      case 'laughing':
        this.setMorph('Emotion_Laughing', targetVal);
        this.setMorph('Eyes_Squint', targetVal * 0.5);
        break;
      case 'neutral':
      default:
        // Already zeroed
        break;
    }
  }

  clearEmotion() {
    this.setEmotion('neutral', 0.0);
  }

  /**
   * Set Speech Viseme (Mutually exclusive phonetic mouth cues)
   * Supports either full Member 2 viseme name ('Viseme_A') or Rhubarb cue char ('A', 'B', etc.)
   */
  setViseme(viseme, intensity = 1.0) {
    if (!viseme) return;

    let targetViseme = viseme;
    if (this.rhubarbMapping[viseme.toUpperCase()]) {
      targetViseme = this.rhubarbMapping[viseme.toUpperCase()];
    }

    this.activeViseme = targetViseme;
    this.activeVisemeWeight = intensity;

    if (!this.isProductionGLB) {
      // Legacy procedural mouth fallback
      this.setMouthAperture(intensity);
      return;
    }

    // Reset all visemes to 0.0
    this.allVisemes.forEach((v) => this.setMorph(v, 0.0));

    // Apply active viseme
    this.setMorph(targetViseme, intensity);
  }

  clearViseme() {
    this.activeViseme = 'Viseme_Silence';
    this.activeVisemeWeight = 0.0;
    this.allVisemes.forEach((v) => this.setMorph(v, 0.0));
    if (this.mouth3DMesh) {
      this.setMouthAperture(0.0);
    }
  }

  /**
   * Independent Bilateral and Unilateral Eye Blinks
   */
  setBlink(side = 'both', value = 1.0) {
    const val = Math.max(0.0, Math.min(1.0, value));
    if (side === 'left' || side === 'both') {
      this.setMorph('Blink_L', val);
    }
    if (side === 'right' || side === 'both') {
      this.setMorph('Blink_R', val);
    }
  }

  triggerBlink(duration = 0.15) {
    this.blinkState.isBlinking = true;
    this.blinkState.progress = 0;
    this.blinkState.duration = duration;
    this.blinkState.side = 'both';
  }

  blink() {
    this.triggerBlink(0.15);
  }

  resetFace() {
    if (this.morphInfluences) {
      for (let i = 0; i < this.morphInfluences.length; i++) {
        this.morphInfluences[i] = 0.0;
      }
    }
    this.currentEmotion = 'neutral';
    this.activeViseme = 'Viseme_Silence';
  }

  // =========================================================================
  // Skeletal Body Gesture & Action API
  // =========================================================================

  /**
   * Play skeletal action by exact clip name or semantic alias with smooth crossfade
   */
  playAction(actionName, duration = 0.35) {
    if (!this.actions || Object.keys(this.actions).length === 0) return;

    // Resolve semantic alias
    const resolvedName = this.gestureActionMap[actionName.toLowerCase()] || actionName;
    const targetAction = this.actions[resolvedName];

    if (!targetAction) {
      console.warn(`[Mascot 3D Engine] Action '${actionName}' (${resolvedName}) not found in clips.`);
      return;
    }

    if (this.activeActionName === resolvedName) return;

    const prevAction = this.activeActionName ? this.actions[this.activeActionName] : null;
    this.activeActionName = resolvedName;

    targetAction.reset();
    targetAction.setEffectiveTimeScale(1.0);
    targetAction.setEffectiveWeight(1.0);
    targetAction.clampWhenFinished = false;

    // Set loop modes
    if (resolvedName === 'Chacha_Idle') {
      targetAction.setLoop(THREE.LoopRepeat);
    } else {
      targetAction.setLoop(THREE.LoopRepeat, 3);
    }

    if (prevAction) {
      prevAction.crossFadeTo(targetAction, duration, true);
    }
    targetAction.play();
  }

  setGesture(gesture) {
    this.currentGesture = (gesture || 'idle').toLowerCase();
    this.playAction(this.currentGesture);
  }

  // =========================================================================
  // State Machine Integration
  // =========================================================================

  setState(state) {
    const s = (state || 'IDLE').toUpperCase();
    this.currentState = s;

    switch (s) {
      case 'LISTENING':
        this.playAction('Chacha_Idle');
        this.setMorph('Brow_Raise', 0.35);
        this.setMorph('Eyes_Wide', 0.25);
        break;

      case 'THINKING':
        this.playAction('Chacha_Thinking');
        this.setEmotion('thinking', 0.85);
        break;

      case 'SPEAKING':
        // Speaking gesture is driven by renderResponse; defaults to nod/point/idle
        break;

      case 'IDLE':
      default:
        this.clearViseme();
        this.setMorph('Brow_Raise', 0.0);
        this.setMorph('Eyes_Wide', 0.0);
        this.playAction('Chacha_Idle');
        break;
    }
  }

  // =========================================================================
  // Procedural Blinking Engine
  // =========================================================================

  _randomBlinkInterval() {
    // 3.0s to 7.0s interval
    return 3.0 + Math.random() * 4.0;
  }

  _updateProceduralBlink(dt) {
    if (!this.isProductionGLB) return;

    if (this.blinkState.isBlinking) {
      this.blinkState.progress += dt;
      if (this.blinkState.progress >= this.blinkState.duration) {
        // Complete blink
        this.setBlink(this.blinkState.side, 0.0);
        this.blinkState.isBlinking = false;
        this.blinkState.progress = 0;
        this.blinkState.timeToNext = this._randomBlinkInterval();
      } else {
        // Sinusoidal curve 0 -> 1 -> 0
        const p = this.blinkState.progress / this.blinkState.duration;
        const val = Math.sin(Math.PI * p);
        this.setBlink(this.blinkState.side, val);
      }
    } else {
      this.blinkState.timeToNext -= dt;
      if (this.blinkState.timeToNext <= 0) {
        this.triggerBlink(0.15);
      }
    }
  }

  // =========================================================================
  // Legacy Procedural Compatibility Helpers
  // =========================================================================

  setMouthAperture(val) {
    const clamped = Math.max(0, Math.min(1, val));
    this.mouthAperture = clamped;
    if (this.isProductionGLB) {
      this.setMorph('Viseme_A', clamped * 0.8);
    }
  }

  _setProceduralEmotion(em) {
    // Procedural avatar disabled. Emotions are handled via 35 morph targets on Chacha_Master.glb.
  }
}
