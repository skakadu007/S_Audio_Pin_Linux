/**
 * S_Audio_Pin — High-Performance 60 FPS Apple Pro Studio Audio VU Meter Engine
 */
class AudioVisualizerEngine {
  constructor() {
    this.canvases = new Map(); // id -> { canvas, ctx, width, height, currentPeak, targetPeak, holdPeak, holdTime }
    this.animationFrameId = null;
    this.isRunning = false;
  }

  registerCanvas(sourceId, canvasElement) {
    if (!canvasElement) return;
    const ctx = canvasElement.getContext('2d');
    
    // Support HiDPI / Retina displays
    const dpr = window.devicePixelRatio || 1;
    const rect = canvasElement.getBoundingClientRect();
    const width = Math.round(rect.width) || 140;
    const height = Math.round(rect.height) || 9;

    canvasElement.width = width * dpr;
    canvasElement.height = height * dpr;
    ctx.scale(dpr, dpr);

    this.canvases.set(sourceId, {
      canvas: canvasElement,
      ctx: ctx,
      width: width,
      height: height,
      currentPeak: 0.0,
      targetPeak: 0.0,
      holdPeak: 0.0,
      holdTime: 0
    });

    if (!this.isRunning) {
      this.start();
    }
  }

  unregisterCanvas(sourceId) {
    this.canvases.delete(sourceId);
  }

  updatePeak(sourceId, targetLevel) {
    const entry = this.canvases.get(sourceId);
    if (entry) {
      entry.targetPeak = Math.max(0.0, Math.min(1.0, targetLevel));
      if (entry.targetPeak > entry.holdPeak) {
        entry.holdPeak = entry.targetPeak;
        entry.holdTime = Date.now();
      }
    }
  }

  start() {
    this.isRunning = true;
    const renderLoop = () => {
      this.render();
      if (this.isRunning) {
        this.animationFrameId = requestAnimationFrame(renderLoop);
      }
    };
    this.animationFrameId = requestAnimationFrame(renderLoop);
  }

  stop() {
    this.isRunning = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
    }
  }

  render() {
    const now = Date.now();
    const totalSegments = 20;
    const gap = 1.5;

    this.canvases.forEach((entry) => {
      const { ctx, width, height } = entry;

      // Smooth interpolation for fluid animation
      entry.currentPeak += (entry.targetPeak - entry.currentPeak) * 0.35;
      if (entry.currentPeak < 0.005) entry.currentPeak = 0;

      // Peak-hold decay after 600ms
      if (now - entry.holdTime > 600) {
        entry.holdPeak = Math.max(0, entry.holdPeak - 0.02);
      }

      ctx.clearRect(0, 0, width, height);

      // Studio background track
      ctx.fillStyle = '#0f1118';
      ctx.fillRect(0, 0, width, height);

      const totalGapWidth = (totalSegments - 1) * gap;
      const segWidth = Math.max(1, (width - totalGapWidth) / totalSegments);
      const activeSegments = Math.round(entry.currentPeak * totalSegments);
      const holdSegment = Math.round(entry.holdPeak * totalSegments);

      // Render segmented Apple Logic Pro-style LED meters
      for (let i = 0; i < totalSegments; i++) {
        const x = i * (segWidth + gap);
        const ratio = i / totalSegments;

        // Apple Pro Audio Color Calibration:
        // Green (0-60%), Amber (60-85%), Red (>85% overload)
        let activeColor = '#30d158'; // Apple Green
        let inactiveColor = '#14281a';

        if (ratio > 0.85) {
          activeColor = '#ff453a'; // Apple Red
          inactiveColor = '#2d1416';
        } else if (ratio > 0.60) {
          activeColor = '#ffd60a'; // Apple Amber
          inactiveColor = '#2b2512';
        }

        if (i < activeSegments) {
          ctx.fillStyle = activeColor;
          ctx.shadowColor = activeColor;
          ctx.shadowBlur = 3;
        } else {
          ctx.fillStyle = inactiveColor;
          ctx.shadowBlur = 0;
        }

        // Draw LED slice with subtle rounded corner
        ctx.fillRect(x, 1, segWidth, height - 2);
      }

      // Render Peak Hold Indicator
      if (holdSegment > 0 && holdSegment <= totalSegments) {
        const holdX = (holdSegment - 1) * (segWidth + gap);
        const holdRatio = (holdSegment - 1) / totalSegments;
        ctx.fillStyle = holdRatio > 0.85 ? '#ff453a' : (holdRatio > 0.6 ? '#ffd60a' : '#ffffff');
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 4;
        ctx.fillRect(holdX, 0, Math.max(1.5, segWidth), height);
      }

      // Reset shadow for next render iteration
      ctx.shadowBlur = 0;
    });
  }
}

// Global visualizer engine instance
window.visualizerEngine = new AudioVisualizerEngine();
