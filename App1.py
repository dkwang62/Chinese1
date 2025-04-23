{\rtf1\ansi\ansicpg1252\cocoartf2822
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import json\
from collections import defaultdict\
import streamlit as st\
\
st.set_page_config(layout="wide")\
\
st.markdown("""\
<h1 style='font-size: 1.8em;'>\uc0\u55358 \u56809  Character Decomposition Explorer</h1>\
""", unsafe_allow_html=True)\
\
# === Step 1: Load strokes1.json from local file (cached) ===\
@st.cache_data\
def load_char_decomp():\
    with open("strokes1.json", "r", encoding="utf-8") as f:\
        entries = json.load(f)\
        return \{entry["character"]: entry for entry in entries\}\
\
char_decomp = load_char_decomp()\
\
# === Step 2: Recursive decomposition ===\
def get_all_components(char, max_depth=2, depth=0, seen=None):\
    if seen is None:\
        seen = set()\
    if char in seen or depth > max_depth:\
        return set()\
    seen.add(char)\
    components = set()\
    for comp in char_decomp.get(char, \{\}).get("decomposition", ""):\
        if '\uc0\u19968 ' <= comp <= '\u40959 ':\
            components.add(comp)\
            components.update(get_all_components(comp, max_depth, depth + 1, seen))\
    return components\
\
# === Step 3: Build component map (cached) ===\
@st.cache_data\
def build_component_map(max_depth):\
    component_map = defaultdict(list)\
    for char in char_decomp:\
        all_components = get_all_components(char, max_depth=max_depth)\
        for comp in all_components:\
            component_map[comp].append(char)\
    return component_map\
\
# === Step 4: Controls ===\
if "selected_comp" not in st.session_state:\
    st.session_state.selected_comp = "\uc0\u26408 "\
if "max_depth" not in st.session_state:\
    st.session_state.max_depth = 1\
if "stroke_range" not in st.session_state:\
    st.session_state.stroke_range = (4, 10)\
\
col1, col2 = st.columns(2)\
with col1:\
    st.slider("Max Decomposition Depth", 0, 5, key="max_depth")\
with col2:\
    st.slider("Stroke Count Range", 0, 30, key="stroke_range")\
\
min_strokes, max_strokes = st.session_state.stroke_range\
component_map = build_component_map(max_depth=st.session_state.max_depth)\
\
# === Helper: Get stroke count ===\
def get_stroke_count(char):\
    return char_decomp.get(char, \{\}).get("strokes", float('inf'))\
\
# === Filter dropdown options ===\
filtered_components = [\
    comp for comp in component_map\
    if min_strokes <= get_stroke_count(comp) <= max_strokes\
]\
sorted_components = sorted(filtered_components, key=get_stroke_count)\
\
# === Component selection ===\
def on_text_input_change():\
    text_value = st.session_state.text_input_comp.strip()\
    if text_value and text_value in component_map:\
        st.session_state.selected_comp = text_value\
    elif text_value:\
        st.warning("Invalid component entered. Please select from the dropdown or enter a valid component.")\
\
col_a, col_b = st.columns(2)\
with col_a:\
    st.selectbox(\
        "Select a component:",\
        options=sorted_components,\
        format_func=lambda c: f"\{c\} (\{get_stroke_count(c)\} strokes)",\
        index=sorted_components.index(st.session_state.selected_comp) if st.session_state.selected_comp in sorted_components else 0,\
        key="selected_comp"\
    )\
with col_b:\
    st.text_input(\
        "Or type a component:",\
        value=st.session_state.selected_comp,\
        key="text_input_comp",\
        on_change=on_text_input_change\
    )\
\
# === Display current selection ===\
st.markdown(f"""\
<h2 style='font-size: 1.2em;'>\uc0\u55357 \u56524  Current Selection</h2>\
<p><strong>Component:</strong> \{st.session_state.selected_comp\} \'a0\'a0 <strong>Level:</strong> \{st.session_state.max_depth\} \'a0\'a0 <strong>Stroke Range:</strong> \{min_strokes\} \'96 \{max_strokes\}</p>\
""", unsafe_allow_html=True)\
\
# === Step 5: Display decomposed characters ===\
if st.session_state.selected_comp:\
    chars = [\
        c for c in component_map.get(st.session_state.selected_comp, [])\
        if min_strokes <= get_stroke_count(c) <= max_strokes\
    ]\
    chars = sorted(set(chars))\
\
    st.markdown(\
        f"<h2 style='font-size: 1.2em;'>\uc0\u55358 \u56812  Characters with: \{st.session_state.selected_comp\} \'97 \{len(chars)\} result(s)</h2>",\
        unsafe_allow_html=True\
    )\
    for c in chars:\
        entry = char_decomp.get(c, \{\})\
        pinyin = entry.get("pinyin", "\'97")\
        definition = entry.get("definition", "No definition available")\
        st.write(f"**\{c\}** \'97 \{pinyin\} \'97 \{definition\}")\
\
        compounds = entry.get("compounds", [])\
        if compounds:\
            st.markdown(f"**Compound Words for \{c\}:**")\
            for word_info in compounds:\
                st.write(f"- **\{word_info['word']\}** \'97 \{word_info['pinyin']\} \'97 \{word_info['definition']\}")\
}