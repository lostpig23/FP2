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
    border: 1px solid #7eaac7;
    border-radius: 4px;
    cursor: default;
  }
  #editor-bar {
    margin-top: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  #label-input {
    flex-grow: 1;
    min-width: 180px;
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
  .input-control {
    display: flex;
    align-items: center;
    gap: 6px;
    font-weight: bold;
    font-size: 13px;
    color: #17557d;
    white-space: nowrap;
  }
  .num-input {
    width: 65px;
    padding: 7px 8px;
    font-size: 13.5px;
    font-weight: 600;
    color: #17557d;
    border: 1px solid #a0b8cc;
    border-radius: 4px;
    outline: none;
    text-align: center;
  }
  .num-input:focus {
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
  .btn-r { background: #003a70; }
  .btn-r:hover { background: #002244; }
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
  <canvas id="cv" width="1050" height="570"></canvas>
  <div id="editor-bar">
    <div class="input-control">
      <label for="label-input">Edit Selected:</label>
    </div>
    <input type="text" id="label-input" placeholder="Click any point, title, airport code, or red FL label to edit..." />
    
    <div class="input-control">
      <label for="max-time-input">Max Time:</label>
      <input type="number" id="max-time-input" class="num-input" value="120" min="20" max="1000" step="5" />
    </div>

    <button class="btn btn-r" onclick="spawnRBadge()" title="Spawn Ⓡ Symbol (Hot-key: R)">+ Ⓡ (R)</button>
    <button class="btn btn-alt" onclick="saveImage()">Export Image (J)</button>
    <button class="btn" onclick="saveData()">Export JSON (S)</button>
  </div>
  <div id="instructions">
    <b>Controls:</b><br>
    • <b>Ⓡ (Reposition) Symbol:</b> Press <b>R</b> or click <b>+ Ⓡ (R)</b> to spawn. Drag inside to move | Drag its rim or scroll mouse wheel to resize | Right-click it to delete.<br>
    • <b>Edit & Drag Red FL Text:</b> Click red text directly to edit in the bar below, or drag it anywhere.<br>
    • <b>Edit Header & Airports:</b> Click title ("3.7.2 Profile...") or airport codes (KPDX / KSEA) to edit.<br>
    • <b>Move Gradient Boundaries:</b> Click and drag any of the 4 vertical divider lines.<br>
    • <b>Hide dot (keep bend):</b> Right-click on a blue dot. <b>Revive dot:</b> Double-click invisible bend corner.<br>
    • <b>Delete corner:</b> Shift + Right-click on a corner. <b>Add bend & dot:</b> Double-click on any line segment.<br>
    • <b>Shortcuts:</b> <b>R</b> = Spawn Ⓡ | <b>J</b> = Export PNG image | <b>S</b> = Export JSON data.
  </div>
</div>

<script>
const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const labelInput = document.getElementById('label-input');
const maxTimeInput = document.getElementById('max-time-input');

let userMaxTime = 120.0;
let X_MIN = -2;
let X_MAX = 126.0;
const Y_MIN = -2, Y_MAX = 72;
const PAD = { left: 65, right: 35, top: 48, bottom: 62 };

let headerTitle = "3.7.2 Profile - Session B";
let originAirport = "KPDX";
let destAirport = "KSEA";

function updateXLimits(newMaxTime) {
  userMaxTime = Math.max(20, newMaxTime);
  X_MIN = - (userMaxTime * 0.02);
  X_MAX = userMaxTime + (userMaxTime * 0.05);
}
updateXLimits(120.0);

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

// 4 Draggable Gradient Boundaries (in time minutes)
let dividers = [28.0, 42.0, 72.0, 86.0];

let points = [
  { x: 1.0, y: 0.0, label: "ENGINES RUNNING", hasDot: true },
  { x: 7.0, y: 0.0, label: "180° TURN F/O & CAPT", hasDot: true },
  { x: 12.0, y: 0.0, label: "DELAYED WINGTIPS EXTENSION", hasDot: true },
  { x: 15.0, y: 0.0, label: "HUD TAKEOFF", hasDot: true },
  { x: 23.0, y: 40.0, label: "VSD DEMO", hasDot: true },
  { x: 39.0, y: 40.0, label: "", hasDot: false },
  { x: 41.0, y: 26.0, label: "ILS", hasDot: true },
  { x: 45.0, y: 0.0, label: "", hasDot: false },
  { x: 54.0, y: 0.0, label: "HUD TAKEOFF", hasDot: true },
  { x: 55.0, y: 5.0, label: "ENG FAIL R (SEVERE DAMAGE)", hasDot: true },
  { x: 65.0, y: 36.0, label: "", hasDot: false },
  { x: 82.0, y: 36.0, label: "", hasDot: false },
  { x: 83.0, y: 33.0, label: "RNAV Y (LPV MINIMA)", hasDot: true },
  { x: 91.0, y: 0.0, label: "OEI G/A & M/A", hasDot: true },
  { x: 99.0, y: 5.0, label: "[ ] FUEL IMBALANCE", hasDot: true },
  { x: 104.0, y: 5.0, label: "[ ] WINGTIPS DRIVE FAULT", hasDot: true },
  { x: 106.0, y: 1.5, label: "OEI MANUAL ILS", hasDot: true },
  { x: 116.0, y: 0.0, label: "AFTER LANDING", hasDot: true }
];

let flLabels = [
  { text: "FL 360", x: 23.0, y: 34.0 },
  { text: "FL 360", x: 65.0, y: 34.0 }
];

// Draggable & Resizable R-Badges: { x, y, radius }
let rBadges = [
  { x: 70.0, y: 0.0, radius: 12 },
  { x: 86.0, y: 0.0, radius: 12 }
];

let selectedPointIdx = null;
let selectedSegmentIdx = null;
let selectedDividerIdx = null;
let selectedFlIdx = null;
let selectedRBadgeIdx = null;
let rBadgeDragMode = null; // 'move' or 'resize'
let dragStart = null;
let activeTarget = null;
let hoveredTooltip = null;
let hoveredVertexIdx = null;
let hoveredDividerIdx = null;
let hoveredFlIdx = null;
let hoveredRBadgeIdx = null;
let mousePos = { x: 500, y: 250 };

function calculateTickStep(maxVal) {
  const roughSteps = maxVal / 5;
  if (roughSteps <= 10) return 5;
  if (roughSteps <= 20) return 10;
  if (roughSteps <= 40) return 20;
  if (roughSteps <= 80) return 30;
  return 60;
}

function spawnRBadge(atCursor = false) {
  let spawnX = (dividers[1] + dividers[2]) / 2;
  let spawnY = 20.0;
  if (atCursor && mousePos) {
    spawnX = toDataX(mousePos.x);
    spawnY = toDataY(mousePos.y);
  }
  rBadges.push({ x: spawnX, y: Math.max(0, spawnY), radius: 12 });
  selectedRBadgeIdx = rBadges.length - 1;
  rBadgeDragMode = 'move';
  dragStart = { x: spawnX, y: spawnY };
  draw();
}

function draw(hideUI = false) {
  ctx.clearRect(0, 0, cv.width, cv.height);

  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, cv.width, cv.height);

  const pL = toScreenX(X_MIN), pR = toScreenX(X_MAX);
  const pT = toScreenY(Y_MAX), pB = toScreenY(Y_MIN);
  const totalH = pB - pT;

  // Title
  ctx.font = "bold 17px sans-serif";
  ctx.fillStyle = (activeTarget && activeTarget.type === 'title') ? "#0e3752" : "#111827";
  ctx.textAlign = "left";
  ctx.fillText(headerTitle, pL, PAD.top - 16);

  if (!hideUI && activeTarget && activeTarget.type === 'title') {
    const textW = ctx.measureText(headerTitle).width;
    ctx.strokeStyle = "#ff4b4b";
    ctx.lineWidth = 1.8;
    ctx.strokeRect(pL - 4, PAD.top - 32, textW + 8, 22);
  }

  // 1. Five Tiered Zones
  const sx1 = toScreenX(dividers[0]);
  const sx2 = toScreenX(dividers[1]);
  const sx3 = toScreenX(dividers[2]);
  const sx4 = toScreenX(dividers[3]);

  ctx.fillStyle = "#8fb7dc";
  ctx.fillRect(pL, pT, Math.max(0, sx1 - pL), totalH);

  ctx.fillStyle = "#b8d5ed";
  ctx.fillRect(sx1, pT, Math.max(0, sx2 - sx1), totalH);

  ctx.fillStyle = "#edf5fb";
  ctx.fillRect(sx2, pT, Math.max(0, sx3 - sx2), totalH);

  ctx.fillStyle = "#b8d5ed";
  ctx.fillRect(sx3, pT, Math.max(0, sx4 - sx3), totalH);

  ctx.fillStyle = "#8fb7dc";
  ctx.fillRect(sx4, pT, Math.max(0, pR - sx4), totalH);

  // 2. Vertical Divider Lines
  dividers.forEach((dVal, i) => {
    const divX = toScreenX(dVal);
    const isHovered = (hoveredDividerIdx === i);
    const isSelected = (selectedDividerIdx === i);

    ctx.strokeStyle = (isHovered || isSelected) ? "#ffffff" : "rgba(255, 255, 255, 0.85)";
    ctx.lineWidth = (isHovered || isSelected) ? 3.0 : 1.8;

    ctx.beginPath();
    ctx.moveTo(divX, pT);
    ctx.lineTo(divX, pB);
    ctx.stroke();
  });

  // 3. Axes & Ticks
  ctx.strokeStyle = "rgba(255, 255, 255, 0.75)";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#1e293b";
  ctx.font = "bold 11px sans-serif";

  const xStep = calculateTickStep(userMaxTime);
  for (let x = 0; x <= userMaxTime + 0.1; x += xStep) {
    const sx = toScreenX(x);
    ctx.beginPath();
    ctx.moveTo(sx, pT); ctx.lineTo(sx, pB);
    ctx.stroke();
    ctx.fillText(x.toString(), sx - 8, pB + 18);
  }
  ctx.fillText("TIME (Mins)", (pL + pR) / 2 - 35, pB + 36);

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

  // Airport Codes
  ctx.font = "bold 14px sans-serif";
  ctx.fillStyle = "#1b8a36";

  ctx.textAlign = "left";
  ctx.fillText(originAirport, pL + 2, pB + 40);
  if (!hideUI && activeTarget && activeTarget.type === 'origin') {
    const w = ctx.measureText(originAirport).width;
    ctx.strokeStyle = "#ff4b4b";
    ctx.lineWidth = 1.8;
    ctx.strokeRect(pL - 2, pB + 26, w + 8, 18);
  }

  ctx.textAlign = "right";
  ctx.fillText(destAirport, pR - 2, pB + 40);
  if (!hideUI && activeTarget && activeTarget.type === 'dest') {
    const w = ctx.measureText(destAirport).width;
    ctx.strokeStyle = "#ff4b4b";
    ctx.lineWidth = 1.8;
    ctx.strokeRect(pR - w - 6, pB + 26, w + 8, 18);
  }

  // 4. Red FL Labels
  ctx.textAlign = "left";
  ctx.font = "bold 13px sans-serif";
  flLabels.forEach((fl, idx) => {
    const sx = toScreenX(fl.x);
    const sy = toScreenY(fl.y);
    const textW = ctx.measureText(fl.text).width;

    ctx.fillStyle = "#d01818";
    ctx.fillText(fl.text, sx, sy);

    if (!hideUI && activeTarget && activeTarget.type === 'fl' && activeTarget.idx === idx) {
      ctx.strokeStyle = "#ff4b4b";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(sx - 3, sy - 14, textW + 6, 18);
    }
  });

  // 5. Flight Profile Path
  if (points.length > 1) {
    ctx.strokeStyle = "#082f4d";
    ctx.lineWidth = 3.0;
    ctx.beginPath();
    ctx.moveTo(toScreenX(points[0].x), toScreenY(points[0].y));
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(toScreenX(points[i].x), toScreenY(points[i].y));
    }
    ctx.stroke();
  }

  // 6. Checkpoints & Labels
  points.forEach((pt, i) => {
    const sx = toScreenX(pt.x);
    const sy = toScreenY(pt.y);

    if (pt.hasDot) {
      ctx.fillStyle = "#004880";
      ctx.beginPath();
      ctx.arc(sx, sy, 5.5, 0, Math.PI * 2);
      ctx.fill();

      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 1.2;
      ctx.stroke();

      if (!hideUI && activeTarget && activeTarget.type === 'point' && activeTarget.idx === i) {
        ctx.strokeStyle = "#ff4b4b";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(sx, sy, 8, 0, Math.PI * 2);
        ctx.stroke();
      }

      if (pt.label) {
        ctx.save();
        ctx.translate(sx, sy - 10);
        ctx.rotate(-Math.PI / 2);
        ctx.fillStyle = "#004075";
        ctx.font = "600 10.5px sans-serif";
        ctx.textAlign = "left";
        ctx.fillText(pt.label, 0, 3.5);
        ctx.restore();
      }
    } else {
      if (!hideUI && (hoveredVertexIdx === i || (activeTarget && activeTarget.type === 'point' && activeTarget.idx === i))) {
        ctx.strokeStyle = "rgba(8, 47, 77, 0.55)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(sx, sy, 6, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
  });

  // 7. Encircled Ⓡ (Reposition) Badges
  rBadges.forEach((rb, idx) => {
    const sx = toScreenX(rb.x);
    const sy = toScreenY(rb.y);
    const r = rb.radius;

    // Outer Circle Fill (White background with crisp navy border)
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.arc(sx, sy, r, 0, Math.PI * 2);
    ctx.fill();

    ctx.strokeStyle = (hoveredRBadgeIdx === idx || selectedRBadgeIdx === idx) ? "#0066cc" : "#082f4d";
    ctx.lineWidth = Math.max(1.8, r * 0.14);
    ctx.stroke();

    // Inner letter 'R'
    ctx.fillStyle = (hoveredRBadgeIdx === idx || selectedRBadgeIdx === idx) ? "#0066cc" : "#082f4d";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = `bold ${Math.round(r * 1.35)}px sans-serif`;
    ctx.fillText("R", sx, sy + 0.5);

    // Selected Resize Handle Indicator
    if (!hideUI && selectedRBadgeIdx === idx) {
      ctx.strokeStyle = "#ff4b4b";
      ctx.lineWidth = 1.5;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      ctx.arc(sx, sy, r + 4, 0, Math.PI * 2);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  });
  ctx.textBaseline = "alphabetic"; // Reset

  // 8. Tooltip HUD
  if (!hideUI && hoveredTooltip) {
    ctx.fillStyle = "rgba(18, 24, 32, 0.90)";
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

maxTimeInput.addEventListener('input', (e) => {
  const val = parseFloat(e.target.value);
  if (!isNaN(val) && val >= 10) {
    updateXLimits(val);
    draw();
  }
});

cv.addEventListener('mousedown', (e) => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const dataX = toDataX(mx);
  const dataY = toDataY(my);

  const pL = toScreenX(X_MIN), pR = toScreenX(X_MAX);
  const pB = toScreenY(Y_MIN);

  // Right-Click handling
  if (e.button === 2) {
    e.preventDefault();
    // 1. Delete R-Badge on right-click
    for (let i = 0; i < rBadges.length; i++) {
      const sx = toScreenX(rBadges[i].x);
      const sy = toScreenY(rBadges[i].y);
      if (Math.hypot(sx - mx, sy - my) <= rBadges[i].radius + 3) {
        rBadges.splice(i, 1);
        draw();
        return;
      }
    }
    // 2. Hide dot / remove corner
    for (let i = 0; i < points.length; i++) {
      if (Math.hypot(toScreenX(points[i].x) - mx, toScreenY(points[i].y) - my) < 12) {
        if (e.shiftKey) {
          if (points.length > 2) {
            points.splice(i, 1);
            activeTarget = null;
            labelInput.value = "";
          }
        } else {
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

  // 1. Check R-Badges (Drag or Rim Resize)
  for (let i = 0; i < rBadges.length; i++) {
    const sx = toScreenX(rBadges[i].x);
    const sy = toScreenY(rBadges[i].y);
    const dist = Math.hypot(sx - mx, sy - my);
    const r = rBadges[i].radius;

    if (Math.abs(dist - r) <= 4) { // Edge resize
      selectedRBadgeIdx = i;
      rBadgeDragMode = 'resize';
      draw();
      return;
    } else if (dist < r) { // Center body drag
      selectedRBadgeIdx = i;
      rBadgeDragMode = 'move';
      dragStart = { x: dataX, y: dataY };
      hoveredTooltip = { x: mx, y: my, text: `Ⓡ Reposition (${rBadges[i].x.toFixed(1)}m, ${rBadges[i].y.toFixed(1)}k)` };
      draw();
      return;
    }
  }

  // 2. Check Red FL Labels
  ctx.font = "bold 13px sans-serif";
  for (let i = 0; i < flLabels.length; i++) {
    const sx = toScreenX(flLabels[i].x), sy = toScreenY(flLabels[i].y);
    const textW = Math.max(40, ctx.measureText(flLabels[i].text).width);
    if (mx >= sx - 6 && mx <= sx + textW + 6 && my >= sy - 16 && my <= sy + 8) {
      selectedFlIdx = i;
      dragStart = { x: dataX, y: dataY };
      activeTarget = { type: 'fl', idx: i };
      labelInput.value = flLabels[i].text;
      labelInput.focus();
      hoveredTooltip = { x: mx, y: my, text: `${flLabels[i].text} (${flLabels[i].x.toFixed(1)}m, ${flLabels[i].y.toFixed(1)}k)` };
      draw();
      return;
    }
  }

  // 3. Check Header Title Click
  ctx.font = "bold 17px sans-serif";
  const titleW = ctx.measureText(headerTitle).width;
  if (mx >= pL - 5 && mx <= pL + titleW + 5 && my >= PAD.top - 36 && my <= PAD.top - 10) {
    activeTarget = { type: 'title' };
    labelInput.value = headerTitle;
    labelInput.focus();
    draw();
    return;
  }

  // 4. Check Origin Airport Click (Left)
  ctx.font = "bold 14px sans-serif";
  const origW = ctx.measureText(originAirport).width;
  if (mx >= pL - 5 && mx <= pL + origW + 10 && my >= pB + 22 && my <= pB + 48) {
    activeTarget = { type: 'origin' };
    labelInput.value = originAirport;
    labelInput.focus();
    draw();
    return;
  }

  // 5. Check Destination Airport Click (Right)
  const destW = ctx.measureText(destAirport).width;
  if (mx >= pR - destW - 10 && mx <= pR + 5 && my >= pB + 22 && my <= pB + 48) {
    activeTarget = { type: 'dest' };
    labelInput.value = destAirport;
    labelInput.focus();
    draw();
    return;
  }

  // 6. Check Divider Lines
  for (let i = 0; i < dividers.length; i++) {
    const divScreenX = toScreenX(dividers[i]);
    if (Math.abs(mx - divScreenX) <= 7) {
      selectedDividerIdx = i;
      dragStart = { x: dataX };
      draw();
      return;
    }
  }

  // 7. Check Points / Vertices
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

  // 8. Check Segments
  for (let i = 0; i < points.length - 1; i++) {
    const d = distToSegment(mx, my, toScreenX(points[i].x), toScreenY(points[i].y), toScreenX(points[i + 1].x), toScreenY(points[i + 1].y));
    if (d < 8) {
      selectedSegmentIdx = i;
      dragStart = { x: dataX, y: dataY };
      draw();
      return;
    }
  }
});

cv.addEventListener('dblclick', (e) => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

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

// Mouse Wheel: Dynamic scale for hovered R-Badge
cv.addEventListener('wheel', (e) => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;

  for (let i = 0; i < rBadges.length; i++) {
    const sx = toScreenX(rBadges[i].x);
    const sy = toScreenY(rBadges[i].y);
    if (Math.hypot(sx - mx, sy - my) <= rBadges[i].radius + 6) {
      e.preventDefault();
      const delta = e.deltaY < 0 ? 1 : -1;
      rBadges[i].radius = Math.max(8, Math.min(35, rBadges[i].radius + delta));
      hoveredTooltip = { x: mx, y: my, text: `Size: ${rBadges[i].radius}px` };
      draw();
      return;
    }
  }
}, { passive: false });

window.addEventListener('mousemove', (e) => {
  const rect = cv.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  const dataX = toDataX(mx);
  const dataY = toDataY(my);
  mousePos = { x: mx, y: my };

  // Dragging or Resizing R-Badge
  if (selectedRBadgeIdx !== null) {
    const rb = rBadges[selectedRBadgeIdx];
    if (rBadgeDragMode === 'move') {
      const dx = dataX - dragStart.x;
      const dy = dataY - dragStart.y;
      rb.x = Math.max(0, Math.min(userMaxTime, rb.x + dx));
      rb.y = Math.max(0, Math.min(70, rb.y + dy));
      dragStart = { x: dataX, y: dataY };
      hoveredTooltip = { x: mx, y: my, text: `Ⓡ Reposition (${rb.x.toFixed(1)}m, ${rb.y.toFixed(1)}k)` };
    } else if (rBadgeDragMode === 'resize') {
      const sx = toScreenX(rb.x);
      const sy = toScreenY(rb.y);
      rb.radius = Math.max(8, Math.min(35, Math.hypot(sx - mx, sy - my)));
      hoveredTooltip = { x: mx, y: my, text: `Size: ${Math.round(rb.radius)}px` };
    }
    draw();
    return;
  }

  // Dragging Red FL Label
  if (selectedFlIdx !== null) {
    const dx = dataX - dragStart.x;
    const dy = dataY - dragStart.y;
    flLabels[selectedFlIdx].x = Math.max(0, Math.min(userMaxTime, flLabels[selectedFlIdx].x + dx));
    flLabels[selectedFlIdx].y = Math.max(0, Math.min(70, flLabels[selectedFlIdx].y + dy));
    dragStart = { x: dataX, y: dataY };
    hoveredTooltip = { 
      x: mx, 
      y: my, 
      text: `${flLabels[selectedFlIdx].text} (${flLabels[selectedFlIdx].x.toFixed(1)}m, ${flLabels[selectedFlIdx].y.toFixed(1)}k)` 
    };
    draw();
    return;
  }

  // Dragging Boundary Divider
  if (selectedDividerIdx !== null) {
    const idx = selectedDividerIdx;
    const minVal = (idx > 0) ? dividers[idx - 1] + 2.0 : 2.0;
    const maxVal = (idx < dividers.length - 1) ? dividers[idx + 1] - 2.0 : userMaxTime - 2.0;
    dividers[idx] = Math.max(minVal, Math.min(maxVal, dataX));
    hoveredTooltip = { x: mx, y: my, text: `Boundary ${idx + 1}: ${dividers[idx].toFixed(1)} mins` };
    draw();
    return;
  }

  // Dragging Point
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

  // Dragging Segment
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

  // Hover Detection & Cursor
  hoveredVertexIdx = null;
  hoveredDividerIdx = null;
  hoveredFlIdx = null;
  hoveredRBadgeIdx = null;
  let cursor = 'default';

  // Check hover over R-Badges
  for (let i = 0; i < rBadges.length; i++) {
    const sx = toScreenX(rBadges[i].x);
    const sy = toScreenY(rBadges[i].y);
    const dist = Math.hypot(sx - mx, sy - my);
    const r = rBadges[i].radius;
    if (Math.abs(dist - r) <= 4) {
      hoveredRBadgeIdx = i;
      cursor = 'nwse-resize';
      break;
    } else if (dist < r) {
      hoveredRBadgeIdx = i;
      cursor = 'grab';
      break;
    }
  }

  // Check hover over FL labels
  if (cursor === 'default') {
    ctx.font = "bold 13px sans-serif";
    for (let i = 0; i < flLabels.length; i++) {
      const sx = toScreenX(flLabels[i].x), sy = toScreenY(flLabels[i].y);
      const textW = Math.max(40, ctx.measureText(flLabels[i].text).width);
      if (mx >= sx - 6 && mx <= sx + textW + 6 && my >= sy - 16 && my <= sy + 8) {
        hoveredFlIdx = i;
        cursor = 'grab';
        break;
      }
    }
  }

  if (cursor === 'default') {
    for (let i = 0; i < dividers.length; i++) {
      const divScreenX = toScreenX(dividers[i]);
      if (Math.abs(mx - divScreenX) <= 7) {
        hoveredDividerIdx = i;
        cursor = 'col-resize';
        break;
      }
    }
  }

  if (cursor === 'default') {
    for (let i = 0; i < points.length; i++) {
      if (Math.hypot(toScreenX(points[i].x) - mx, toScreenY(points[i].y) - my) < 12) {
        hoveredVertexIdx = i;
        cursor = 'pointer';
        break;
      }
    }
  }

  cv.style.cursor = cursor;
  draw();
});

window.addEventListener('mouseup', () => {
  selectedPointIdx = null;
  selectedSegmentIdx = null;
  selectedDividerIdx = null;
  selectedFlIdx = null;
  selectedRBadgeIdx = null;
  rBadgeDragMode = null;
  hoveredTooltip = null;
  draw();
});

labelInput.addEventListener('input', (e) => {
  if (!activeTarget) return;
  if (activeTarget.type === 'fl' && flLabels[activeTarget.idx]) {
    flLabels[activeTarget.idx].text = e.target.value;
  } else if (activeTarget.type === 'title') {
    headerTitle = e.target.value;
  } else if (activeTarget.type === 'origin') {
    originAirport = e.target.value;
  } else if (activeTarget.type === 'dest') {
    destAirport = e.target.value;
  } else if (activeTarget.type === 'point' && points[activeTarget.idx]) {
    points[activeTarget.idx].label = e.target.value;
    if (e.target.value.trim() !== '') {
      points[activeTarget.idx].hasDot = true;
    }
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
    title: headerTitle,
    origin_airport: originAirport,
    destination_airport: destAirport,
    max_time_min: userMaxTime,
    dividers: dividers.map(d => +d.toFixed(2)),
    r_badges: rBadges.map(b => ({ time_min: +b.x.toFixed(2), altitude_kft: +b.y.toFixed(2), radius_px: Math.round(b.radius) })),
    points: points.map(p => ({
      time_min: +p.x.toFixed(2),
      altitude_kft: +p.y.toFixed(2),
      label: p.label,
      hasDot: p.hasDot
    })),
    fl_labels: flLabels.map(f => ({ text: f.text, time_min: +f.x.toFixed(2), altitude_kft: +f.y.toFixed(2) }))
  };
  const blob = new Blob([JSON.stringify(payload, null, 4)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'flight_profile.json';
  a.click();
}

window.addEventListener('keydown', (e) => {
  if (document.activeElement !== labelInput && document.activeElement !== maxTimeInput) {
    if (e.key === 'r' || e.key === 'R') {
      spawnRBadge(true);
    } else if (e.key === 'j' || e.key === 'J') {
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

components.html(html_code, height=900, scrolling=False)
