/**
 * Just Another Wine App — minimal charting helpers.
 * Lightweight canvas-based line charts for sensor history — no dependency.
 */

const Charts = (() => {
  function lineChart(canvas, readings, options = {}) {
    const ctx = canvas.getContext("2d");
    const dpr = window.devicePixelRatio || 1;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, width, height);

    if (!readings || readings.length === 0) {
      ctx.fillStyle = "#6b6475";
      ctx.font = "13px Inter, sans-serif";
      ctx.fillText("No data available", 12, height / 2);
      return;
    }

    const values = readings.map((r) => r.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const padding = 8;

    const points = readings.map((r, i) => {
      const x = padding + (i / (readings.length - 1 || 1)) * (width - padding * 2);
      const y = height - padding - ((r.value - min) / range) * (height - padding * 2);
      return [x, y];
    });

    // Line
    ctx.beginPath();
    ctx.strokeStyle = options.color || "#d4925a";
    ctx.lineWidth = 2;
    points.forEach(([x, y], i) => (i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)));
    ctx.stroke();

    // Fill under line
    ctx.lineTo(points[points.length - 1][0], height - padding);
    ctx.lineTo(points[0][0], height - padding);
    ctx.closePath();
    ctx.fillStyle = (options.color || "#d4925a") + "22";
    ctx.fill();

    // Latest point
    const [lx, ly] = points[points.length - 1];
    ctx.beginPath();
    ctx.arc(lx, ly, 3, 0, Math.PI * 2);
    ctx.fillStyle = options.color || "#d4925a";
    ctx.fill();
  }

  function sparkline(canvas, values, color = "#d4925a") {
    lineChart(canvas, values.map((v) => ({ value: v })), { color });
  }

  return { lineChart, sparkline };
})();
