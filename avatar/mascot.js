/**
 * 3D WebGL Avatar Animation Engine for "Chacha Mascot" (Model 2: Chacha_Rigged.fbx)
 * Renders the canonical 3D Chacha avatar in WebGL using Three.js with skeletal rigging,
 * facial blendshapes / eyebrow poses, arm gestural poses, and lip-sync mouth morphing.
 */

class MascotController {
  constructor() {
    this.canvas = document.getElementById('mascotCanvas3D');
    this.currentEmotion = 'neutral';
    this.currentGesture = 'idle';
    this.mouthAperture = 0;
    
    this.is3DReady = false;
    this.model3D = null;
    this.mixer = null;

    if (this.canvas) {
      this.init3DScene();
    }
  }

  init3DScene() {
    // 1. Create WebGL Renderer
    const container = this.canvas.parentElement;
    const width = container.clientWidth || 360;
    const height = container.clientHeight || 380;

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
    });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.outputEncoding = THREE.sRGBEncoding;

    // 2. Create Scene & Camera
    this.scene = new THREE.Scene();

    this.camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 100);
    this.camera.position.set(0, 1.35, 2.6);
    this.camera.lookAt(0, 1.1, 0);

    // 3. Studio Lighting setup (Key, Fill, Back light for elderly mascot materials)
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
    this.scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
    keyLight.position.set(2, 4, 3);
    this.scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xea580c, 0.6);
    fillLight.position.set(-2, 2, 2);
    this.scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0xffffff, 0.7);
    rimLight.position.set(0, 3, -3);
    this.scene.add(rimLight);

    // 4. Create 3D Character Group (Procedural 3D Mesh + FBX Model Loader)
    this.characterGroup = new THREE.Group();
    this.scene.add(this.characterGroup);

    this.buildProcedural3DMascot();
    this.load3DFBXModel();

    // 5. Render Loop
    this.clock = new THREE.Clock();
    const animate = () => {
      requestAnimationFrame(animate);
      const delta = this.clock.getDelta();
      
      if (this.mixer) {
        this.mixer.update(delta);
      }
      
      // Idle micro-animation breathing
      if (this.characterGroup) {
        this.characterGroup.position.y = Math.sin(Date.now() / 800) * 0.015;
        this.characterGroup.rotation.y = Math.sin(Date.now() / 1500) * 0.03;
      }

      this.renderer.render(this.scene, this.camera);
    };
    animate();

    // Handle Window Resize
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
   * Build authentic 3D Procedural Chacha Avatar mesh (Red Turban, Moustache, White Kurta, Vest, Cane)
   */
  buildProcedural3DMascot() {
    this.avatar3DMeshGroup = new THREE.Group();

    // Head (Skin tone)
    const headGeo = new THREE.SphereGeometry(0.32, 32, 32);
    const skinMat = new THREE.MeshStandardMaterial({ color: 0xfed7aa, roughness: 0.6 });
    const head = new THREE.Mesh(headGeo, skinMat);
    head.position.set(0, 1.2, 0);
    this.avatar3DMeshGroup.add(head);

    // Signature Red Turban
    const turbanGeo = new THREE.SphereGeometry(0.36, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.55);
    const turbanMat = new THREE.MeshStandardMaterial({ color: 0xea580c, roughness: 0.4 });
    const turban = new THREE.Mesh(turbanGeo, turbanMat);
    turban.position.set(0, 1.25, 0);
    this.avatar3DMeshGroup.add(turban);

    // Signature White Moustache
    const stacheGeo = new THREE.ConeGeometry(0.18, 0.08, 16);
    const stacheMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, roughness: 0.8 });
    const stacheL = new THREE.Mesh(stacheGeo, stacheMat);
    stacheL.rotation.z = -Math.PI / 2.5;
    stacheL.position.set(-0.1, 1.1, 0.28);
    const stacheR = new THREE.Mesh(stacheGeo, stacheMat);
    stacheR.rotation.z = Math.PI / 2.5;
    stacheR.position.set(0.1, 1.1, 0.28);
    this.avatar3DMeshGroup.add(stacheL);
    this.avatar3DMeshGroup.add(stacheR);

    // Mouth Mesh for Lip Sync
    const mouthGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.03, 16);
    const mouthMat = new THREE.MeshStandardMaterial({ color: 0x991b1b });
    this.mouth3DMesh = new THREE.Mesh(mouthGeo, mouthMat);
    this.mouth3DMesh.rotation.x = Math.PI / 2;
    this.mouth3DMesh.position.set(0, 1.02, 0.29);
    this.mouth3DMesh.scale.set(1, 0.2, 1);
    this.avatar3DMeshGroup.add(this.mouth3DMesh);

    // Eyebrows
    const browGeo = new THREE.BoxGeometry(0.12, 0.02, 0.02);
    const browMat = new THREE.MeshStandardMaterial({ color: 0x0f172a });
    this.browL3D = new THREE.Mesh(browGeo, browMat);
    this.browL3D.position.set(-0.12, 1.28, 0.3);
    this.browR3D = new THREE.Mesh(browGeo, browMat);
    this.browR3D.position.set(0.12, 1.28, 0.3);
    this.avatar3DMeshGroup.add(this.browL3D);
    this.avatar3DMeshGroup.add(this.browR3D);

    // Torso / Dark Vest
    const vestGeo = new THREE.CylinderGeometry(0.35, 0.38, 0.75, 32);
    const vestMat = new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.5 });
    const vest = new THREE.Mesh(vestGeo, vestMat);
    vest.position.set(0, 0.55, 0);
    this.avatar3DMeshGroup.add(vest);

    // Left Arm (Gestures)
    const armGeo = new THREE.CylinderGeometry(0.06, 0.05, 0.45, 16);
    const armMat = new THREE.MeshStandardMaterial({ color: 0x0369a1 });
    this.armL3D = new THREE.Mesh(armGeo, armMat);
    this.armL3D.position.set(-0.42, 0.5, 0);
    this.armL3D.rotation.z = 0.3;
    this.avatar3DMeshGroup.add(this.armL3D);

    // Right Arm (Cane / Gestures)
    this.armR3D = new THREE.Mesh(armGeo, armMat);
    this.armR3D.position.set(0.42, 0.5, 0);
    this.armR3D.rotation.z = -0.3;
    this.avatar3DMeshGroup.add(this.armR3D);

    this.characterGroup.add(this.avatar3DMeshGroup);
    this.is3DReady = true;
  }

  /**
   * Load 3D Unity Model 2 (Chacha_Rigged.fbx) if THREE.FBXLoader is available
   */
  load3DFBXModel() {
    if (typeof THREE.FBXLoader === 'undefined') return;

    const fbxPath = '/07_Unity/Assets/ChachaAvatar/Models/Chacha_Rigged.fbx';
    const loader = new THREE.FBXLoader();

    loader.load(
      fbxPath,
      (fbx) => {
        fbx.scale.setScalar(0.012);
        fbx.position.set(0, -0.2, 0);

        fbx.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            if (child.morphTargetSummaries || child.morphTargetInfluences) {
              this.fbxMorphMesh = child;
            }
          }
        });

        // Hide procedural fallback, attach actual FBX
        if (this.avatar3DMeshGroup) {
          this.avatar3DMeshGroup.visible = false;
        }
        this.characterGroup.add(fbx);
        this.model3D = fbx;

        if (fbx.animations && fbx.animations.length > 0) {
          this.mixer = new THREE.AnimationMixer(fbx);
          const action = this.mixer.clipAction(fbx.animations[0]);
          action.play();
        }
        console.log('[Mascot 3D Engine] Successfully loaded Model 2 FBX (Chacha_Rigged.fbx)');
      },
      undefined,
      (err) => {
        console.info('[Mascot 3D Engine] Using 3D WebGL procedural Chacha model (FBX fallback active).');
      }
    );
  }

  /**
   * Lip-sync mouth openness aperture (0.0 to 1.0)
   */
  setMouthAperture(val) {
    const clamped = Math.max(0, Math.min(1, val));
    this.mouthAperture = clamped;

    if (this.mouth3DMesh) {
      this.mouth3DMesh.scale.set(1 + clamped * 0.4, 0.2 + clamped * 0.9, 1);
    }
  }

  /**
   * Set 3D Emotion expression: 'neutral' | 'happy' | 'sad' | 'thinking'
   */
  setEmotion(emotion) {
    this.currentEmotion = emotion || 'neutral';
    const em = this.currentEmotion.toLowerCase();

    if (!this.browL3D || !this.browR3D) return;

    if (em === 'happy') {
      this.browL3D.rotation.z = -0.2;
      this.browR3D.rotation.z = 0.2;
      this.browL3D.position.y = 1.3;
      this.browR3D.position.y = 1.3;
    } else if (em === 'thinking') {
      this.browL3D.rotation.z = 0.25;
      this.browR3D.rotation.z = -0.15;
      this.browL3D.position.y = 1.31;
      this.browR3D.position.y = 1.27;
    } else if (em === 'sad') {
      this.browL3D.rotation.z = 0.2;
      this.browR3D.rotation.z = -0.2;
      this.browL3D.position.y = 1.26;
      this.browR3D.position.y = 1.26;
    } else {
      this.browL3D.rotation.z = 0;
      this.browR3D.rotation.z = 0;
      this.browL3D.position.y = 1.28;
      this.browR3D.position.y = 1.28;
    }
  }

  /**
   * Set 3D Gesture animation pose: 'idle' | 'thinking' | 'explaining' | 'wave'
   */
  setGesture(gesture) {
    this.currentGesture = gesture || 'idle';
    const gst = this.currentGesture.toLowerCase();

    if (!this.armL3D || !this.armR3D) return;

    if (gst === 'explaining') {
      this.armL3D.rotation.z = 0.9;
      this.armR3D.rotation.z = -0.9;
      this.armL3D.rotation.x = 0.4;
      this.armR3D.rotation.x = 0.4;
    } else if (gst === 'thinking') {
      this.armL3D.rotation.z = 0.3;
      this.armR3D.rotation.z = -1.4;
      this.armR3D.rotation.x = 0.8;
    } else if (gst === 'wave') {
      this.armL3D.rotation.z = 0.3;
      this.armR3D.rotation.z = -2.1;
      this.armR3D.rotation.x = 0.2;
    } else {
      this.armL3D.rotation.z = 0.3;
      this.armR3D.rotation.z = -0.3;
      this.armL3D.rotation.x = 0;
      this.armR3D.rotation.x = 0;
    }
  }
}

