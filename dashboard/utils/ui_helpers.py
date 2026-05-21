"""Shared UI helpers — premium dark theme for DocuMind AI."""

import os
import streamlit as st


# ─────────────────────────────────────────────────────────────────────────────
# Premium CSS  (v2 — Glassmorphism + Gradient Mesh)
# ─────────────────────────────────────────────────────────────────────────────

PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ═══════════════════════ VARIABLES ═══════════════════════ */
:root {
  --bg-base:        #04070f;
  --bg-surface:     #080e1c;
  --bg-elevated:    #0d1427;
  --bg-glass:       rgba(13,20,39,0.65);

  --primary:        #6366f1;
  --primary-light:  #818cf8;
  --primary-glow:   rgba(99,102,241,0.22);
  --secondary:      #06b6d4;
  --accent:         #a855f7;
  --success:        #10b981;
  --warning:        #f59e0b;
  --danger:         #ef4444;

  --text-1: #f1f5f9;
  --text-2: #94a3b8;
  --text-3: #475569;

  --border:        rgba(255,255,255,0.055);
  --border-active: rgba(99,102,241,0.45);

  --r-sm: 8px;  --r-md: 12px;  --r-lg: 16px;  --r-xl: 22px;
}

/* ═══════════════════════ HIDE STREAMLIT CHROME ═══════════════════════ */
/* Toolbar, menu, footer */
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu { visibility: hidden !important; height: 0 !important; }
header    { visibility: hidden !important; }
footer    { visibility: hidden !important; }

/* Sidebar collapse << >> double-arrow toggle */
[data-testid="collapsedControl"]          { display: none !important; }
[data-testid="stSidebarCollapseButton"]   { display: none !important; }
button[data-testid="baseButton-header"]   { display: none !important; }
section[data-testid="stSidebar"] > div > button { display: none !important; }

/* ═══════════════════════ RESET / BASE ═══════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"], [class*="st-"] {
  font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
}

/* ═══════════════════════ APP BACKGROUND ═══════════════════════ */
.stApp {
  background-color: var(--bg-base) !important;
  background-image:
    radial-gradient(ellipse 90% 55% at 8% -5%,  rgba(99,102,241,0.07) 0%, transparent 55%),
    radial-gradient(ellipse 70% 45% at 92% 105%, rgba(168,85,247,0.06) 0%, transparent 55%),
    radial-gradient(ellipse 55% 50% at 50% 50%,  rgba(6,182,212,0.025) 0%, transparent 65%);
  color: var(--text-1);
}

/* ═══════════════════════ MAIN CONTAINER ═══════════════════════ */
.main .block-container {
  padding: 1.75rem 2.25rem 3rem !important;
  max-width: 1440px;
}

/* ═══════════════════════ SIDEBAR ═══════════════════════ */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #060a17 0%, #08101f 100%) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* ═══════════════════════ SCROLLBARS ═══════════════════════ */
* { scrollbar-width: thin; scrollbar-color: rgba(99,102,241,0.28) transparent; }
*::-webkit-scrollbar { width: 4px; height: 4px; }
*::-webkit-scrollbar-track { background: transparent; }
*::-webkit-scrollbar-thumb {
  background: rgba(99,102,241,0.28);
  border-radius: 4px;
}
*::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.55); }

/* ═══════════════════════ TYPOGRAPHY ═══════════════════════ */
h1, h2, h3 {
  color: var(--text-1) !important;
  font-weight: 700 !important;
  letter-spacing: -0.025em;
}
p, .stMarkdown p { color: var(--text-2); line-height: 1.65; }
.stCaption, [data-testid="stCaptionContainer"] p {
  color: var(--text-3) !important;
  font-size: 0.78rem !important;
}
label, .stSelectbox label, .stSlider label,
.stTextInput label, .stToggle label {
  color: var(--text-2) !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  margin-bottom: 4px !important;
}

