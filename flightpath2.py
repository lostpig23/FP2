import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Flight Profile Editor", layout="wide")

html_code = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 10px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #f7f9fa;
    user-select: none;
  }
  #container {
    max-width: 1100px;
    margin: 0 auto;
    background: #ffffff;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  }
  canvas {
    display: block;
    border: 1px solid #c8d9e6;
    border-radius: 4px;
    cursor: default;
  }
  #editor-bar {
    margin-top: 12px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  #label-input {
    flex-grow: 1;
    padding: 8px 12px;
    font-size: 14px;
    border: 1px solid #a0b8cc;
    border-radius: 4px;
    outline: none;
  }
  #label-input:focus {
    border-color: #17557d;
    box-shadow: 0 0 0 2px rgba(23,85,125,0.2);
  }
  .btn {
    padding: 8px 14px;
    font-size: 13.5px;
    font-weight: 600;
    color: white;
    background: #17557d;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    white-space: nowrap;
  }
  .btn:hover { background: #0e3752; }
  .btn-alt { background: #2a7b62; }
  .btn-alt:hover { background: #1c5543; }
  #instructions {
    margin-top: 12px;
    padding: 10px 14px;
    background: #f1f5f9;
    border-radius: 6px;
    font-size: 13px;
    color: #334155;
    line-height: 1.6;
  }
</style>
</head>
<body>
<div id="container">
  <canvas id="cv" width="1050" height="540"></canvas>
  <div id="editor-bar">
    <label for="label-input" style="font-weight: bold; font-size: 13px; color: #17557d;">Edit Selected Label:</label>
    <input type="text" id="label-input" placeholder="Click any point or FL label to edit..." />
    <button class="btn btn-alt" onclick="saveImage()">Export Image (J)</button>
    <button class="btn" onclick="saveData()">Export JSON (S)</button>
  </div>
  <div id="instructions">
    <b>Controls:</b><br>
    • <b>Create dot:</b> Double-click anywhere on the line.<br>
    • <b>Hide dot (keep bend):</b> Right-click on a blue dot to hide the dot while preserving the corner bend.<br>
    • <b>Revive dot:</b> Double-click any invisible bend corner to make the blue dot appear again.<br>
    • <b>Delete corner completely:</b> Shift + Right-click on a corner to remove the bend entirely.<br>
    • <b>Add bend & dot:</b> Double-click anywhere on a line.<br>
    • <b>Move:</b> Drag any dot, invisible bend corner, straight line segment, band, or red FL text.<br>
    • <b>Shortcuts:</b> Press <b>J</b> for PNG screenshot | Press <b>S</b> for JSON export.
  </div>
</div>

<script>
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const labelInput = document.getElementById('label-input');

const X_MIN = -2, X_MAX = 126;
const Y_MIN = -2, Y_MAX = 72;
const PAD = { left: 65, right: 35, top: 35, bottom: 55 };

function toScreenX(x) {
  return PAD.left + (x - X_MIN) / (X_MAX - X_MIN) * (cv.width - PAD.left - PAD.right);
}
function toScreenY(y) {
  return cv.height - PAD.bottom - (y - Y_MIN) / (Y_MAX - Y_MIN) * (cv.height - PAD.top - PAD.bottom);
}
function toDataX(px) {
  return X_MIN + (px - PAD.left) / (cv.width - PAD.left - PAD.right) * (X_MAX - X_MIN);
}
function toDataY(py) {
  return Y_MIN + (cv.height - PAD.bottom - py) / (cv.height - PAD.top - PAD.bottom) * (Y_MAX - Y_MIN);
}

// Points: hasDot controls if the checkpoint dot and label are rendered
let points = [
  { x: 1.0, y: 0.0, label: "ENGINES RUNNING", hasDot: true },
  { x: 7.0, y: 0.0, label: "180° TURN F/O & CAPT", hasDot: true },
  { x: 12.0, y: 0.0, label: "DELAYED WINGTIPS EXTENSION", hasDot: true },
  { x: 15.0, y: 0.0, label: "HUD TAKEOFF", hasDot: true },
  { x: 23.0, y: 40.0, label: "VSD DEMO", hasDot: true },
  { x: 39.0, y: 40.0, label: "", hasDot: false }, // Invisible corner (top of descent)
  { x: 41.0, y: 26.0, label: "ILS", hasDot: true },
  { x: 45.0, y: 0.0, label: "", hasDot: false }, // Invisible corner (touchdown)
  { x: 54.0, y: 0.0, label: "HUD TAKEOFF", hasDot: true },
  { x: 55.0, y: 5.0, label: "ENG FAIL R (SEVERE DAMAGE)", hasDot: true },
  { x: 65.0, y: 36.0, label: "", hasDot: false }, // Invisible corner
  { x: 82.0, y: 36.0, label: "", hasDot: false }, // Invisible corner
  { x: 83.0, y: 33.0, label: "RNAV Y (LPV MINIMA)", hasDot: true },
  { x: 91.0, y: 0.0, label: "OEI G/A & M/A", hasDot: true },
  { x: 99.0, y: 5.0, label: "[ ] FUEL IMBALANCE", hasDot: true },
  { x: 104.0, y: 5.0, label: "[ ] WINGTIPS DRIVE FAULT", hasDot: true },
  { x: 106.0, y: 1.5, label: "OEI MANUAL ILS", hasDot: true },
  { x: 116.0, y: 0.0, label: "AFTER LANDING", hasDot: true }
];

let bands = [
  { left: 12.0, right: 26.0 },
  { left: 81.0, right: 93.0 }
];

let flLabels = [
  { text: "FL 360", x: 23.0, y: 34.0 },
  { text: "FL 360", x: 65.0, y: 34.0 }
];

let selectedPointIdx = null;
let selectedSegmentIdx = null;
let selectedBandIdx = null;
let bandDragMode = null;
let selectedFlIdx = null;
let dragStart = null;
let activeTarget = null;
let hoveredTooltip = null;
let hoveredVertexIdx = null;

function draw(hideUI = false) {
  ctx.clearRect(0, 0, cv.width, cv.height);

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, cv.width, cv.height);

  const pL = toScreenX(X_MIN), pR = toScreenX(X_MAX);
  const pT = toScreenY(Y_MAX), pB = toScreenY(Y_MIN);
  ctx.fillStyle = "#d7ecf8";
  ctx.fillRect(pL, pT, pR - pL, pB - pT);

  // 1. Shaded Bands
  bands.forEach((b) => {
    const bx1 = toScreenX(b.left);
    const bx2 = toScreenX(b.right);
    ctx.fillStyle = "rgba(185, 224, 247, 0.75)";
    ctx.fillRect(bx1, pT, bx2 - bx1, pB - pT);

    ctx.strokeStyle = "rgba(140, 190, 225, 0.8)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(bx1, pT); ctx.lineTo(bx1, pB);
    ctx.moveTo(bx2, pT); ctx.lineTo(bx2, pB);
    ctx.stroke();
  });

  // 2. Axes & Tick Marks
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#2c3e50";
  ctx.font = "bold 11px sans-serif";

  for (let x = 0; x <= 120; x += 30) {
    const sx = toScreenX(x);
    ctx.beginPath();
    ctx.moveTo(sx, pT); ctx.lineTo(sx, pB);
    ctx.stroke();
    ctx.fillText(x.toString(), sx - 8, pB + 18);
  }
  ctx.fillText("TIME (Mins)", (pL + pR) / 2 - 35, pB + 40);

  for (let y = 0; y <= 70; y += 10) {
    const sy = toScreenY(y);
    ctx.beginPath();
    ctx.moveTo(pL, sy); ctx.lineTo(pR, sy);
    ctx.stroke();
    ctx.fillText(y.toString(), pL - 25, sy + 4);
  }

  ctx.save();
  ctx.translate(18, (pT + pB) / 2);
  ctx.rotate(-Math.PI / 2);
  ctx.fillText("ALTITUDE (x1,000)", -55, 0);
  ctx.restore();

  // 3. FL 360 Labels
  flLabels.forEach((fl) => {
    ctx.fillStyle = "red";
    ctx.font = "bold 13px sans-serif";
    ctx.fillText(fl.text, toScreenX(fl.x), toScreenY(fl.y));
  });

  // 4. Flight Profile Continuous Line (Bends through all points)
  if (points.length > 1) {
    ctx.strokeStyle = "#17557d";
    ctx.lineWidth = 2.8;
    ctx.beginPath();
    ctx.moveTo(toScreenX(points[0].x), toScreenY(points[0].y));
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(toScreenX(points[i].x), toScreenY(points[i].y));
    }
    ctx.stroke();
  }

  // 5. Checkpoints & Vertices
  points.forEach((pt, i) => {
    const sx = toScreenX(pt.x);
    const sy = toScreenY(pt.y);

    if (pt.hasDot) {
      // Visible Checkpoint Dot
      ctx.fillStyle = "#17557d";
      ctx.beginPath();
      ctx.arc(sx, sy, 5.5, 0, Math.PI * 2);
      ctx.fill();

      // Red Selection Ring
      if (!hideUI && activeTarget && activeTarget.type === 'point' && activeTarget.idx === i) {
        ctx.strokeStyle = "#ff4b4b";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(sx, sy, 8, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Vertical text label
      if (pt.label) {
        ctx.save();
        ctx.translate(sx, sy - 10);
        ctx.rotate(-Math.PI / 2);
        ctx.fillStyle = "#005596";
        ctx.font = "600 10.5px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(pt.label, 0, 3.5);
        ctx.restore();
      }
    } else {
      // Invisible Corner (Draw subtle halo only when hovered or selected)
      if (!hideUI && (hoveredVertexIdx === i || (activeTarget && activeTarget.type === 'point' && activeTarget.idx === i))) {
        ctx.strokeStyle = "rgba(23, 85, 125, 0.45)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(sx, sy, 6, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
  });

  // 6. Tooltip HUD
  if (!hideUI && hoveredTooltip) {
    ctx.fillStyle = "rgba(30, 30, 30, 0.85)";
    ctx.roundRect(hoveredTooltip.x + 10, hoveredTooltip.y - 30, hoveredTooltip.text.length * 7 + 16, 24, 4);
    ctx.fill();
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 10px sans-serif";
    ctx.fillText(hoveredTooltip.text, hoveredTooltip.x + 18, hoveredTooltip.y - 14);
  }
}

function distToSegment(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1, dy = y2 - y1;
  const len2 = dx * dx + dy * dy;
  if (len2 === 0) return Math.hypot(px - x1, py - y1);
  let t = Math.max(0, Math.min(1, ((px - x1) * dx + (py - y1) * dy) / len2));
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}

cv.addEventListener('mousedown', (e) => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const dataX = toDataX(mx);
  const dataY = toDataY(my);

  // --- RIGHT CLICK: Toggle Dot vs Complete Delete ---
  if (e.button === 2) {
    e.preventDefault();
    for (let i = 0; i < points.length; i++) {
      if (Math.hypot(toScreenX(points[i].x) - mx, toScreenY(points[i].y) - my) < 12) {
        if (e.shiftKey) {
          // SHIFT + RIGHT CLICK: Completely remove the bend
          if (points.length > 2) {
            points.splice(i, 1);
            activeTarget = null;
            labelInput.value = "";
          }
        } else {
          // RIGHT CLICK: Remove dot/label, but KEEP THE BEND
          points[i].hasDot = false;
          points[i].label = "";
          activeTarget = null;
          labelInput.value = "";
        }
        draw();
        return;
      }
    }
    return;
  }

  if (e.button !== 0) return;

  // --- LEFT CLICK: FL LABELS ---
  for (let i = 0; i < flLabels.length; i++) {
    const sx = toScreenX(flLabels[i].x), sy = toScreenY(flLabels[i].y);
    if (mx >= sx - 4 && mx <= sx + 60 && my >= sy - 16 && my <= sy + 4) {
      selectedFlIdx = i;
      dragStart = { x: dataX, y: dataY };
      activeTarget = { type: 'fl', idx: i };
      labelInput.value = flLabels[i].text;
      labelInput.focus();
      draw();
      return;
    }
  }

  // --- LEFT CLICK: ALL VERTICES (Visible dots AND invisible bends) ---
  for (let i = 0; i < points.length; i++) {
    if (Math.hypot(toScreenX(points[i].x) - mx, toScreenY(points[i].y) - my) < 12) {
      selectedPointIdx = i;
      activeTarget = { type: 'point', idx: i };
      labelInput.value = points[i].label;
      if (points[i].hasDot) labelInput.focus();
      hoveredTooltip = { x: mx, y: my, text: `T: ${points[i].x.toFixed(1)}m | Alt: ${points[i].y.toFixed(1)}k` };
      draw();
      return;
    }
  }

  // --- LEFT CLICK: SEGMENT DRAGGING ---
  for (let i = 0; i < points.length - 1; i++) {
    const d = distToSegment(mx, my, toScreenX(points[i].x), toScreenY(points[i].y), toScreenX(points[i + 1].x), toScreenY(points[i + 1].y));
    if (d < 8) {
      selectedSegmentIdx = i;
      dragStart = { x: dataX, y: dataY };
      draw();
      return;
    }
  }

  // --- LEFT CLICK: BANDS ---
  const edgeThreshold = 2.0;
  for (let i = 0; i < bands.length; i++) {
    if (Math.abs(dataX - bands[i].left) <= edgeThreshold) {
      selectedBandIdx = i;
      bandDragMode = 'left_edge';
      dragStart = { x: dataX };
      return;
    } else if (Math.abs(dataX - bands[i].right) <= edgeThreshold) {
      selectedBandIdx = i;
      bandDragMode = 'right_edge';
      dragStart = { x: dataX };
      return;
    } else if (dataX >= bands[i].left && dataX <= bands[i].right) {
      selectedBandIdx = i;
      bandDragMode = 'move';
      dragStart = { x: dataX };
      return;
    }
  }
});

// DOUBLE CLICK: Revive invisible dot OR add new bend along line
cv.addEventListener('dblclick', (e) => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

  // 1. If double clicking an existing invisible corner, turn dot back ON
  for (let i = 0; i < points.length; i++) {
    if (Math.hypot(toScreenX(points[i].x) - mx, toScreenY(points[i].y) - my) < 14) {
      points[i].hasDot = true;
      if (!points[i].label) points[i].label = "WAYPOINT";
      activeTarget = { type: 'point', idx: i };
      labelInput.value = points[i].label;
      labelInput.focus();
      draw();
      return;
    }
  }

  // 2. Otherwise insert a new vertex along the line
  for (let i = 0; i < points.length - 1; i++) {
    const d = distToSegment(mx, my, toScreenX(points[i].x), toScreenY(points[i].y), toScreenX(points[i + 1].x), toScreenY(points[i + 1].y));
    if (d < 10) {
      const newPt = { x: toDataX(mx), y: Math.max(0, toDataY(my)), label: "WAYPOINT", hasDot: true };
      points.splice(i + 1, 0, newPt);
      activeTarget = { type: 'point', idx: i + 1 };
      labelInput.value = newPt.label;
      labelInput.focus();
      draw();
      return;
    }
  }
});

window.addEventListener('mousemove', (e) => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const dataX = toDataX(mx);
  const dataY = toDataY(my);

  // Moving a vertex (dot or corner)
  if (selectedPointIdx !== null) {
    const idx = selectedPointIdx;
    const minX = idx > 0 ? points[idx - 1].x + 0.1 : X_MIN;
    const maxX = idx < points.length - 1 ? points[idx + 1].x - 0.1 : X_MAX;
    points[idx].x = Math.max(minX, Math.min(maxX, dataX));
    points[idx].y = Math.max(0, dataY);
    hoveredTooltip = { x: mx, y: my, text: `T: ${points[idx].x.toFixed(1)}m | Alt: ${points[idx].y.toFixed(1)}k` };
    draw();
    return;
  }

  // Moving a line segment
  if (selectedSegmentIdx !== null) {
    const dx = dataX - dragStart.x;
    const dy = dataY - dragStart.y;
    const idx = selectedSegmentIdx;
    const p1 = points[idx], p2 = points[idx + 1];

    if (p1.y + dy >= 0 && p2.y + dy >= 0) {
      const minX = idx > 0 ? points[idx - 1].x + 0.1 : X_MIN;
      const maxX = idx + 2 < points.length ? points[idx + 2].x - 0.1 : X_MAX;
      if (p1.x + dx > minX && p2.x + dx < maxX) {
        p1.x += dx; p1.y += dy;
        p2.x += dx; p2.y += dy;
        dragStart = { x: dataX, y: dataY };
        draw();
      }
    }
    return;
  }

  // Moving FL Label
  if (selectedFlIdx !== null) {
    flLabels[selectedFlIdx].x += dataX - dragStart.x;
    flLabels[selectedFlIdx].y += dataY - dragStart.y;
    dragStart = { x: dataX, y: dataY };
    draw();
    return;
  }

  // Moving/resizing band
  if (selectedBandIdx !== null) {
    const dx = dataX - dragStart.x;
    const b = bands[selectedBandIdx];
    if (bandDragMode === 'move') {
      b.left += dx; b.right += dx;
    } else if (bandDragMode === 'left_edge') {
      if (b.left + dx < b.right - 1.0) b.left += dx;
    } else if (bandDragMode === 'right_edge') {
      if (b.right + dx > b.left + 1.0) b.right += dx;
    }
    dragStart = { x: dataX };
    draw();
    return;
  }

  // Hover detection for vertices
  hoveredVertexIdx = null;
  let cursor = 'default';
  for (let i = 0; i < points.length; i++) {
    if (Math.hypot(toScreenX(points[i].x) - mx, toScreenY(points[i].y) - my) < 12) {
      hoveredVertexIdx = i;
      cursor = 'pointer';
      break;
    }
  }

  if (cursor === 'default') {
    for (let i = 0; i < bands.length; i++) {
      if (Math.abs(dataX - bands[i].left) <= 2.0 || Math.abs(dataX - bands[i].right) <= 2.0) {
        cursor = 'ew-resize'; break;
      }
    }
  }
  cv.style.cursor = cursor;
  draw();
});

window.addEventListener('mouseup', () => {
  selectedPointIdx = null;
  selectedSegmentIdx = null;
  selectedBandIdx = null;
  selectedFlIdx = null;
  bandDragMode = null;
  hoveredTooltip = null;
  draw();
});

labelInput.addEventListener('input', (e) => {
  if (!activeTarget) return;
  if (activeTarget.type === 'point' && points[activeTarget.idx]) {
    points[activeTarget.idx].label = e.target.value;
    if (e.target.value.trim() !== '') {
      points[activeTarget.idx].hasDot = true;
    }
  } else if (activeTarget.type === 'fl' && flLabels[activeTarget.idx]) {
    flLabels[activeTarget.idx].text = e.target.value;
  }
  draw();
});

cv.addEventListener('contextmenu', e => e.preventDefault());

function saveImage() {
  draw(true);
  const a = document.createElement('a');
  a.href = cv.toDataURL('image/png');
  a.download = 'flight_profile.png';
  a.click();
  draw(false);
}

function saveData() {
  const payload = {
    points: points.map(p => ({
      time_min: +p.x.toFixed(2),
      altitude_kft: +p.y.toFixed(2),
      label: p.label,
      hasDot: p.hasDot
    })),
    bands: bands.map(b => ({ left: +b.left.toFixed(2), right: +b.right.toFixed(2) })),
    fl_labels: flLabels.map(f => ({ text: f.text, time_min: +f.x.toFixed(2), altitude_kft: +f.y.toFixed(2) }))
  };
  const blob = new Blob([JSON.stringify(payload, null, 4)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'flight_profile.json';
  a.click();
}

window.addEventListener('keydown', (e) => {
  if (document.activeElement !== labelInput) {
    if (e.key === 'j' || e.key === 'J') {
      saveImage();
    } else if (e.key === 's' || e.key === 'S') {
      saveData();
    }
  }
});

draw();
</script>
</body>
</html>
"""

components.html(html_code, height=800, scrolling=False)
