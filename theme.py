"""
theme.py
--------
Custom CSS for a dark, neon-accented, eye-comfortable look on top of the
base dark theme set in .streamlit/config.toml.

Design choices (why it's "eye comfort" and not just "dark mode"):
- Background is a deep navy-black (#0B0F19), not pure #000000 -- pure
  black next to bright neon creates harsher edge contrast and more eye
  strain over long sessions.
- Body text is a soft off-white (#E6EDF3), not pure #FFFFFF -- avoids
  the glare of maximum-contrast white-on-dark text.
- Neon (cyan/magenta) is used only as *accents* -- headings, borders,
  buttons, focus states -- never as large filled blocks or as body text
  color, so it reads as vibrant without being fatiguing.
- Glow effects use soft, low-spread box/text-shadows rather than solid
  bright fills.
"""

CSS = """
<style>
:root {
    --bg: #0B0F19;
    --bg-panel: #131A2A;
    --bg-panel-2: #0F1524;
    --text: #E6EDF3;
    --text-dim: #93A1B8;
    --neon-cyan: #39E6E1;
    --neon-magenta: #C77DFF;
    --neon-green: #39FF88;
    --border: #223047;
}

/* ---- App background ---- */
.stApp {
    background: radial-gradient(1200px 600px at 10% -10%, #101A2E 0%, var(--bg) 55%) fixed;
    color: var(--text);
}

/* ---- Headings: subtle neon gradient + soft glow ---- */
h1, h2, h3 {
    background: linear-gradient(90deg, var(--neon-cyan), var(--neon-magenta));
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 18px rgba(57, 230, 225, 0.15);
    font-weight: 700 !important;
}

/* Caption / helper text stays low-contrast so it doesn't compete with body text */
.stCaption, [data-testid="stCaptionContainer"] {
    color: var(--text-dim) !important;
}

/* ---- Containers used for item rows (st.container(border=True)) ---- */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--bg-panel);
    border: 1px solid var(--border) !important;
    border-radius: 10px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(57, 230, 225, 0.55) !important;
    box-shadow: 0 0 14px rgba(57, 230, 225, 0.12);
}

/* ---- Inputs ---- */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {
    background-color: var(--bg-panel-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus,
.stNumberInput input:focus, .stDateInput input:focus {
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 0 1px var(--neon-cyan), 0 0 12px rgba(57, 230, 225, 0.35) !important;
}

/* Selectbox / radio */
[data-baseweb="select"] > div {
    background-color: var(--bg-panel-2) !important;
    border-color: var(--border) !important;
}
div[role="radiogroup"] label {
    color: var(--text) !important;
}

/* ---- Buttons ---- */
.stButton > button, .stDownloadButton > button {
    background: var(--bg-panel-2);
    color: var(--neon-cyan);
    border: 1px solid var(--neon-cyan);
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.15s ease;
    box-shadow: 0 0 8px rgba(57, 230, 225, 0.15);
}
.stButton > button:hover, .stDownloadButton > button:hover {
    color: #04211F;
    background: var(--neon-cyan);
    box-shadow: 0 0 22px rgba(57, 230, 225, 0.55);
    border-color: var(--neon-cyan);
}

/* Primary "Generate PDF" button gets the stronger magenta/cyan glow */
.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, rgba(57,230,225,0.15), rgba(199,125,255,0.15));
    color: var(--text);
    border: 1px solid var(--neon-magenta);
    box-shadow: 0 0 14px rgba(199, 125, 255, 0.25);
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(90deg, var(--neon-cyan), var(--neon-magenta));
    color: #0B0F19;
    box-shadow: 0 0 26px rgba(199, 125, 255, 0.55);
}

/* ---- Dividers ---- */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--neon-cyan), transparent);
    opacity: 0.35;
    margin: 1.4rem 0;
}

/* ---- File uploader ---- */
[data-testid="stFileUploaderDropzone"] {
    background-color: var(--bg-panel-2) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 10px;
}

/* ---- Success / warning / error boxes: keep readable, just re-tint borders ---- */
div[data-testid="stAlert"] {
    background-color: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px;
}

/* ---- Metric-like totals line ---- */
.stMarkdown h3 {
    text-shadow: 0 0 14px rgba(57, 255, 136, 0.25);
}
</style>
"""


def inject(st):
    st.markdown(CSS, unsafe_allow_html=True)