/* ═══════════════════════ BUTTONS ═══════════════════════ */
.stButton > button {
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: var(--r-md) !important;
  font-weight: 600 !important;
  font-size: 0.855rem !important;
  letter-spacing: 0.012em;
  padding: 0.52rem 1.15rem !important;
  transition: all 0.22s cubic-bezier(0.4,0,0.2,1) !important;
  box-shadow: 0 2px 14px rgba(99,102,241,0.28) !important;
  position: relative; overflow: hidden;
}
.stButton > button::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.13) 50%, transparent 100%);
  transform: translateX(-100%);
  transition: transform 0.45s ease;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 7px 28px rgba(99,102,241,0.48) !important;
}
.stButton > button:hover::after { transform: translateX(100%); }
.stButton > button:active { transform: translateY(0) scale(0.98) !important; }

.stButton > button[kind="secondary"] {
  background: rgba(255,255,255,0.035) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-2) !important;
  box-shadow: none !important;
}
.stButton > button[kind="secondary"]:hover {
  background: rgba(99,102,241,0.09) !important;
  border-color: var(--border-active) !important;
  color: var(--primary-light) !important;
  box-shadow: 0 4px 18px rgba(99,102,241,0.14) !important;
  transform: translateY(-1px) !important;
}

/* ═══════════════════════ INPUTS ═══════════════════════ */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
  background: rgba(255,255,255,0.026) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-1) !important;
  font-size: 0.885rem !important;
  padding: 0.62rem 1rem !important;
  transition: all 0.2s ease !important;
  caret-color: var(--primary-light);
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color: var(--text-3) !important; }
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 3px var(--primary-glow) !important;
  background: rgba(99,102,241,0.038) !important;
  outline: none !important;
}

/* ═══════════════════════ SELECTBOX ═══════════════════════ */
.stSelectbox > div > div {
  background: rgba(255,255,255,0.026) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-1) !important;
  transition: border-color 0.2s ease;
}
.stSelectbox > div > div:hover { border-color: rgba(99,102,241,0.35) !important; }
[data-baseweb="select"] > div { background: var(--bg-elevated) !important; }
[data-baseweb="popover"] {
  background: var(--bg-elevated) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  box-shadow: 0 16px 50px rgba(0,0,0,0.55) !important;
}
[data-baseweb="menu"] li { color: var(--text-2) !important; }
[data-baseweb="menu"] li:hover {
  background: rgba(99,102,241,0.1) !important;
  color: var(--text-1) !important;
}

/* ═══════════════════════ SLIDERS ═══════════════════════ */
.stSlider > div > div > div > div { background: var(--primary) !important; }
.stSlider [data-baseweb="slider"] > div:first-child {
  background: rgba(255,255,255,0.07) !important;
}

/* ═══════════════════════ METRICS ═══════════════════════ */
[data-testid="stMetric"] {
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1rem 1.2rem;
  transition: all 0.25s ease;
}
[data-testid="stMetric"]:hover {
  border-color: var(--border-active);
  box-shadow: 0 6px 24px rgba(99,102,241,0.13);
  transform: translateY(-2px);
}
[data-testid="stMetricValue"] {
  color: var(--primary-light) !important;
  font-size: 1.75rem !important;
  font-weight: 800 !important;
  letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
  color: var(--text-3) !important;
  font-size: 0.72rem !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 600;
}

/* ═══════════════════════ TABS ═══════════════════════ */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.018) !important;
  border-bottom: 1px solid var(--border) !important;
  border-radius: var(--r-md) var(--r-md) 0 0;
  padding: 4px 6px 0;
  gap: 2px;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-3) !important;
  border-radius: var(--r-sm) var(--r-sm) 0 0 !important;
  font-size: 0.845rem !important;
  font-weight: 500 !important;
  padding: 9px 18px !important;
  transition: all 0.2s ease !important;
  border: none !important;
}
.stTabs [data-baseweb="tab"]:hover {
  color: var(--text-1) !important;
  background: rgba(255,255,255,0.038) !important;
}
.stTabs [aria-selected="true"] {
  background: rgba(99,102,241,0.11) !important;
  color: var(--primary-light) !important;
  border-bottom: 2px solid var(--primary) !important;
  font-weight: 650 !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: rgba(255,255,255,0.01);
  border: 1px solid var(--border);
  border-top: none;
  border-radius: 0 0 var(--r-md) var(--r-md);
  padding: 1.4rem 1.1rem;
}

