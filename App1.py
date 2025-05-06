import streamlit as st
import json
import re
import os
from pathlib import Path

st.set_page_config(layout="wide")

# === CSS Styling ===
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# === Constants ===
IDC_CHARS = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}
MODE_LENGTH_MAP = {
    "2-Character Phrases": 2,
    "3-Character Phrases": 3,
    "4-Character Phrases": 4
}

# === Helper Functions ===
def clean_field(field):
    if isinstance(field, list):
        return ", ".join(field)
    return field or "—"

def get_stroke_count(c):
    return char_decomp.get(c, {}).get("strokes", "—")

def is_valid_component(comp):
    return ('一' <= comp <= '鿿' or '⺀' <= comp <= '⻿' or
            '㐀' <= comp <= '䶿' or '\U00020000' <= comp <= '\U0002A6DF')

def get_char_info(char):
    entry = char_decomp.get(char, {})
    return {
        "pinyin": clean_field(entry.get("pinyin")),
        "definition": clean_field(entry.get("definition", "No definition available")),
        "radical": clean_field(entry.get("radical")),
        "hint": clean_field(entry.get("etymology", {}).get("hint", "No hint available")),
        "strokes": get_stroke_count(char)
    }

# === Load Data ===
@st.cache_data
def load_data():
    with open("char_decomp.json", encoding="utf-8") as f:
        char_decomp = json.load(f)
    with open("compounds.json", encoding="utf-8") as f:
        compounds = json.load(f)
    return char_decomp, compounds

char_decomp, compounds = load_data()

# === Component Extraction ===
def get_all_components(char):
    components = set()
    stack = [char]
    while stack:
        current = stack.pop()
        decomp = char_decomp.get(current, {}).get("decomposition", "")
        for comp in decomp:
            if comp in IDC_CHARS or not is_valid_component(comp):
                continue
            components.add(comp)
            stack.append(comp)
    return components

# === Component Map ===
def build_component_map():
    component_map = {}
    for comp in compounds:
        all_chars = set(comp)
        components = set()
        for c in comp:
            components |= get_all_components(c)
        for c in components:
            component_map.setdefault(c, set()).add(comp)
    return component_map

component_map = build_component_map()

# === Sidebar Controls ===
st.sidebar.title("Decomposition Tool")
input_char = st.sidebar.text_input("Enter a Chinese character:", max_chars=1)
st.sidebar.selectbox(
    "Display Mode:",
    ["All Components", "2-Character Phrases", "3-Character Phrases", "4-Character Phrases"],
    key="display_mode"
)

# === Main Display ===
if input_char:
    input_char = input_char.strip()
    st.header(f"Character: {input_char}")

    components = get_all_components(input_char)
    components = sorted(components, key=lambda x: get_stroke_count(x) if isinstance(get_stroke_count(x), int) else 0)

    if st.session_state.display_mode == "All Components":
        cols = st.columns(4)
        for i, c in enumerate(components):
            with cols[i % 4]:
                info = get_char_info(c)
                st.markdown(f"<div class='char-box'>{c}</div>", unsafe_allow_html=True)
                st.markdown(f"Pinyin: {info['pinyin']}")
                st.markdown(f"Meaning: {info['definition']}")
                st.markdown(f"Radical: {info['radical']}")
                st.markdown(f"Hint: {info['hint']}")
                st.markdown(f"Strokes: {info['strokes']}")
    else:
        phrase_length = MODE_LENGTH_MAP.get(st.session_state.display_mode)
        filtered_compounds = [comp for c in components for comp in component_map.get(c, []) if len(comp) == phrase_length]
        filtered_compounds = sorted(set(filtered_compounds))
        st.markdown(f"### Matching {phrase_length}-Character Compounds")
        st.write(", ".join(filtered_compounds) if filtered_compounds else "No matching compounds found.")
