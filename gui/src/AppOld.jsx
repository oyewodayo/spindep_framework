import { useState, useCallback, useRef, useEffect, useMemo } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Area, AreaChart, Legend
} from "recharts";

// ═══════════════════════════════════════════════════════════════
// DESIGN TOKENS
// ═══════════════════════════════════════════════════════════════
const T = {
  bg0:      "#050810",
  bg1:      "#08101a",
  bg2:      "#0c1624",
  surface:  "#0f1e30",
  panel:    "#122238",
  border:   "#1a2e45",
  borderHi: "#234060",
  blue:     "#4a9eff",
  blueD:    "#1a4a8a",
  blueDim:  "#0d2040",
  teal:     "#2dd4bf",
  tealDim:  "#0a2520",
  amber:    "#fbbf24",
  amberD:   "#78350f",
  amberDim: "#1e1200",
  red:      "#f87171",
  redDim:   "#2a0a0a",
  green:    "#34d399",
  greenDim: "#0a1f17",
  violet:   "#a78bfa",
  violetDim:"#1a1040",
  muted:    "#3a5570",
  dim:      "#2a4060",
  text:     "#b8cfe8",
  textDim:  "#5a7898",
  textHi:   "#dceeff",
  mono:     "'IBM Plex Mono', 'Fira Code', monospace",
  sans:     "'IBM Plex Sans', 'DM Sans', sans-serif",
};

// ═══════════════════════════════════════════════════════════════
// API — all calls go to FastAPI on port 8001
// ═══════════════════════════════════════════════════════════════
const API = "http://localhost:8001";

async function apiRun(mode = "full") {
  const r = await fetch(`${API}/api/run?mode=${mode}`, { method: "POST" });
  return r.json();
}
async function apiPoll(jobId) {
  const r = await fetch(`${API}/api/job/${jobId}`);
  return r.json();
}
async function apiResults(jobId) {
  const r = await fetch(`${API}/api/results/${jobId}`);
  return r.json();
}
async function apiStatus() {
  try {
    const r = await fetch(`${API}/api/status`);
    return r.json();
  } catch { return null; }
}

// ═══════════════════════════════════════════════════════════════
// MOCK FOLDER TREE (visual only — real data comes from API)
// ═══════════════════════════════════════════════════════════════
function makeFolderTree(couplings) {
  const COUPLINGS = couplings || ["gAgA", "gsgs", "gVgV", "gpgp", "gpgs"];
  return {
    name: "datasets/normalized",
    type: "folder",
    children: COUPLINGS.map(c => ({
      name: c,
      type: "folder",
      children: [{ name: "lepton-lepton", type: "folder", children: [] }]
    }))
  };
}

// ═══════════════════════════════════════════════════════════════
// ICONS
// ═══════════════════════════════════════════════════════════════
const I = ({ n, s = 16 }) => {
  const icons = {
    folder:  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>,
    file:    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><polyline points="13 2 13 9 20 9"/></svg>,
    upload:  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>,
    play:    <svg width={s} height={s} viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21"/></svg>,
    chart:   <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
    grid:    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
    table:   <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>,
    check:   <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="20 6 9 17 4 12"/></svg>,
    warn:    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
    error:   <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>,
    info:    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>,
    dl:      <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>,
    atom:    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><circle cx="12" cy="12" r="1.5" fill="currentColor"/><ellipse cx="12" cy="12" rx="10" ry="4"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4" transform="rotate(120 12 12)"/></svg>,
    layers:  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>,
    report:  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
    chevron: <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>,
    chevD:   <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>,
    search:  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>,
    settings:<svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>,
    validate:<svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>,
    close:   <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>,
    copy:    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>,
    scope:   <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="3"/><line x1="2" y1="12" x2="9" y2="12"/><line x1="15" y1="12" x2="22" y2="12"/></svg>,
    wifi:    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>,
    wifiOff: <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><line x1="1" y1="1" x2="23" y2="23"/><path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/><path d="M5 12.55a11 11 0 0 1 5.17-2.39"/><path d="M10.71 5.05A16 16 0 0 1 22.56 9"/><path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>,
  };
  return icons[n] ?? null;
};

