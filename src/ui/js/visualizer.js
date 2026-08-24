/**
 * High-performance 60 FPS Canvas Audio VU / Peak Meter Renderer
 */
class AudioVisualizerEngine {
  constructor() {
    this.canvases = new Map(); // id -> { canvas, ctx, currentPeak, holdPeak, holdTime }
    this.animationFrameId = null;
    this.isRunning = false;
  }

  registerCanvas(sourceId, canvasElement) {
    if (!canvasElement) return;
    const ctx = canvasElement.getContext('2d');
    
    // Support HiDPI / Retina screens
    const dpr = window.devicePixelRatio || 1;
    const rect = canvasElement.getBoundingClientRect();
    const width = rect.width || 220;
    const height = rect.height || 14;

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
    const totalSegments = 24;
    const gap = 2;

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

      // Background track
      ctx.fillStyle = '#181b28';
      ctx.fillRect(0, 0, width, height);

      const segWidth = (width - (totalSegments - 1) * gap) / totalSegments;
      const activeSegments = Math.round(entry.currentPeak * totalSegments);
      const holdSegment = Math.round(entry.holdPeak * totalSegments);

      // Render segmented LED meters
      for (let i = 0; i < totalSegments; i++) {
        const x = i * (segWidth + gap);
        const ratio = i / totalSegments;

        // Color zoning: Green (0-60%), Yellow (60-85%), Red (>85%)
        let activeColor = '#10b981';
        let inactiveColor = '#1e293b';

        if (ratio > 0.85) {
          activeColor = '#ef4444'; // Red (clipping)
          inactiveColor = '#331b24';
        } else if (ratio > 0.60) {
          activeColor = '#f59e0b'; // Amber
          inactiveColor = '#32281e';
        }

        if (i < activeSegments) {
          ctx.fillStyle = activeColor;
          ctx.shadowColor = activeColor;
          ctx.shadowBlur = 4;
        } else {
          ctx.fillStyle = inactiveColor;
          ctx.shadowBlur = 0;
        }

        // Draw LED block with slight rounded corner
        ctx.fillRect(x, 1, Math.max(1, segWidth), height - 2);
      }

      // Render Peak Hold Tick
      if (holdSegment > 0 && holdSegment <= totalSegments) {
        const holdX = (holdSegment - 1) * (segWidth + gap);
        const holdRatio = (holdSegment - 1) / totalSegments;
        ctx.fillStyle = holdRatio > 0.85 ? '#ff4d6d' : (holdRatio > 0.6 ? '#fbbf24' : '#34d399');
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 6;
        ctx.fillRect(holdX, 0, Math.max(2, segWidth), height);
      }

      // Reset shadow for next draw
      ctx.shadowBlur = 0;
    });
  }
}

// Global visualizer engine instance
window.visualizerEngine = new AudioVisualizerEngine();
