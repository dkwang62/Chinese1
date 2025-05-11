import json
from collections import defaultdict
import streamlit as st
import streamlit.components.v1 as components
import random

st.set_page_config(layout="wide")

# --- Global IDC Characters ---
idc_chars = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}

# --- Custom CSS ---
st.markdown("""
<style>
    .selected-card {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 15px;
        border-left: 5px solid #3498db;
    }
    .selected-char { font-size: 2.5em; color: #e74c3c; margin: 0; }
    .details { font-size: 1.5em; color: #34495e; margin: 0; }
    .details strong { color: #2c3e50; }
    .results-header { font-size: 1.5em; color: #2c3e50; margin: 20px 0 10px; }
    .char-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .char-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 3px 8px rgba(0,0,0,0.15);
    }
    .char-title { font-size: 1.4em; color: #e74c3c; margin: 0; display: inline; }
    .compounds-section {
        background-color: #f1f8e9;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
    .compounds-title { font-size: 1.1em; color: #558b2f; margin: 0 0 5px; }
    .compounds-list { font-size: 1em; color: #34495e; margin: 0; }
    .stContainer {
        padding: 10px;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        margin-bottom: 15px;
    }
    .stButton button {
        background-color: #3498db;
        color: white;
        border-radius: 5px;
    }
    .stButton button:hover {
        background-color: #2980b9;
    }
</style>
""", unsafe_allow_html=True)

# --- Session Initialization ---
def init_session_state():
    options = [
        {"selected_comp": "爫", "stroke_count": 4, "selected_idc": "No Filter", "component_idc": "No Filter", "display_mode": "Single Character"},
        {"selected_comp": "心", "stroke_count": 4, "selected_idc": "No Filter", "component_idc": "No Filter", "display_mode": "2-Character Phrases"},
        {"selected_comp": "⺌", "stroke_count": 3, "selected_idc": "No Filter", "component_idc": "No Filter", "display_mode": "3-Character Phrases"}
    ]
    config = random.choice(options)
    defaults = {
        "selected_comp": config["selected_comp"],
        "stroke_count": config["stroke_count"],
        "display_mode": config["display_mode"],
        "selected_idc": config["selected_idc"],
        "component_idc": config["component_idc"],
        "idc_refresh": False,
        "text_input_comp": config["selected_comp"],
        "page": 1,
        "results_per_page": 50,
        "previous_selected_comp": config["selected_comp"]
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# --- Load JSON Data ---
@st.cache_data
def load_char_decomp():
    try:
        with open("strokes1.json", "r", encoding="utf-8") as f:
            return {e["character"]: e for e in json.load(f)}
    except Exception as e:
        st.error(f"Failed to load strokes1.json: {e}")
        return {}

char_decomp = load_char_decomp()

# --- Utility Functions ---
def is_valid_char(c):
    return ('一' <= c <= '鿿' or '⺀' <= c <= '⻿' or '㐀' <= c <= '䶿' or '𠀀' <= c <= '𪛟')

def get_stroke_count(char):
    return char_decomp.get(char, {}).get("strokes", -1)

def clean_field(field):
    if isinstance(field, list):
        return field[0] if field else "—"
    return field if field else "—"

def get_all_components(char, max_depth, depth=0, seen=None):
    if seen is None: seen = set()
    if char in seen or depth > max_depth: return set()
    seen.add(char)
    components = set()
    decomp = char_decomp.get(char, {}).get("decomposition", "")
    for comp in decomp:
        if comp in idc_chars or not is_valid_char(comp): continue
        components.add(comp)
        components.update(get_all_components(comp, max_depth, depth + 1, seen.copy()))
    return components

@st.cache_data
def build_component_map(max_depth=5):
    component_map = defaultdict(list)
    for char in char_decomp:
        components = set()
        decomp = char_decomp.get(char, {}).get("decomposition", "")
        for comp in decomp:
            if is_valid_char(comp):
                components.add(comp)
                components.update(get_all_components(comp, max_depth))
        components.add(char)
        for comp in components:
            component_map[comp].append(char)
    return component_map

# --- UI Component Selection ---
def on_selectbox_change():
    st.session_state.previous_selected_comp = st.session_state.selected_comp
    st.session_state.idc_refresh = not st.session_state.idc_refresh
    st.session_state.page = 1
def render_component_selection(component_map):
    st.markdown("### 🔍 Select Input Component")
    st.caption("Choose or type a single character to explore its related characters.")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        sorted_components = sorted(component_map.keys(), key=get_stroke_count)
        if st.session_state.selected_comp not in sorted_components:
            sorted_components.insert(0, st.session_state.selected_comp)

        st.selectbox(
            "Component Selector:",
            options=sorted_components,
            format_func=lambda c: f"{c} ({get_stroke_count(c)} strokes)" if c in char_decomp else c,
            key="selected_comp",
            on_change=on_selectbox_change
        )
    with col2:
        st.text_input("Or type a component:",
                      value=st.session_state.selected_comp,
                      key="text_input_comp",
                      on_change=on_text_input_change,
                      args=(component_map,))
    with col3:
        st.button("Reset Filters", on_click=on_reset_filters)

# --- Main App ---
def main():
    component_map = build_component_map()
    st.markdown("<h1>🧩 Character Decomposition Explorer</h1>", unsafe_allow_html=True)
    render_component_selection(component_map)

if __name__ == "__main__":
    main()
