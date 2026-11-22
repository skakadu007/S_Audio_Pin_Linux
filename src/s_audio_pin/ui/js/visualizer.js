/**
 * S_Audio_Pin — 60 FPS Logarithmic dB Audio VU Meter Engine
 */
class AudioVisualizerEngine {
  constructor() {
    this.canvases = new Map(); // id -> { canvas, ctx, width, height, currentPeak, targetPeak, holdPeak, holdTime }
    this.animationFrameId = null;
    this.isRunning = false;
    this._resizeObserver =
      typeof ResizeObserver !== 'undefined'
        ? new ResizeObserver((entries) => {
            for (const entry of entries) {
              const sourceId = entry.target.dataset.vizSourceId;
              if (sourceId) {
                this._configureCanvasGeometry(sourceId);
              }
            }
          })
        : null;
  }

  static linearToDbNorm(level) {
    if (!level || level <= 0.0001) return 0.0;
    const clamped = Math.max(1e-5, Math.min(1.0, level));
    const db = Math.max(-48, Math.min(0, 20 * Math.log10(clamped)));
    return (db + 48) / 48;
  }

  _configureCanvasGeometry(sourceId) {
    const entry = this.canvases.get(sourceId);
    if (!entry) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = entry.canvas.getBoundingClientRect();
    const width = Math.round(rect.width) || 140;
    const height = Math.round(rect.height) || 9;

    if (entry.width === width && entry.height === height && entry.dpr === dpr) {
      return;
    }

    entry.width = width;
    entry.height = height;
    entry.dpr = dpr;
    entry.canvas.width = width * dpr;
    entry.canvas.height = height * dpr;
    entry.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  registerCanvas(sourceId, canvasElement) {
    if (!canvasElement) return;
    const existing = this.canvases.get(sourceId);
    if (existing && existing.canvas === canvasElement) {
      this._configureCanvasGeometry(sourceId);
      return;
    }

    if (existing && this._resizeObserver) {
      this._resizeObserver.unobserve(existing.canvas);
    }

    const ctx = canvasElement.getContext('2d');
    canvasElement.dataset.vizSourceId = sourceId;

    this.canvases.set(sourceId, {
      canvas: canvasElement,
      ctx: ctx,
      width: 0,
      height: 0,
      dpr: 1,
      currentPeak: 0.0,
      targetPeak: 0.0,
      holdPeak: 0.0,
      holdTime: 0
    });

    this._configureCanvasGeometry(sourceId);
    if (this._resizeObserver) {
      this._resizeObserver.observe(canvasElement);
    }

    if (!this.isRunning) {
      this.start();
    }
  }

  unregisterCanvas(sourceId) {
    const entry = this.canvases.get(sourceId);
    if (entry && this._resizeObserver) {
      this._resizeObserver.unobserve(entry.canvas);
    }
    this.canvases.delete(sourceId);
    if (this.canvases.size === 0 && this.isRunning) {
      this.stop();
    }
  }

  pruneCanvases(activeIds) {
    for (const sourceId of Array.from(this.canvases.keys())) {
      if (!activeIds.has(sourceId)) {
        this.unregisterCanvas(sourceId);
      }
    }
  }

  updatePeak(sourceId, targetLevel) {
    const entry = this.canvases.get(sourceId);
    if (entry) {
      const dbNorm = AudioVisualizerEngine.linearToDbNorm(targetLevel);
      entry.targetPeak = Math.max(0.0, Math.min(1.0, dbNorm));
      if (entry.targetPeak > entry.holdPeak) {
        entry.holdPeak = entry.targetPeak;
        entry.holdTime = Date.now();
      }
    }
  }

  start() {
    if (this.isRunning) return;
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
      this.animationFrameId = null;
    }
  }

  render() {
    const now = Date.now();
    const totalSegments = 20;
    const gap = 1.5;

    this.canvases.forEach((entry) => {
      const { ctx, width, height } = entry;
      if (!width || !height) return;

      entry.currentPeak += (entry.targetPeak - entry.currentPeak) * 0.35;
      if (entry.currentPeak < 0.005) entry.currentPeak = 0;

      if (now - entry.holdTime > 600) {
        entry.holdPeak = Math.max(0, entry.holdPeak - 0.02);
      }

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#0f1118';
      ctx.fillRect(0, 0, width, height);

      const totalGapWidth = (totalSegments - 1) * gap;
      const segWidth = Math.max(1, (width - totalGapWidth) / totalSegments);
      const activeSegments = Math.round(entry.currentPeak * totalSegments);
      const holdSegment = Math.round(entry.holdPeak * totalSegments);

      for (let i = 0; i < totalSegments; i++) {
        const x = i * (segWidth + gap);
        const ratio = i / totalSegments;

        let activeColor = '#30d158';
        let inactiveColor = '#14281a';

        if (ratio > 0.85) {
          activeColor = '#ff453a';
          inactiveColor = '#2d1416';
        } else if (ratio > 0.60) {
          activeColor = '#ffd60a';
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

        ctx.fillRect(x, 1, segWidth, height - 2);
      }

      if (holdSegment > 0 && holdSegment <= totalSegments) {
        const holdX = (holdSegment - 1) * (segWidth + gap);
        const holdRatio = (holdSegment - 1) / totalSegments;
        ctx.fillStyle = holdRatio > 0.85 ? '#ff453a' : (holdRatio > 0.6 ? '#ffd60a' : '#ffffff');
        ctx.shadowColor = ctx.fillStyle;
        ctx.shadowBlur = 4;
        ctx.fillRect(holdX, 0, Math.max(1.5, segWidth), height);
      }

      ctx.shadowBlur = 0;
    });
  }
}

window.visualizerEngine = new AudioVisualizerEngine();