// ═══════════════════════════════════════════════════════════════
// GLOBAL CSS
// ═══════════════════════════════════════════════════════════════
const CSS = `
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; background: ${T.bg0}; color: ${T.text}; font-family: ${T.sans}; font-size: 13px; overflow: hidden; }
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: ${T.bg1}; }
::-webkit-scrollbar-thumb { background: ${T.dim}; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: ${T.muted}; }
button { font-family: ${T.sans}; cursor: pointer; }
input, select, textarea { font-family: ${T.sans}; }
.app-shell { display: flex; height: 100vh; width: 100vw; overflow: hidden; }
.sidebar { width: 220px; min-width: 220px; background: ${T.bg1}; border-right: 1px solid ${T.border}; display: flex; flex-direction: column; overflow: hidden; }
.main-area { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.topbar { height: 48px; min-height: 48px; background: ${T.bg1}; border-bottom: 1px solid ${T.border}; display: flex; align-items: center; padding: 0 20px; gap: 12px; }
.workspace { flex: 1; overflow-y: auto; padding: 24px; }
.nav-group { padding: 16px 10px 6px; font-size: 10px; font-weight: 700; color: ${T.muted}; letter-spacing: .12em; text-transform: uppercase; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 8px 14px; border-radius: 6px; cursor: pointer; color: ${T.textDim}; font-size: 13px; font-weight: 400; transition: all .12s; margin: 1px 6px; border: none; background: none; width: calc(100% - 12px); text-align: left; }
.nav-item:hover { background: ${T.bg2}; color: ${T.text}; }
.nav-item.active { background: ${T.blueDim}; color: ${T.blue}; font-weight: 500; }
.nav-item .badge { margin-left: auto; background: ${T.blue}; color: #000; font-size: 9px; font-weight: 700; padding: 1px 5px; border-radius: 8px; font-family: ${T.mono}; }
.panel { background: ${T.panel}; border: 1px solid ${T.border}; border-radius: 10px; overflow: hidden; }
.panel-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid ${T.border}; }
.panel-title { display: flex; align-items: center; gap: 8px; font-weight: 600; color: ${T.textHi}; font-size: 13px; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 14px; border-radius: 6px; border: 1px solid transparent; font-size: 12px; font-weight: 500; cursor: pointer; transition: all .12s; white-space: nowrap; }
.btn-primary { background: ${T.blue}; color: ${T.bg0}; font-weight: 600; border-color: ${T.blue}; }
.btn-primary:hover { background: #69b2ff; box-shadow: 0 0 0 3px ${T.blue}22; }
.btn-ghost { background: transparent; color: ${T.textDim}; border-color: ${T.border}; }
.btn-ghost:hover { background: ${T.bg2}; color: ${T.text}; border-color: ${T.borderHi}; }
.btn-teal { background: ${T.teal}; color: ${T.bg0}; font-weight: 600; border-color: ${T.teal}; }
.btn:disabled { opacity: .35; cursor: not-allowed; pointer-events: none; }
.btn-icon { padding: 6px; }
.input { background: ${T.bg1}; border: 1px solid ${T.border}; color: ${T.text}; border-radius: 6px; padding: 7px 10px; font-size: 12px; transition: border-color .12s; }
.input:focus { outline: none; border-color: ${T.blue}; }
.input::placeholder { color: ${T.muted}; }
.select { background: ${T.bg1}; border: 1px solid ${T.border}; color: ${T.text}; border-radius: 6px; padding: 7px 10px; font-size: 12px; cursor: pointer; appearance: none; }
.label { font-size: 10px; font-weight: 600; color: ${T.textDim}; letter-spacing: .09em; text-transform: uppercase; margin-bottom: 5px; display: block; }
.tag { display: inline-flex; align-items: center; gap: 3px; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 600; font-family: ${T.mono}; letter-spacing: .02em; }
.tag-blue   { background: ${T.blueDim};   color: ${T.blue}; }
.tag-teal   { background: ${T.tealDim};   color: ${T.teal}; }
.tag-amber  { background: ${T.amberDim};  color: ${T.amber}; }
.tag-red    { background: ${T.redDim};    color: ${T.red}; }
.tag-green  { background: ${T.greenDim};  color: ${T.green}; }
.tag-violet { background: ${T.violetDim}; color: ${T.violet}; }
.tag-muted  { background: ${T.dim};       color: ${T.muted}; }
.stat { background: ${T.bg2}; border: 1px solid ${T.border}; border-radius: 8px; padding: 12px 14px; }
.stat-val { font-family: ${T.mono}; font-size: 20px; font-weight: 700; color: ${T.textHi}; line-height: 1; }
.stat-lbl { font-size: 10px; color: ${T.textDim}; text-transform: uppercase; letter-spacing: .09em; margin-top: 5px; }
.data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.data-table th { padding: 8px 12px; text-align: left; font-size: 10px; font-weight: 700; color: ${T.textDim}; text-transform: uppercase; letter-spacing: .09em; border-bottom: 1px solid ${T.border}; white-space: nowrap; }
.data-table td { padding: 9px 12px; border-bottom: 1px solid ${T.border}20; font-family: ${T.mono}; vertical-align: middle; }
.data-table tr:hover td { background: ${T.bg1}; }
.data-table tr:last-child td { border-bottom: none; }
.ftree-item { display: flex; align-items: center; gap: 7px; padding: 4px 6px; border-radius: 4px; cursor: pointer; font-size: 12px; transition: background .1s; }
.ftree-item:hover { background: ${T.bg2}; }
.ftree-item.selected { background: ${T.blueDim}; color: ${T.blue}; }
.drop-zone { border: 2px dashed ${T.border}; border-radius: 10px; padding: 40px 32px; text-align: center; cursor: pointer; transition: all .2s; }
.drop-zone:hover, .drop-zone.drag { border-color: ${T.blue}; background: ${T.blueDim}20; }
.drop-zone.filled { border-color: ${T.teal}; border-style: solid; background: ${T.tealDim}20; }
.prog-bar { height: 2px; background: ${T.border}; border-radius: 1px; overflow: hidden; }
.prog-fill { height: 100%; background: linear-gradient(90deg, ${T.blue}, ${T.teal}); transition: width .3s ease; }
.heat-cell { border-radius: 4px; display: flex; align-items: center; justify-content: center; font-family: ${T.mono}; font-size: 11px; font-weight: 600; cursor: default; transition: transform .1s; }
.heat-cell:hover { transform: scale(1.08); z-index: 1; }
.fade-in { animation: fadeIn .25s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.spin-anim { animation: spin 2s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.search-bar { display: flex; align-items: center; gap: 8px; background: ${T.bg2}; border: 1px solid ${T.border}; border-radius: 6px; padding: 6px 10px; flex: 1; max-width: 380px; }
.search-bar input { background: none; border: none; color: ${T.text}; font-size: 12px; outline: none; flex: 1; }
.search-bar input::placeholder { color: ${T.muted}; }
.split { display: grid; gap: 16px; }
.split-2 { grid-template-columns: 1fr 1fr; }
.split-3 { grid-template-columns: 1fr 1fr 1fr; }
.split-4 { grid-template-columns: repeat(4, 1fr); }
.split-5 { grid-template-columns: repeat(5, 1fr); }
.pipe-step { display: flex; align-items: center; gap: 8px; padding: 10px 14px; border-radius: 8px; border: 1px solid ${T.border}; background: ${T.bg2}; font-size: 12px; }
.pipe-step.done { border-color: ${T.teal}40; }
.pipe-step.running { border-color: ${T.blue}40; background: ${T.blueDim}20; }
.pipe-step.error { border-color: ${T.red}40; background: ${T.redDim}20; }
.code-block { background: ${T.bg0}; border: 1px solid ${T.border}; border-radius: 6px; padding: 12px 16px; font-family: ${T.mono}; font-size: 11px; color: ${T.green}; line-height: 1.8; overflow-x: auto; }
.api-banner { padding: 10px 16px; border-radius: 8px; display: flex; align-items: center; gap: 10px; font-size: 12px; margin-bottom: 16px; }
.api-banner.ok  { background: ${T.tealDim}; border: 1px solid ${T.teal}40; color: ${T.teal}; }
.api-banner.err { background: ${T.redDim};  border: 1px solid ${T.red}40;  color: ${T.red}; }
`;

// ═══════════════════════════════════════════════════════════════
// SHARED COMPONENTS
// ═══════════════════════════════════════════════════════════════
function Stat({ label, value, unit, color, sub }) {
  return (
    <div className="stat">
      <div className="stat-val" style={color ? { color } : {}}>
        {value}
        {unit && <span style={{ fontSize: 11, fontWeight: 400, color: T.textDim, marginLeft: 3 }}>{unit}</span>}
      </div>
      <div className="stat-lbl">{label}</div>
      {sub && <div style={{ fontSize: 10, color: T.muted, marginTop: 3 }}>{sub}</div>}
    </div>
  );
}

function PanelHeader({ title, icon, right, sub }) {
  return (
    <div className="panel-header">
      <div>
        <div className="panel-title">
          {icon && <span style={{ color: T.blue }}><I n={icon} s={14} /></span>}
          {title}
        </div>
        {sub && <div style={{ fontSize: 10, color: T.textDim, marginTop: 2 }}>{sub}</div>}
      </div>
      {right}
    </div>
  );
}