/* ═══════════════════════ EXPANDER ═══════════════════════ */
[data-testid="stExpander"] summary {
  background: rgba(255,255,255,0.02) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-2) !important;
  font-size: 0.865rem !important;
  font-weight: 500 !important;
  padding: 0.72rem 1rem !important;
  transition: all 0.2s ease !important;
}
[data-testid="stExpander"] summary:hover {
  border-color: var(--border-active) !important;
  color: var(--text-1) !important;
  background: rgba(99,102,241,0.05) !important;
}
[data-testid="stExpander"] > div:last-child {
  border: 1px solid var(--border) !important;
  border-top: none !important;
  border-radius: 0 0 var(--r-md) var(--r-md) !important;
  padding: 1rem !important;
  background: rgba(255,255,255,0.008) !important;
}

/* ═══════════════════════ FILE UPLOADER ═══════════════════════ */
[data-testid="stFileUploader"] {
  border: 2px dashed rgba(99,102,241,0.22) !important;
  border-radius: var(--r-xl) !important;
  padding: 2.5rem 2rem !important;
  background: rgba(99,102,241,0.025) !important;
  transition: all 0.3s ease !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--primary) !important;
  background: rgba(99,102,241,0.055) !important;
  box-shadow: 0 0 36px rgba(99,102,241,0.1) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] p,
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span {
  color: var(--text-2) !important;
}

/* ═══════════════════════ PROGRESS BAR ═══════════════════════ */
.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--primary), var(--accent)) !important;
  border-radius: 4px !important;
}
.stProgress > div > div > div {
  background: rgba(255,255,255,0.06) !important;
  border-radius: 4px !important;
}

/* ═══════════════════════ ALERTS ═══════════════════════ */
[data-testid="stAlert"] {
  border-radius: var(--r-md) !important;
  font-size: 0.87rem !important;
  border-left-width: 3px !important;
}

/* ═══════════════════════ DIVIDER ═══════════════════════ */
hr {
  border: none !important;
  border-top: 1px solid var(--border) !important;
  margin: 1.2rem 0 !important;
}

/* ═══════════════════════ SPINNER ═══════════════════════ */
.stSpinner > div { border-top-color: var(--primary) !important; }

/* ═══════════════════════ CODE ═══════════════════════ */
.stCode, code, pre {
  background: rgba(0,0,0,0.45) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important;
  color: #a5f3fc !important;
  font-size: 0.82rem !important;
}

/* ═══════════════════════ FORM ═══════════════════════ */
[data-testid="stForm"] {
  background: rgba(255,255,255,0.012);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.1rem 1.2rem;
}

/* ── Send arrow button ── */
[data-testid="stForm"] .stButton > button {
  font-size: 1.3rem !important;
  padding: 0.45rem 0.6rem !important;
  border-radius: var(--r-md) !important;
  min-height: 42px;
  letter-spacing: 0;
}

/* ════════════════════════════════════════════════════
   CUSTOM COMPONENTS
════════════════════════════════════════════════════ */

