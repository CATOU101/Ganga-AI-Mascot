/**
 * Vector SVG Mascot Animation Engine for "Chacha Mascot"
 * Controls expressions, gestures, mouth lip-sync morphing, and idle micro-animations.
 */

class MascotController {
  constructor() {
    this.mouthPath = document.getElementById('mouthPath');
    this.leftBrow = document.getElementById('leftBrow');
    this.rightBrow = document.getElementById('rightBrow');
    this.leftPupil = document.getElementById('leftPupil');
    this.rightPupil = document.getElementById('rightPupil');
    this.headGroup = document.getElementById('headGroup');
    this.leftArmPath = document.getElementById('leftArmPath');
    this.rightArmPath = document.getElementById('rightArmPath');
    this.leftHand = document.getElementById('leftHand');
    this.rightHand = document.getElementById('rightHand');
    
    this.currentEmotion = 'neutral';
    this.currentGesture = 'idle';
    this.blinkTimer = null;
    
    this.initIdleAnimations();
  }

  initIdleAnimations() {
    // Eye Blinking loop
    setInterval(() => {
      this.blink();
    }, 4500);
  }

  blink() {
    if (!this.leftPupil || !this.rightPupil) return;
    this.leftPupil.setAttribute('ry', '0.5');
    this.rightPupil.setAttribute('ry', '0.5');
    setTimeout(() => {
      this.leftPupil.setAttribute('ry', '4.5');
      this.rightPupil.setAttribute('ry', '4.5');
    }, 150);
  }

  /**
   * Set mouth openness for lip-sync (val: 0.0 to 1.0)
   */
  setMouthAperture(val) {
    if (!this.mouthPath) return;
    const clamped = Math.max(0, Math.min(1, val));
    const openY = 252 + clamped * 22;
    const pathD = `M 180 252 Q 200 ${openY} 220 252 Q 200 ${252 - clamped * 4} 180 252 Z`;
    this.mouthPath.setAttribute('d', pathD);
  }

  /**
   * Apply emotion face pose: 'neutral' | 'happy' | 'sad' | 'thinking'
   */
  setEmotion(emotion) {
    this.currentEmotion = emotion || 'neutral';
    
    switch (this.currentEmotion.toLowerCase()) {
      case 'happy':
        this.leftBrow.setAttribute('d', 'M 155 176 Q 170 166 185 178');
        this.rightBrow.setAttribute('d', 'M 215 178 Q 230 166 245 176');
        this.headGroup.setAttribute('transform', 'rotate(2 200 210)');
        this.leftPupil.setAttribute('cy', '194');
        this.rightPupil.setAttribute('cy', '194');
        break;

      case 'sad':
        this.leftBrow.setAttribute('d', 'M 155 175 Q 170 182 185 182');
        this.rightBrow.setAttribute('d', 'M 215 182 Q 230 182 245 175');
        this.headGroup.setAttribute('transform', 'rotate(-3 200 210)');
        this.leftPupil.setAttribute('cy', '197');
        this.rightPupil.setAttribute('cy', '197');
        break;

      case 'thinking':
        this.leftBrow.setAttribute('d', 'M 155 174 Q 170 168 185 175');
        this.rightBrow.setAttribute('d', 'M 215 182 Q 230 180 245 182');
        this.headGroup.setAttribute('transform', 'rotate(4 200 210)');
        this.leftPupil.setAttribute('cx', '173');
        this.leftPupil.setAttribute('cy', '192');
        this.rightPupil.setAttribute('cx', '233');
        this.rightPupil.setAttribute('cy', '192');
        break;

      case 'neutral':
      default:
        this.leftBrow.setAttribute('d', 'M 155 180 Q 170 172 185 180');
        this.rightBrow.setAttribute('d', 'M 215 180 Q 230 172 245 180');
        this.headGroup.setAttribute('transform', 'rotate(0 200 210)');
        this.leftPupil.setAttribute('cx', '170');
        this.leftPupil.setAttribute('cy', '195');
        this.rightPupil.setAttribute('cx', '230');
        this.rightPupil.setAttribute('cy', '195');
        break;
    }
  }

  /**
   * Apply gesture arm animation pose: 'idle' | 'thinking' | 'explaining' | 'wave'
   */
  setGesture(gesture) {
    this.currentGesture = gesture || 'idle';

    switch (this.currentGesture.toLowerCase()) {
      case 'wave':
        // Right hand waving pose
        this.rightArmPath.setAttribute('d', 'M 280 310 C 330 280, 350 220, 340 180');
        this.rightHand.setAttribute('cx', '340');
        this.rightHand.setAttribute('cy', '180');
        this.leftArmPath.setAttribute('d', 'M 120 310 C 90 350, 70 380, 70 420');
        this.leftHand.setAttribute('cx', '70');
        this.leftHand.setAttribute('cy', '420');
        break;

      case 'thinking':
        // Right hand at chin pose
        this.rightArmPath.setAttribute('d', 'M 280 310 C 300 320, 240 280, 215 255');
        this.rightHand.setAttribute('cx', '215');
        this.rightHand.setAttribute('cy', '255');
        this.leftArmPath.setAttribute('d', 'M 120 310 C 90 350, 70 380, 70 420');
        this.leftHand.setAttribute('cx', '70');
        this.leftHand.setAttribute('cy', '420');
        break;

      case 'explaining':
        // Both hands gesturing forward
        this.leftArmPath.setAttribute('d', 'M 120 310 C 80 330, 60 310, 85 280');
        this.leftHand.setAttribute('cx', '85');
        this.leftHand.setAttribute('cy', '280');
        this.rightArmPath.setAttribute('d', 'M 280 310 C 320 330, 340 310, 315 280');
        this.rightHand.setAttribute('cx', '315');
        this.rightHand.setAttribute('cy', '280');
        break;

      case 'idle':
      default:
        this.leftArmPath.setAttribute('d', 'M 120 310 C 90 350, 70 380, 70 420');
        this.leftHand.setAttribute('cx', '70');
        this.leftHand.setAttribute('cy', '420');
        this.rightArmPath.setAttribute('d', 'M 280 310 C 310 350, 330 380, 330 420');
        this.rightHand.setAttribute('cx', '330');
        this.rightHand.setAttribute('cy', '420');
        break;
    }
  }
}