const ChartTooltip = ({ active, payload, label, fmt }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: T.bg1, border: `1px solid ${T.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 11, fontFamily: T.mono }}>
      {label !== undefined && <div style={{ color: T.textDim, marginBottom: 5 }}>λ = 10<sup>{Number(label).toFixed(1)}</sup> m</div>}
      {payload.map(p => (
        <div key={p.name} style={{ color: p.color ?? T.text, marginBottom: 2 }}>
          {p.name}: {fmt ? fmt(p.value) : p.value}
        </div>
      ))}
    </div>
  );
};

function pvalColor(p) { return p < 0.001 ? T.red : p < 0.05 ? T.amber : T.green; }
function sigTag(p) {
  return p < 0.001 ? <span className="tag tag-red">✦✦✦ p &lt; 0.001</span>
       : p < 0.05  ? <span className="tag tag-amber">✦ p &lt; 0.05</span>
       :              <span className="tag tag-teal">ns</span>;
}

function ApiBanner({ online }) {
  return (
    <div className={`api-banner ${online ? "ok" : "err"}`}>
      <I n={online ? "wifi" : "wifiOff"} s={14} />
      {online
        ? "API connected — pipeline will use real data from ~/spindep_framework/datasets"
        : "API offline — start the server: python3 app_server.py (from ~/spindep_framework)"}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// FILE TREE
// ═══════════════════════════════════════════════════════════════
function FileTree({ node, depth = 0, onSelect, selected }) {
  const [open, setOpen] = useState(depth < 2);
  const isFolder = node.type === "folder";
  const isSelected = selected === node.name;
  return (
    <div style={{ paddingLeft: depth * 14 }}>
      <div
        className={`ftree-item${isSelected ? " selected" : ""}`}
        onClick={() => { if (isFolder) setOpen(o => !o); else onSelect?.(node); }}
      >
        <span style={{ color: isFolder ? T.amber : T.blue, flexShrink: 0 }}>
          {isFolder ? <I n="folder" s={13} /> : <I n="file" s={13} />}
        </span>
        <span style={{ color: isFolder ? T.amber : T.text, fontSize: 11.5, fontFamily: isFolder ? T.sans : T.mono, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {node.name}
        </span>
        {!isFolder && node.rows && <span style={{ marginLeft: "auto", fontSize: 10, color: T.muted, fontFamily: T.mono }}>{node.rows}r</span>}
        {isFolder && <span style={{ marginLeft: "auto", color: T.muted }}><I n={open ? "chevD" : "chevron"} s={11} /></span>}
      </div>
      {isFolder && open && node.children?.map((c, i) => (
        <FileTree key={i} node={c} depth={depth + 1} onSelect={onSelect} selected={selected} />
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SECTION 1: INGEST
// ═══════════════════════════════════════════════════════════════
function IngestSection({ onStartRun, apiOnline }) {
  const [ready, setReady] = useState(false);
  const [tree, setTree] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);

  // Show the dataset structure preview from the server
  const loadPreview = async () => {
    try {
        const r = await fetch(`${API}/api/tree`);
        const data = await r.json();
        // API returns the root node directly — use it as-is
        setTree(data);
        setReady(true);
    } catch {
        setTree(makeFolderTree());
        setReady(true);
    }
};

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Dataset Ingest</h2>
        <p style={{ color: T.textDim, fontSize: 13 }}>
          The pipeline reads from
          <span style={{ fontFamily: T.mono, color: T.blue, margin: "0 6px" }}>~/spindep_framework/datasets/normalized/</span>
          on the server. Click <b style={{ color: T.textHi }}>Preview Structure</b> then run the pipeline.
        </p>
      </div>

      <ApiBanner online={apiOnline} />

      <div className="split split-2" style={{ marginBottom: 20, alignItems: "start" }}>
        {/* Drop zone — visual only, real data is server-side */}
        <div>
          <div
            className={`drop-zone${tree ? " filled" : ""}`}
            onClick={loadPreview}
          >
            {tree ? (
              <>
                <div style={{ color: T.teal, marginBottom: 10 }}><I n="check" s={36} /></div>
                <div style={{ fontWeight: 600, color: T.textHi, marginBottom: 4 }}>Dataset structure loaded</div>
                <div style={{ color: T.textDim, fontSize: 12 }}>
                  Reading from server: datasets/normalized/
                </div>
              </>
            ) : (
              <>
                <div style={{ color: T.muted, marginBottom: 12 }}><I n="folder" s={40} /></div>
                <div style={{ fontWeight: 600, color: T.textHi, marginBottom: 6 }}>Click to preview dataset structure</div>
                <div style={{ color: T.textDim, fontSize: 12, marginBottom: 12 }}>
                  Data is read from the server filesystem — no upload needed
                </div>
                <div style={{ fontFamily: T.mono, fontSize: 11, color: T.muted, background: T.bg0, borderRadius: 4, padding: "6px 12px", display: "inline-block" }}>
                  datasets/normalized/<br />
                  ├── gAgA/lepton-lepton/*.csv<br />
                  ├── gsgs/lepton-nucleon/*.csv<br />
                  └── gVgV/nucleon-nucleon/*.csv
                </div>
              </>
            )}
          </div>
          {tree && (
            <div style={{ marginTop: 12, display: "flex", gap: 8 }}>
              <button className="btn btn-ghost btn-icon" onClick={() => { setTree(null); setReady(false); }} title="Clear">
                <I n="close" s={13} />
              </button>
            </div>
          )}
        </div>

        {/* File tree browser */}
        <div className="panel" style={{ maxHeight: 340, overflowY: "auto" }}>
          <PanelHeader title="Dataset Tree" icon="folder" sub={tree ? "datasets/normalized/" : "Click preview to browse"} />
          <div style={{ padding: "8px 6px" }}>
            {tree ? (
              <FileTree node={tree} onSelect={setSelectedFile} selected={selectedFile?.name} />
            ) : (
              <div style={{ padding: 24, textAlign: "center", color: T.muted, fontSize: 12 }}>
                Click the panel on the left to preview
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Always show run buttons — dataset is server-side */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <button
          className="btn btn-primary"
          style={{ padding: "10px 24px" }}
          disabled={!apiOnline}
          onClick={() => onStartRun("full")}
        >
          <I n="play" s={13} /> Run Full Pipeline
        </button>
        <button className="btn btn-ghost" disabled={!apiOnline} onClick={() => onStartRun("validate")}>
          <I n="validate" s={13} /> Validate Only
        </button>
        <button className="btn btn-ghost" disabled={!apiOnline} onClick={() => onStartRun("gaps")}>
          <I n="scope" s={13} /> Gap Analysis Only
        </button>
        <button className="btn btn-ghost" disabled={!apiOnline} onClick={() => onStartRun("atlas")}>
          <I n="layers" s={13} /> Constraint Atlas Only
        </button>
      </div>
      {!apiOnline && (
        <div style={{ marginTop: 10, fontSize: 11, color: T.amber }}>
          ⚠ Start the API server first: <span style={{ fontFamily: T.mono }}>cd ~/spindep_framework && python3 app_server.py</span>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SECTION 2: PIPELINE RUNNER — polls real API
// ═══════════════════════════════════════════════════════════════
function PipelineSection({ mode, jobId, onComplete }) {
  const [log, setLog]         = useState([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus]   = useState("running");
  const logRef = useRef();

  const STEPS = {
    full:     ["Discovering datasets", "Unit audit & conversion", "Matching matter–antimatter pairs", "Computing χ² & asymmetry", "Gap analysis", "Constraint atlas", "Generating report"],
    validate: ["Discovering datasets", "Unit audit & conversion", "Matching matter–antimatter pairs", "Generating validation report"],
    gaps:     ["Discovering datasets", "Scanning λ coverage", "Gap analysis figures"],
    atlas:    ["Discovering datasets", "Constraint atlas plots"],
  };
  const steps = STEPS[mode] ?? STEPS.full;

  useEffect(() => {
    if (!jobId) return;
    let cancelled = false;

    const poll = async () => {
      while (!cancelled) {
        try {
          const job = await apiPoll(jobId);
          if (cancelled) break;

          setLog(job.log || []);
          // Estimate progress from log line count
          const est = Math.min(95, (job.log?.length || 0) * 4);
          setProgress(est);

          setTimeout(() => { logRef.current?.scrollTo(0, logRef.current.scrollHeight); }, 50);

          if (job.status === "done") {
            setProgress(100);
            setStatus("done");
            setTimeout(() => onComplete?.(), 600);
            break;
          }
          if (job.status === "error") {
            setStatus("error");
            break;
          }
        } catch (e) {
          // API temporarily unreachable — keep polling
        }
        await new Promise(r => setTimeout(r, 1000));
      }
    };

    poll();
    return () => { cancelled = true; };
  }, [jobId]);

  const done  = status === "done";
  const error = status === "error";
  const stepIdx = Math.min(Math.floor((progress / 100) * steps.length), steps.length - 1);

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>
          Pipeline: {mode === "full" ? "Full Analysis" : mode === "validate" ? "Validation" : mode === "gaps" ? "Gap Analysis" : "Constraint Atlas"}
        </h2>
        {jobId && (
          <div style={{ fontSize: 10, color: T.muted, fontFamily: T.mono, marginBottom: 8 }}>
            job: {jobId}
          </div>
        )}
        <div className="prog-bar" style={{ height: 4, marginTop: 12, borderRadius: 2 }}>
          <div className="prog-fill" style={{ width: `${progress}%` }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6, fontSize: 11, color: T.textDim }}>
          <span>
            {done ? "Complete" : error ? "Error — check log" : `Running: ${steps[stepIdx]}`}
          </span>
          <span style={{ fontFamily: T.mono }}>{progress.toFixed(0)}%</span>
        </div>
      </div>

      <div className="split split-2" style={{ alignItems: "start" }}>
        {/* Steps */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {steps.map((s, i) => {
            const isDone    = done || i < stepIdx;
            const isRunning = !done && !error && i === stepIdx;
            return (
              <div key={s} className={`pipe-step${isDone ? " done" : isRunning ? " running" : error && i === stepIdx ? " error" : ""}`}>
                <span style={{ color: isDone ? T.teal : isRunning ? T.blue : T.muted, flexShrink: 0 }}>
                  {isDone ? <I n="check" s={14} /> : isRunning
                    ? <span className="spin-anim" style={{ display: "inline-block" }}><I n="atom" s={14} /></span>
                    : <I n="scope" s={14} />}
                </span>
                <span style={{ color: isDone ? T.text : isRunning ? T.textHi : T.muted, fontSize: 12 }}>{s}</span>
                {isDone    && <span className="tag tag-teal"  style={{ marginLeft: "auto", fontSize: 9 }}>done</span>}
                {isRunning && <span className="tag tag-blue"  style={{ marginLeft: "auto", fontSize: 9 }}>running</span>}
              </div>
            );
          })}
        </div>

        {/* Real log output */}
        <div className="panel" style={{ display: "flex", flexDirection: "column" }}>
          <PanelHeader title="Live Log Output" icon="report" sub="Streaming from Python pipeline" />
          <div ref={logRef} style={{ padding: 12, fontFamily: T.mono, fontSize: 11, lineHeight: 1.9, maxHeight: 340, overflowY: "auto", background: T.bg0 }}>
            {log.length === 0 && (
              <div style={{ color: T.muted }}>Waiting for pipeline output…</div>
            )}
            {log.map((line, i) => {
              const col = line.includes("[OK]") || line.includes("OK") ? T.teal
                        : line.includes("[WARN]") || line.includes("WARN") ? T.amber
                        : line.includes("[ERR]") || line.includes("ERROR") || line.includes("error") ? T.red
                        : T.textDim;
              return <div key={i} style={{ color: col }}>{line}</div>;
            })}
            {!done && !error && <div style={{ color: T.blue }}>▌</div>}
          </div>
        </div>
      </div>

      {done && (
        <div style={{ marginTop: 16, padding: "14px 16px", background: T.tealDim, border: `1px solid ${T.teal}40`, borderRadius: 8, display: "flex", alignItems: "center", gap: 10 }}>
          <I n="check" s={18} />
          <span style={{ color: T.teal, fontWeight: 600 }}>Pipeline complete — real results loaded in all tabs</span>
        </div>
      )}
      {error && (
        <div style={{ marginTop: 16, padding: "14px 16px", background: T.redDim, border: `1px solid ${T.red}40`, borderRadius: 8, display: "flex", alignItems: "center", gap: 10 }}>
          <I n="error" s={18} />
          <span style={{ color: T.red, fontWeight: 600 }}>Pipeline error — check the log above for details</span>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SECTION 3: BATCH RESULTS
// ═══════════════════════════════════════════════════════════════
function BatchResultsSection({ pairs }) {
  const [sort, setSort]               = useState({ col: "pval", asc: true });
  const [filter, setFilter]           = useState("");
  const [filterCoupling, setFilterCoupling] = useState("All");
  const [selected, setSelected]       = useState(null);

  const couplings = useMemo(() => [...new Set(pairs.map(p => p.coupling))], [pairs]);

  const sorted = useMemo(() => {
    let list = pairs.filter(p =>
      (filterCoupling === "All" || p.coupling === filterCoupling) &&
      (!filter || p.id?.toLowerCase().includes(filter.toLowerCase()))
    );
    return [...list].sort((a, b) => {
      const v = col => col === "pval" ? a.pval - b.pval
               : col === "meanAbsA" ? a.meanAbsA - b.meanAbsA
               : a.chi2Weighted - b.chi2Weighted;
      return sort.asc ? v(sort.col) : -v(sort.col);
    });
  }, [pairs, sort, filter, filterCoupling]);

  const SortTh = ({ col, label }) => (
    <th style={{ cursor: "pointer", userSelect: "none" }}
        onClick={() => setSort(s => ({ col, asc: s.col === col ? !s.asc : true }))}>
      {label} {sort.col === col ? (sort.asc ? "↑" : "↓") : ""}
    </th>
  );

  const sig  = pairs.filter(p => p.pval < 0.05).length;
  const hSig = pairs.filter(p => p.pval < 0.001).length;

  if (pairs.length === 0) {
    return (
      <div className="fade-in" style={{ textAlign: "center", padding: 60, color: T.muted }}>
        <I n="table" s={40} />
        <div style={{ marginTop: 16, fontSize: 14, fontWeight: 600, color: T.textDim }}>No results yet</div>
        <div style={{ marginTop: 8, fontSize: 12 }}>Run the pipeline from the Ingest tab to load real data</div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div className="split split-4" style={{ marginBottom: 18 }}>
        <Stat label="Total pairs"    value={pairs.length} />
        <Stat label="p < 0.05"       value={sig}  color={T.amber} sub="significant" />
        <Stat label="p < 0.001"      value={hSig} color={T.red}   sub="highly significant" />
        <Stat label="Coupling types" value={couplings.length} color={T.teal} />
      </div>

      <div style={{ display: "flex", gap: 10, marginBottom: 14, alignItems: "center" }}>
        <div className="search-bar">
          <I n="search" s={13} />
          <input placeholder="Filter by coupling, potential, sector…" value={filter} onChange={e => setFilter(e.target.value)} />
        </div>
        <select className="select" value={filterCoupling} onChange={e => setFilterCoupling(e.target.value)}>
          <option>All</option>
          {couplings.map(c => <option key={c}>{c}</option>)}
        </select>
        <button className="btn btn-ghost" style={{ marginLeft: "auto" }}>
          <I n="dl" s={12} /> Export CSV
        </button>
        <button className="btn btn-ghost">
          <I n="dl" s={12} /> Export LaTeX
        </button>
      </div>

      <div className="panel" style={{ marginBottom: selected ? 16 : 0 }}>
        <div style={{ overflowX: "auto", maxHeight: 420, overflowY: "auto" }}>
          <table className="data-table">
            <thead style={{ position: "sticky", top: 0, background: T.panel }}>
              <tr>
                <th>Pair ID</th>
                <th>Coupling</th>
                <th>Potential</th>
                <th>Sectors</th>
                <SortTh col="meanAbsA"     label="|Aα| mean" />
                <SortTh col="chi2Weighted" label="χ² (w)" />
                <th>dof</th>
                <SortTh col="pval" label="p-value" />
                <th>Sig.</th>
                <th>λ range (m)</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map(p => (
                <tr key={p.id} onClick={() => setSelected(selected?.id === p.id ? null : p)} style={{ cursor: "pointer" }}>
                  <td style={{ color: T.textDim, maxWidth: 140, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{p.id}</td>
                  <td><span className="tag tag-blue">{p.coupling}</span></td>
                  <td><span className="tag tag-violet">{p.potential}</span></td>
                  <td style={{ color: T.textDim }}>{p.secM} × {p.secA}</td>
                  <td style={{ color: p.meanAbsA > 0.5 ? T.red : p.meanAbsA > 0.2 ? T.amber : T.text }}>{p.meanAbsA?.toFixed(4)}</td>
                  <td>{p.chi2Weighted?.toFixed(1)}</td>
                  <td style={{ color: T.textDim }}>{p.dof}</td>
                  <td style={{ color: pvalColor(p.pval) }}>{p.pval < 1e-9 ? "<10⁻⁹" : p.pval?.toExponential(2)}</td>
                  <td>{sigTag(p.pval)}</td>
                  <td style={{ color: T.textDim, fontSize: 10 }}>
                    {p.lambdaMin?.toExponential(1)}–{p.lambdaMax?.toExponential(1)}
                  </td>
                  <td>
                    <button className="btn btn-ghost btn-icon" style={{ padding: "3px 6px" }}>
                      <I n="chevron" s={11} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selected && <PairDetail pair={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// PAIR DETAIL
// ═══════════════════════════════════════════════════════════════
function PairDetail({ pair, onClose }) {
  const pts = pair.points || [];

  return (
    <div className="panel fade-in">
      <PanelHeader
        title={pair.id}
        icon="chart"
        right={<button className="btn btn-ghost btn-icon" onClick={onClose}><I n="close" s={14} /></button>}
      />
      <div style={{ padding: 16 }}>
        <div className="split split-5" style={{ marginBottom: 16 }}>
          <Stat label="Mean |Aα|"    value={pair.meanAbsA?.toFixed(4)}     color={pair.meanAbsA > 0.5 ? T.red : pair.meanAbsA > 0.2 ? T.amber : T.teal} />
          <Stat label="χ² weighted"  value={pair.chi2Weighted?.toFixed(0)} />
          <Stat label="χ² uniform"   value={pair.chi2Uniform?.toFixed(0)}  />
          <Stat label="p-value"      value={pair.pval < 1e-9 ? "<10⁻⁹" : pair.pval?.toExponential(2)} color={pvalColor(pair.pval)} />
          <Stat label="σ matter avg" value={pair.sigmaM?.toFixed(1)} unit="%" />
        </div>

        <div className="split split-2">
          <div>
            <div style={{ fontSize: 11, color: T.textDim, marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".08em" }}>
              Coupling Upper Bounds (log–log)
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={pts} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                <XAxis dataKey="logLam" tickFormatter={v => `10^${v.toFixed(0)}`} tick={{ fill: T.textDim, fontSize: 9, fontFamily: T.mono }} />
                <YAxis tickFormatter={v => `10^${v.toFixed(0)}`} tick={{ fill: T.textDim, fontSize: 9, fontFamily: T.mono }} width={48} />
                <Tooltip content={<ChartTooltip fmt={v => `10^${v.toFixed(2)}`} />} />
                <Line type="monotone" dataKey="logGm" name={`Matter (${pair.secM})`}       stroke={T.blue}  strokeWidth={1.8} dot={false} />
                <Line type="monotone" dataKey="logGa" name={`Antimatter (${pair.secA})`}   stroke={T.amber} strokeWidth={1.8} dot={false} strokeDasharray="5 3" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div>
            <div style={{ fontSize: 11, color: T.textDim, marginBottom: 8, fontWeight: 600, textTransform: "uppercase", letterSpacing: ".08em" }}>
              CPT Asymmetry Aα
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={pts} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                <XAxis dataKey="logLam" tickFormatter={v => `10^${v.toFixed(0)}`} tick={{ fill: T.textDim, fontSize: 9, fontFamily: T.mono }} />
                <YAxis domain={[-1.1, 1.1]} tick={{ fill: T.textDim, fontSize: 9, fontFamily: T.mono }} width={36} />
                <Tooltip content={<ChartTooltip fmt={v => v.toFixed(4)} />} />
                <ReferenceLine y={0} stroke={T.muted} strokeDasharray="4 4" />
                <defs>
                  <linearGradient id={`gP_${pair.id?.replace(/[^a-z0-9]/gi,"_")}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%"   stopColor={T.blue} stopOpacity={0.4} />
                    <stop offset="100%" stopColor={T.blue} stopOpacity={0}   />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="A" name="Aα" stroke={T.blue}
                  fill={`url(#gP_${pair.id?.replace(/[^a-z0-9]/gi,"_")})`} strokeWidth={1.5} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SECTION 4: GAP ANALYSIS (derived from real pairs)
// ═══════════════════════════════════════════════════════════════
function GapAnalysisSection({ pairs }) {
  const [hover, setHover] = useState(null);

  const couplings  = useMemo(() => [...new Set(pairs.map(p => p.coupling))].sort(), [pairs]);
  const potentials = useMemo(() => [...new Set(pairs.map(p => p.potential))].sort(), [pairs]);

  const matrix = useMemo(() => couplings.map(c => ({
    coupling: c,
    coverage: potentials.map(pot => ({
      potential:   pot,
      paired:      pairs.filter(p => p.coupling === c && p.potential === pot).length,
      matter:      pairs.filter(p => p.coupling === c && p.potential === pot).length,
      antimatter:  pairs.filter(p => p.coupling === c && p.potential === pot).length,
    }))
  })), [pairs, couplings, potentials]);

  const maxPairs = Math.max(1, ...matrix.flatMap(r => r.coverage.map(c => c.paired)));

  function cellColor(val, max) {
    if (val === 0) return T.bg0;
    return `rgba(74,158,255,${0.15 + (val / max) * 0.7})`;
  }

  if (pairs.length === 0) {
    return (
      <div className="fade-in" style={{ textAlign: "center", padding: 60, color: T.muted }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: T.textDim }}>Run the pipeline first to see gap analysis</div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Gap Analysis</h2>
        <p style={{ color: T.textDim, fontSize: 13 }}>Coverage matrix built from real pipeline results.</p>
      </div>

      <div className="panel" style={{ marginBottom: 16 }}>
        <PanelHeader title="Coverage Matrix: Matched Pairs per (Coupling × Potential)" icon="grid"
          sub="Number of matched matter–antimatter pairs. Dark = no experimental data." />
        <div style={{ padding: 20, overflowX: "auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: `120px repeat(${potentials.length}, 1fr)`, gap: 4, minWidth: 400 }}>
            <div />
            {potentials.map(p => (
              <div key={p} style={{ textAlign: "center", fontSize: 10, color: T.textDim, fontFamily: T.mono, fontWeight: 600, padding: "4px 0" }}>{p}</div>
            ))}
            {matrix.map(row => (
              <React.Fragment key={row.coupling}>
                <div style={{ display: "flex", alignItems: "center", fontSize: 11, fontFamily: T.mono, color: T.blue, fontWeight: 600, paddingRight: 8 }}>{row.coupling}</div>
                {row.coverage.map((cell, j) => (
                  <div key={j} className="heat-cell"
                    style={{ height: 44, background: cellColor(cell.paired, maxPairs), border: `1px solid ${T.border}`, color: cell.paired > 0 ? T.textHi : T.muted }}
                    onMouseEnter={() => setHover({ ...cell, coupling: row.coupling })}
                    onMouseLeave={() => setHover(null)}>
                    {cell.paired > 0 ? cell.paired : <I n="close" s={10} />}
                  </div>
                ))}
              </React.Fragment>
            ))}
          </div>
          {hover && (
            <div style={{ marginTop: 12, padding: "8px 14px", background: T.bg2, border: `1px solid ${T.border}`, borderRadius: 6, fontSize: 12, display: "inline-flex", gap: 20 }}>
              <span style={{ fontFamily: T.mono, color: T.blue }}>{hover.coupling} · {hover.potential}</span>
              <span>Pairs: <b style={{ color: hover.paired > 0 ? T.teal : T.red }}>{hover.paired}</b></span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Need React for React.Fragment
import React from "react";

// ═══════════════════════════════════════════════════════════════
// SECTION 5: CONSTRAINT ATLAS
// ═══════════════════════════════════════════════════════════════
function AtlasSection({ pairs }) {
  const couplings  = useMemo(() => [...new Set(pairs.map(p => p.coupling))].sort(), [pairs]);
  const potentials = useMemo(() => [...new Set(pairs.map(p => p.potential))].sort(), [pairs]);

  const [selectedCoupling,  setSelectedCoupling]  = useState(null);
  const [selectedPotential, setSelectedPotential] = useState(null);

  useEffect(() => {
    if (couplings.length  && !selectedCoupling)  setSelectedCoupling(couplings[0]);
    if (potentials.length && !selectedPotential) setSelectedPotential(potentials[0]);
  }, [couplings, potentials]);

  const pairsForView = pairs.filter(p => p.coupling === selectedCoupling && p.potential === selectedPotential);

  if (pairs.length === 0) {
    return (
      <div className="fade-in" style={{ textAlign: "center", padding: 60, color: T.muted }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: T.textDim }}>Run the pipeline first to see the constraint atlas</div>
      </div>
    );
  }

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 18 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Constraint Atlas</h2>
        <p style={{ color: T.textDim, fontSize: 13 }}>Real coupling upper bounds from your experimental datasets.</p>
      </div>

      <div style={{ display: "flex", gap: 10, marginBottom: 18, flexWrap: "wrap", alignItems: "center" }}>
        <div>
          <label className="label">Coupling</label>
          <div style={{ display: "flex", gap: 6 }}>
            {couplings.map(c => (
              <button key={c} className={`btn ${selectedCoupling === c ? "btn-primary" : "btn-ghost"}`}
                style={{ fontSize: 11, fontFamily: T.mono }} onClick={() => setSelectedCoupling(c)}>{c}</button>
            ))}
          </div>
        </div>
        <div style={{ width: 1, height: 32, background: T.border, margin: "0 4px" }} />
        <div>
          <label className="label">Potential</label>
          <div style={{ display: "flex", gap: 6 }}>
            {potentials.map(p => (
              <button key={p} className={`btn ${selectedPotential === p ? "btn-primary" : "btn-ghost"}`}
                style={{ fontSize: 11, fontFamily: T.mono }} onClick={() => setSelectedPotential(p)}>{p}</button>
            ))}
          </div>
        </div>
      </div>

      {pairsForView.length > 0 ? (
        <div className="panel">
          <PanelHeader
            title={`${selectedCoupling} · ${selectedPotential} — Constraint curves`}
            icon="chart"
            sub="Upper bounds on coupling |g| vs interaction range λ"
          />
          <div style={{ padding: "12px 4px 8px" }}>
            <ResponsiveContainer width="100%" height={340}>
              <LineChart margin={{ top: 8, right: 20, left: 8, bottom: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={T.border} />
                <XAxis type="number" dataKey="logLam" domain={[-12, 6]}
                  tickFormatter={v => `10^${v.toFixed(0)}`}
                  tick={{ fill: T.textDim, fontSize: 9, fontFamily: T.mono }}
                  label={{ value: "Interaction range λ (m)", position: "insideBottom", offset: -8, fill: T.muted, fontSize: 11 }} />
                <YAxis type="number"
                  tickFormatter={v => `10^${v.toFixed(0)}`}
                  tick={{ fill: T.textDim, fontSize: 9, fontFamily: T.mono }} width={54}
                  label={{ value: "Coupling |g|", angle: -90, position: "insideLeft", fill: T.muted, fontSize: 11 }} />
                <Tooltip content={<ChartTooltip fmt={v => `10^(${v.toFixed(2)})`} />} />
                <Legend wrapperStyle={{ fontSize: 10, color: T.textDim, paddingTop: 8 }} />
                {pairsForView.map((p, i) => [
                  <Line key={`m${i}`} data={p.points} type="monotone" dataKey="logGm"
                    name={`${p.secM} (matter)`}
                    stroke={[T.blue, T.teal, T.violet][i % 3]} strokeWidth={1.8} dot={false} />,
                  <Line key={`a${i}`} data={p.points} type="monotone" dataKey="logGa"
                    name={`${p.secA} (antimatter)`}
                    stroke={[T.amber, T.red, "#ec4899"][i % 3]} strokeWidth={1.8} dot={false} strokeDasharray="6 3" />,
                ])}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      ) : (
        <div style={{ textAlign: "center", padding: 48, color: T.muted }}>
          No data for {selectedCoupling} · {selectedPotential}
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// SECTION 6: EXPORT
// ═══════════════════════════════════════════════════════════════
function ExportSection({ pairs }) {
  const sig = pairs.filter(p => p.pval < 0.05);
  const [copied, setCopied] = useState(null);

  const copy = (key, text) => {
    navigator.clipboard.writeText(text).catch(() => {});
    setCopied(key);
    setTimeout(() => setCopied(null), 1600);
  };

  const latexTable = `\\begin{table}[h]
\\centering
\\caption{CPT Asymmetry Test Results}
\\begin{tabular}{lllccc}
\\hline
Coupling & Potential & Sectors & $\\langle|A_\\alpha|\\rangle$ & $\\chi^2$ & $p$-value \\\\
\\hline
${sig.slice(0, 8).map(p =>
  `${p.coupling} & ${p.potential} & $${p.secM} \\times \\bar{${p.secA}}$ & ${p.meanAbsA?.toFixed(3)} & ${p.chi2Weighted?.toFixed(0)} & ${p.pval?.toExponential(1)} \\\\`
).join("\n")}
\\hline
\\end{tabular}
\\end{table}`;

  const outputs = [
    { label: "PDF Report",           icon: "report",   desc: "Full analysis report with all plots and tables",         size: "~4 MB",  tag: "pdf"  },
    { label: "Summary CSV",          icon: "table",    desc: "All pair results: χ², p-values, |Aα|, lambda ranges",   size: "~18 KB", tag: "csv"  },
    { label: "Asymmetry plots",      icon: "chart",    desc: "Per-pair coupling and asymmetry figures (PNG 300 DPI)",  size: "~12 MB", tag: "zip"  },
    { label: "Constraint atlas",     icon: "layers",   desc: "All atlas figures, one per coupling × potential",        size: "~8 MB",  tag: "zip"  },
    { label: "Gap analysis figures", icon: "scope",    desc: "Coverage matrix, λ-space gap plot",                     size: "~1 MB",  tag: "zip"  },
    { label: "LaTeX tables",         icon: "copy",     desc: "Publication-ready .tex tables for significant results",  size: "~6 KB",  tag: "tex"  },
    { label: "HDF5 data archive",    icon: "dl",       desc: "All interpolated g(λ) and A_α(λ) arrays",               size: "~22 MB", tag: "h5"   },
    { label: "YAML config used",     icon: "settings", desc: "Reproducibility: exact config that produced this run",  size: "<1 KB",  tag: "yaml" },
  ];

  return (
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ color: T.textHi, fontSize: 18, fontWeight: 600, marginBottom: 4 }}>Export & Report</h2>
        <p style={{ color: T.textDim, fontSize: 13 }}>
          Results are written to <span style={{ fontFamily: T.mono, color: T.blue }}>~/spindep_framework/results/</span> on the server after each run.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 20 }}>
        {outputs.map(o => (
          <div key={o.label} className="panel" style={{ display: "flex", alignItems: "center", padding: 0 }}>
            <div style={{ padding: "14px 14px 14px 16px", display: "flex", alignItems: "center", gap: 12, flex: 1 }}>
              <span style={{ color: T.blue, flexShrink: 0 }}><I n={o.icon} s={18} /></span>
              <div>
                <div style={{ fontWeight: 600, color: T.textHi, fontSize: 13, marginBottom: 2 }}>{o.label}</div>
                <div style={{ fontSize: 11, color: T.textDim }}>{o.desc}</div>
              </div>
            </div>
            <div style={{ padding: "0 14px", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6, flexShrink: 0 }}>
              <span className="tag tag-muted" style={{ fontFamily: T.mono }}>{o.size}</span>
              <button className="btn btn-ghost" style={{ fontSize: 11, padding: "4px 10px" }}>
                <I n="dl" s={11} /> .{o.tag}
              </button>
            </div>
          </div>
        ))}
      </div>

      {sig.length > 0 && (
        <div className="panel">
          <PanelHeader title="LaTeX Table (significant results)" icon="copy"
            right={
              <button className="btn btn-ghost" style={{ fontSize: 11 }} onClick={() => copy("latex", latexTable)}>
                {copied === "latex" ? <><I n="check" s={12} /> Copied</> : <><I n="copy" s={12} /> Copy</>}
              </button>
            }
          />
          <pre className="code-block" style={{ margin: 0, borderRadius: "0 0 10px 10px", maxHeight: 220, overflowY: "auto", fontSize: 11 }}>
            {latexTable}
          </pre>
        </div>
      )}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════
// ROOT APP
// ═══════════════════════════════════════════════════════════════
export default function App() {
  const [page,          setPage]          = useState("ingest");
  const [pipelineMode,  setPipelineMode]  = useState(null);
  const [jobId,         setJobId]         = useState(null);
  const [resultsReady,  setResultsReady]  = useState(false);
  const [pairs,         setPairs]         = useState([]);       // ← real data, starts empty
  const [apiOnline,     setApiOnline]     = useState(false);

  // Inject CSS
  useEffect(() => {
    const s = document.createElement("style");
    s.textContent = CSS;
    document.head.appendChild(s);
    return () => document.head.removeChild(s);
  }, []);

  // Poll API health every 5 s
  useEffect(() => {
    const check = async () => {
      const r = await apiStatus();
      setApiOnline(!!r);
    };
    check();
    const t = setInterval(check, 5000);
    return () => clearInterval(t);
  }, []);

  // Start a real pipeline run
  const startRun = useCallback(async (mode) => {
    setPipelineMode(mode);
    setPage("pipeline");
    try {
      const { job_id } = await apiRun(mode);
      setJobId(job_id);
    } catch {
      console.error("Could not reach API — is app_server.py running on port 8001?");
    }
  }, []);

  // Called by PipelineSection when the job finishes
  const handlePipelineComplete = useCallback(async () => {
    if (!jobId) return;
    try {
      const data = await apiResults(jobId);
      if (data?.pairs?.length) {
        setPairs(data.pairs);
        setResultsReady(true);
        setTimeout(() => setPage("batch"), 800);
      }
    } catch (e) {
      console.error("Failed to fetch results:", e);
    }
  }, [jobId]);

  const NAV = [
    { id: "ingest",     label: "Ingest",             icon: "upload",   group: "Data" },
    { id: "pipeline",   label: "Pipeline Runner",    icon: "play",     group: "Data" },
    { id: "batch",      label: "Batch Results",      icon: "table",    group: "Analysis", badge: resultsReady ? pairs.length : null },
    { id: "pairs",      label: "Per-Pair Plots",     icon: "chart",    group: "Analysis" },
    { id: "atlas",      label: "Constraint Atlas",   icon: "layers",   group: "Analysis" },
    { id: "gaps",       label: "Gap Analysis",       icon: "scope",    group: "Analysis" },
    { id: "export",     label: "Export & Report",    icon: "report",   group: "Output" },
  ];

  const groups = [...new Set(NAV.map(n => n.group))];
  const sig    = pairs.filter(p => p.pval < 0.05).length;

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────── */}
      <div className="sidebar">
        <div style={{ padding: "14px 14px 12px", borderBottom: `1px solid ${T.border}`, display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 7, background: `linear-gradient(135deg, ${T.blue}, #1a6ac8)`, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", flexShrink: 0 }}>
            <I n="atom" s={15} />
          </div>
          <div>
            <div style={{ fontFamily: T.mono, fontWeight: 700, color: T.textHi, fontSize: 13, letterSpacing: ".06em" }}>SPINDEP</div>
            <div style={{ fontSize: 9, color: T.muted, letterSpacing: ".08em", marginTop: -1 }}>CPT ANALYSIS PLATFORM</div>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
          {groups.map(g => (
            <div key={g}>
              <div className="nav-group">{g}</div>
              {NAV.filter(n => n.group === g).map(n => (
                <button key={n.id} className={`nav-item${page === n.id ? " active" : ""}`} onClick={() => setPage(n.id)}>
                  <I n={n.icon} s={14} />
                  {n.label}
                  {n.badge != null && <span className="badge">{n.badge}</span>}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div style={{ padding: "12px 14px", borderTop: `1px solid ${T.border}`, fontSize: 11 }}>
          {/* API status indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}>
            <span style={{ color: apiOnline ? T.teal : T.red }}>
              <I n={apiOnline ? "wifi" : "wifiOff"} s={11} />
            </span>
            <span style={{ color: apiOnline ? T.teal : T.red, fontSize: 10 }}>
              API {apiOnline ? "online" : "offline"}
            </span>
          </div>

          {resultsReady ? (
            <>
              <div style={{ color: T.teal, fontWeight: 600, marginBottom: 4 }}>
                <I n="check" s={11} /> Analysis complete
              </div>
              <div style={{ color: T.textDim }}>{pairs.length} pairs · {sig} significant</div>
            </>
          ) : (
            <div style={{ color: T.muted }}>No active analysis</div>
          )}
          <div style={{ marginTop: 8, fontSize: 10, color: T.dim }}>spin CLI v2.0 · Python 3.9+</div>
        </div>
      </div>

      {/* ── Main ────────────────────── */}
      <div className="main-area">
        <div className="topbar">
          <div style={{ fontWeight: 600, color: T.textHi, fontSize: 14 }}>
            {NAV.find(n => n.id === page)?.label}
          </div>
          <div style={{ flex: 1 }} />
          {resultsReady && (
            <>
              <span className="tag tag-blue"  style={{ fontFamily: T.mono }}>{pairs.length} pairs</span>
              <span className="tag tag-red"   style={{ fontFamily: T.mono }}>{sig} significant</span>
              <span className="tag tag-teal">Ready</span>
            </>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10, color: apiOnline ? T.teal : T.red, fontFamily: T.mono }}>
            <I n={apiOnline ? "wifi" : "wifiOff"} s={12} />
            {apiOnline ? "API :8001" : "API offline"}
          </div>
        </div>

        <div className="workspace">
          {page === "ingest"   && <IngestSection   onStartRun={startRun} apiOnline={apiOnline} />}
          {page === "pipeline" && <PipelineSection  mode={pipelineMode ?? "full"} jobId={jobId} onComplete={handlePipelineComplete} />}
          {page === "batch"    && <BatchResultsSection pairs={pairs} />}
          {page === "pairs"    && <BatchResultsSection pairs={pairs} />}
          {page === "atlas"    && <AtlasSection     pairs={pairs} />}
          {page === "gaps"     && <GapAnalysisSection pairs={pairs} />}
          {page === "export"   && <ExportSection    pairs={pairs} />}
        </div>
      </div>
    </div>
  );
}