/* ── Logo ── */
.dm-logo {
  padding: 1.6rem 1rem 0.6rem;
  text-align: center;
}
.dm-logo-icon {
  width: 54px; height: 54px;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  border-radius: 15px;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 10px;
  font-size: 1.55rem;
  box-shadow: 0 4px 22px rgba(99,102,241,0.42);
  animation: logo-pulse 3.5s ease-in-out infinite;
}
@keyframes logo-pulse {
  0%,100% { box-shadow: 0 4px 22px rgba(99,102,241,0.42); }
  50%     { box-shadow: 0 4px 36px rgba(168,85,247,0.7); }
}
.dm-logo-title {
  font-size: 1.12rem; font-weight: 800;
  background: linear-gradient(135deg, #e0e7ff 10%, var(--primary-light) 90%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.03em;
}
.dm-logo-sub {
  font-size: 0.65rem; color: var(--text-3);
  margin-top: 3px; letter-spacing: 0.09em;
  text-transform: uppercase;
}

/* ── Mode badge ── */
.dm-badge {
  display: inline-flex; align-items: center; gap: 6px;
  border-radius: 20px; padding: 4px 13px;
  font-size: 0.7rem; font-weight: 700; letter-spacing: 0.05em;
}
.dm-badge-free {
  background: rgba(16,185,129,0.1); color: #34d399;
  border: 1px solid rgba(16,185,129,0.22);
}
.dm-badge-paid {
  background: rgba(99,102,241,0.1); color: var(--primary-light);
  border: 1px solid rgba(99,102,241,0.22);
}
.dm-badge-dot {
  width: 6px; height: 6px; border-radius: 50%;
  display: inline-block;
  animation: dot-blink 2.2s ease-in-out infinite;
}
.dm-badge-free .dm-badge-dot { background: #34d399; }
.dm-badge-paid .dm-badge-dot { background: var(--primary-light); }
@keyframes dot-blink {
  0%,100% { opacity: 1; }
  50%     { opacity: 0.25; }
}

/* ── Page header ── */
.dm-header {
  display: flex; align-items: center; gap: 13px;
  margin-bottom: 1.4rem;
  padding-bottom: 1.1rem;
  border-bottom: 1px solid var(--border);
}
.dm-header-icon {
  width: 42px; height: 42px;
  background: linear-gradient(135deg, rgba(99,102,241,0.18), rgba(168,85,247,0.18));
  border: 1px solid rgba(99,102,241,0.22);
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.15rem;
  flex-shrink: 0;
}
.dm-header-title {
  font-size: 1.32rem; font-weight: 750;
  color: var(--text-1); letter-spacing: -0.025em;
  line-height: 1.2;
}
.dm-header-sub { font-size: 0.78rem; color: var(--text-3); margin-top: 2px; }

/* ── Stat card ── */
.dm-stat {
  background: rgba(255,255,255,0.018);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.15rem 0.9rem;
  text-align: center;
  position: relative; overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.dm-stat::before {
  content: ''; position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--primary), var(--accent));
  opacity: 0.6; transition: opacity 0.3s;
}
.dm-stat:hover {
  border-color: rgba(99,102,241,0.28);
  transform: translateY(-3px);
  box-shadow: 0 10px 34px rgba(99,102,241,0.13);
}
.dm-stat:hover::before { opacity: 1; }
.dm-stat-icon { font-size: 1.35rem; margin-bottom: 5px; display: block; }
.dm-stat-val {
  font-size: 1.55rem; font-weight: 800;
  background: linear-gradient(135deg, var(--text-1) 20%, var(--primary-light) 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1; margin-bottom: 5px;
}
.dm-stat-lbl {
  font-size: 0.7rem; color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;
}

/* ── Chat messages ── */
.dm-msg {
  display: flex; margin-bottom: 18px;
  animation: msg-in 0.28s cubic-bezier(0.4,0,0.2,1);
}
@keyframes msg-in {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* User */
.dm-msg-user { justify-content: flex-end; }
.dm-msg-user .dm-bubble {
  background: linear-gradient(135deg, #5254a3 0%, #7c3aed 100%);
  color: #fff;
  border-radius: 20px 20px 5px 20px;
  padding: 11px 16px;
  max-width: 70%;
  font-size: 0.9rem; line-height: 1.58;
  box-shadow: 0 4px 18px rgba(99,102,241,0.38);
  word-wrap: break-word;
}
.dm-avatar-user {
  width: 31px; height: 31px; border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--accent));
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 800; color: white;
  margin-left: 9px; flex-shrink: 0; align-self: flex-end;
}

/* AI */
.dm-msg-ai { justify-content: flex-start; align-items: flex-start; }
.dm-avatar-ai {
  width: 31px; height: 31px; border-radius: 50%;
  background: linear-gradient(135deg, #1e1b4b, #312e81);
  border: 1px solid rgba(99,102,241,0.38);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.88rem; margin-right: 9px; flex-shrink: 0; margin-top: 3px;
  box-shadow: 0 0 14px rgba(99,102,241,0.22);
  animation: ai-glow 3s ease-in-out infinite;
}
@keyframes ai-glow {
  0%,100% { box-shadow: 0 0 14px rgba(99,102,241,0.22); }
  50%     { box-shadow: 0 0 22px rgba(99,102,241,0.45); }
}
.dm-msg-ai .dm-bubble {
  background: rgba(13,20,39,0.82);
  border: 1px solid rgba(99,102,241,0.14);
  border-radius: 5px 20px 20px 20px;
  padding: 12px 16px;
  max-width: 76%;
  font-size: 0.9rem; line-height: 1.62;
  color: var(--text-1);
  box-shadow: 0 4px 18px rgba(0,0,0,0.35);
  backdrop-filter: blur(12px);
  word-wrap: break-word;
}
.dm-ai-label {
  display: flex; align-items: center; gap: 8px;
  margin-bottom: 7px;
}
.dm-ai-name {
  font-size: 0.75rem; font-weight: 750;
  color: var(--primary-light); letter-spacing: 0.025em;
}
.dm-sources {
  margin-top: 11px; padding-top: 10px;
  border-top: 1px solid var(--border);
  display: flex; flex-wrap: wrap; gap: 5px;
}
.dm-chip {
  display: inline-flex; align-items: center; gap: 3px;
  background: rgba(6,182,212,0.07);
  border: 1px solid rgba(6,182,212,0.18);
  color: #67e8f9; border-radius: 20px;
  padding: 2px 9px; font-size: 0.7rem; font-weight: 500;
  transition: all 0.2s ease;
}
.dm-chip:hover {
  background: rgba(6,182,212,0.14);
  border-color: rgba(6,182,212,0.38);
}

/* Confidence */
.dm-conf {
  display: inline-flex; align-items: center; gap: 3px;
  border-radius: 20px; padding: 2px 8px;
  font-size: 0.68rem; font-weight: 700; margin-left: auto;
}
.dm-conf-hi { background: rgba(16,185,129,0.1); color: #34d399; border: 1px solid rgba(16,185,129,0.22); }
.dm-conf-md { background: rgba(245,158,11,0.1); color: #fbbf24; border: 1px solid rgba(245,158,11,0.22); }
.dm-conf-lo { background: rgba(239,68,68,0.1);  color: #f87171; border: 1px solid rgba(239,68,68,0.22); }

/* Typing indicator */
.dm-typing {
  display: flex; align-items: center; gap: 4px;
  padding: 11px 14px;
  background: rgba(13,20,39,0.75);
  border: 1px solid rgba(99,102,241,0.14);
  border-radius: 5px 18px 18px 18px;
  width: fit-content; margin-bottom: 18px;
}
.dm-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--primary-light);
  animation: typing 1.3s ease-in-out infinite;
}
.dm-dot:nth-child(2) { animation-delay: 0.22s; }
.dm-dot:nth-child(3) { animation-delay: 0.44s; }
@keyframes typing {
  0%,80%,100% { transform: scale(0.65); opacity: 0.35; }
  40%         { transform: scale(1.15); opacity: 1; }
}

/* Context bar */
.dm-ctx {
  display: flex; align-items: center; gap: 8px;
  background: rgba(99,102,241,0.045);
  border: 1px solid rgba(99,102,241,0.14);
  border-radius: var(--r-md);
  padding: 8px 14px; margin-bottom: 16px; font-size: 0.82rem;
}
.dm-ctx-lbl { color: var(--text-3); }
.dm-ctx-docs { color: #67e8f9; font-weight: 500; }

/* Token count */
.dm-tokens {
  text-align: right; color: var(--text-3);
  font-size: 0.75rem; padding-top: 8px;
}
.dm-tokens b { color: var(--primary-light); font-weight: 600; }

/* ── Document items ── */
.dm-doc {
  display: flex; align-items: center; gap: 11px;
  background: rgba(255,255,255,0.018);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 10px 13px; margin-bottom: 7px;
  transition: all 0.22s ease;
}
.dm-doc:hover {
  border-color: rgba(99,102,241,0.24);
  background: rgba(99,102,241,0.038);
  transform: translateX(2px);
}
.dm-doc-ico {
  width: 34px; height: 34px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; flex-shrink: 0;
}
.dm-ico-pdf  { background: rgba(239,68,68,0.11); }
.dm-ico-docx { background: rgba(59,130,246,0.11); }
.dm-ico-txt  { background: rgba(148,163,184,0.11); }
.dm-ico-csv  { background: rgba(16,185,129,0.11); }
.dm-ico-pptx { background: rgba(245,158,11,0.11); }
.dm-ico-md   { background: rgba(99,102,241,0.11); }
.dm-doc-name {
  font-size: 0.875rem; font-weight: 500;
  color: var(--text-1); flex: 1;
}
.dm-doc-ext {
  font-size: 0.67rem; color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.07em;
  background: rgba(255,255,255,0.05);
  padding: 2px 7px; border-radius: 4px;
}

/* ── Empty state ── */
.dm-empty {
  text-align: center; padding: 3.5rem 2rem;
}
.dm-empty-ico { font-size: 2.8rem; opacity: 0.35; margin-bottom: 12px; }
.dm-empty-ttl {
  font-size: 1rem; font-weight: 650;
  color: var(--text-2); margin-bottom: 5px;
}
.dm-empty-sub { font-size: 0.82rem; color: var(--text-3); }

/* ── Sidebar footer ── */
.dm-footer {
  text-align: center; color: var(--text-3);
  font-size: 0.67rem; padding: 0.6rem 0; line-height: 1.7;
}
.dm-footer b { color: var(--text-2); font-weight: 500; }

/* ── Sidebar nav ── */
.dm-nav-section {
  padding: 4px 12px;
  margin-bottom: 3px;
}

/* ── Section label ── */
.dm-section-lbl {
  font-size: 0.62rem; font-weight: 700;
  color: var(--text-3); letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.7rem 0 0.3rem;
}

/* ── Danger zone ── */
.dm-danger {
  background: rgba(239,68,68,0.04);
  border: 1px solid rgba(239,68,68,0.14);
  border-radius: var(--r-md);
  padding: 1rem;
  margin-top: 0.5rem;
}
.dm-danger-ttl {
  font-size: 0.8rem; font-weight: 700;
  color: #f87171; margin-bottom: 8px;
  display: flex; align-items: center; gap: 6px;
}

/* ── Settings form group ── */
.dm-settings-group {
  background: rgba(255,255,255,0.015);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1.1rem;
  margin-bottom: 1rem;
}
.dm-settings-group-ttl {
  font-size: 0.8rem; font-weight: 700;
  color: var(--text-2); margin-bottom: 10px;
  display: flex; align-items: center; gap: 7px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}

/* ── URL input row ── */
.dm-url-row {
  background: rgba(255,255,255,0.015);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1rem;
  margin-top: 0.5rem;
}
</style>
"""


def apply_premium_theme() -> None:
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)


# Keep old name working
apply_dark_theme = apply_premium_theme


# ─────────────────────────────────────────────────────────────────────────────
# Logo
# ─────────────────────────────────────────────────────────────────────────────

def render_logo(sidebar: bool = True) -> None:
    html = """
    <div class="dm-logo">
      <div class="dm-logo-icon">&#x1F9E0;</div>
      <div class="dm-logo-title">DocuMind AI</div>
      <div class="dm-logo-sub">Intelligent Document Q&amp;A</div>
    </div>
    """
    (st.sidebar if sidebar else st).markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Mode badge
# ─────────────────────────────────────────────────────────────────────────────

def render_mode_badge() -> None:
    free = os.getenv("FREE_MODE", "false").lower() == "true"
    cls   = "dm-badge-free" if free else "dm-badge-paid"
    label = "FREE MODE"     if free else "PAID MODE"
    st.sidebar.markdown(
        f'<div style="text-align:center;margin-bottom:4px">'
        f'<span class="dm-badge {cls}">'
        f'<span class="dm-badge-dot"></span>{label}'
        f'</span></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────

def render_page_header(icon: str, title: str, subtitle: str = "") -> None:
    sub_html = f'<div class="dm-header-sub">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="dm-header">'
        f'  <div class="dm-header-icon">{icon}</div>'
        f'  <div>'
        f'    <div class="dm-header-title">{title}</div>'
        f'    {sub_html}'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Stat card
# ─────────────────────────────────────────────────────────────────────────────

def render_stat_card(value: str, label: str, icon: str = "") -> None:
    icon_html = f'<span class="dm-stat-icon">{icon}</span>' if icon else ""
    st.markdown(
        f'<div class="dm-stat">'
        f'  {icon_html}'
        f'  <div class="dm-stat-val">{value}</div>'
        f'  <div class="dm-stat-lbl">{label}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Chat messages
# ─────────────────────────────────────────────────────────────────────────────

def render_user_message(text: str) -> None:
    st.markdown(
        f'<div class="dm-msg dm-msg-user">'
        f'  <div class="dm-bubble">{text}</div>'
        f'  <div class="dm-avatar-user">You</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_ai_message(text: str, sources: list, confidence: float) -> None:
    conf_cls = "dm-conf-hi" if confidence > 0.7 else ("dm-conf-md" if confidence > 0.4 else "dm-conf-lo")
    conf_pct = f"{int(confidence * 100)}%"

    chips = "".join(
        f'<span class="dm-chip">&#x1F4C4; {s.get("filename", "")}</span>'
        for s in sources[:4]
    )
    sources_html = (
        f'<div class="dm-sources">{chips}</div>' if chips else ""
    )

    st.markdown(
        f'<div class="dm-msg dm-msg-ai">'
        f'  <div class="dm-avatar-ai">&#x1F9E0;</div>'
        f'  <div class="dm-bubble">'
        f'    <div class="dm-ai-label">'
        f'      <span class="dm-ai-name">DocuMind AI</span>'
        f'      <span class="dm-conf {conf_cls}">&#x25CF; {conf_pct}</span>'
        f'    </div>'
        f'    <div>{text}</div>'
        f'    {sources_html}'
        f'  </div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def render_typing_indicator() -> None:
    st.markdown(
        '<div class="dm-msg dm-msg-ai">'
        '  <div class="dm-avatar-ai">&#x1F9E0;</div>'
        '  <div class="dm-typing">'
        '    <div class="dm-dot"></div>'
        '    <div class="dm-dot"></div>'
        '    <div class="dm-dot"></div>'
        '  </div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Context bar
# ─────────────────────────────────────────────────────────────────────────────

def render_context_bar(doc_names: list) -> None:
    names = ", ".join(doc_names[:3])
    more  = f" +{len(doc_names) - 3} more" if len(doc_names) > 3 else ""
    st.markdown(
        f'<div class="dm-ctx">'
        f'  <span class="dm-ctx-lbl">&#x1F4DA; Context:</span>'
        f'  <span class="dm-ctx-docs">{names}{more}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Document list item
# ─────────────────────────────────────────────────────────────────────────────

def render_doc_item(filename: str) -> None:
    from pathlib import Path
    ext = Path(filename).suffix.lower().lstrip(".")
    icons = {"pdf": "&#x1F4D5;", "docx": "&#x1F4D8;", "txt": "&#x1F4C4;",
             "csv": "&#x1F4CA;", "pptx": "&#x1F4D9;", "md": "&#x1F5D2;"}
    icon    = icons.get(ext, "&#x1F4C4;")
    ico_cls = f"dm-ico-{ext}" if ext in icons else "dm-ico-txt"
    st.markdown(
        f'<div class="dm-doc">'
        f'  <div class="dm-doc-ico {ico_cls}">{icon}</div>'
        f'  <div class="dm-doc-name">{filename}</div>'
        f'  <div class="dm-doc-ext">.{ext}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline loader — server-level cache (loads once, never again)
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading DocuMind AI … (first load only)")
def _build_pipeline():
    from src.rag_pipeline import RAGPipeline
    return RAGPipeline()


def get_pipeline():
    try:
        return _build_pipeline()
    except Exception as exc:
        st.error(f"Failed to initialise pipeline: {exc}")
        return None
