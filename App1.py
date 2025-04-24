import json
from collections import defaultdict
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<h1 style='font-size: 2.8em;'>🧩 Compound Characters Explorer</h1>
""", unsafe_allow_html=True)

# === Step 1: Load strokes1.json from local file (cached) ===
@st.cache_data
def load_char_decomp():
    try:
        with open("strokes1.json", "r", encoding="utf-8") as f:
            entries = json.load(f)
            return {entry["character"]: entry for entry in entries}
    except FileNotFoundError:
        st.error("Error: strokes1.json file not found.")
        return {}
    except json.JSONDecodeError:
        st.error("Error: strokes1.json is malformed or invalid JSON.")
        return {}

char_decomp = load_char_decomp()

# === Step 2: Recursive decomposition ===
def get_all_components(char, max_depth=2, depth=0, seen=None):
    if seen is None:
        seen = set()
    if char in seen or depth > max_depth:
        return set()
    seen.add(char)
    components = set()
    for comp in char_decomp.get(char, {}).get("decomposition", ""):
        if '一' <= comp <= '鿿':
            components.add(comp)
            components.update(get_all_components(comp, max_depth, depth + 1, seen))
    return components

# === Step 3: Build component map (cached) ===
@st.cache_data
def build_component_map(max_depth):
    component_map = defaultdict(list)
    for char in char_decomp:
        all_components = get_all_components(char, max_depth=max_depth)
        for comp in all_components:
            component_map[comp].append(char)
        # Include the character itself as a component
        component_map[char].append(char)
    return component_map

# === Step 4: Controls ===
if "selected_comp" not in st.session_state:
    st.session_state.selected_comp = "木"
if "max_depth" not in st.session_state:
    st.session_state.max_depth = 1
if "stroke_range" not in st.session_state:
    st.session_state.stroke_range = (4, 10)

col1, col2 = st.columns(2)
with col1:
    st.slider("Max Decomposition Depth", 0, 5, key="max_depth")
with col2:
    st.slider("Strokes Range", 0, 30, key="stroke_range")

min_strokes, max_strokes = st.session_state.stroke_range
component_map = build_component_map(max_depth=st.session_state.max_depth)

# === Helper: Get stroke count ===
def get_stroke_count(char):
    return char_decomp.get(char, {}).get("strokes", float('inf'))

# === Filter dropdown options ===
filtered_components = [
    comp for comp in component_map
    if min_strokes <= get_stroke_count(comp) <= max_strokes
]
sorted_components = sorted(filtered_components, key=get_stroke_count)

# === Component selection ===
def on_text_input_change():
    text_value = st.session_state.text_input_comp.strip()
    if text_value and (text_value in component_map or text_value in char_decomp):
        st.session_state.selected_comp = text_value
    elif text_value:
        st.warning("Character not found in component map or dictionary. Please enter a valid character.")

col_a, col_b = st.columns(2)
with col_a:
    st.selectbox(
        "Select a component:",
        options=sorted_components,
        format_func=lambda c: f"{c} ({get_stroke_count(c)} strokes)",
        index=sorted_components.index(st.session_state.selected_comp) if st.session_state.selected_comp in sorted_components else 0,
        key="selected_comp"
    )
with col_b:
    st.text_input(
        "Or type a component:",
        value=st.session_state.selected_comp,
        key="text_input_comp",
        on_change=on_text_input_change
    )

# === Display current selection and decomposed characters ===
if st.session_state.selected_comp:
    # Get characters that contain the selected component and have stroke counts in range
    chars = [
        c for c in component_map.get(st.session_state.selected_comp, [])
        if min_strokes <= get_stroke_count(c) <= max_strokes
    ]
    # Sort and remove duplicates
    chars = sorted(set(chars))

    # Display all elements in a single row using flexbox
    st.markdown(f"""
    <div style='display: flex; align-items: center; gap: 20px;'>
        <h2 style='font-size: 1.2em; margin: 0;'>📌 Selected</h2>
        <span style='font-size: 2.4em;'>{st.session_state.selected_comp}</span>
        <p style='margin: 0;'>
            <strong>Depth:</strong> {st.session_state.max_depth}    
            <strong>Strokes:</strong> {min_strokes} – {max_strokes}
        </p>
        <h2 style='font-size: 1.2em; margin: 0;'>🧬 Characters with: {st.session_state.selected_comp} — {len(chars)} result(s)</h2>
    </div>
    """, unsafe_allow_html=True)

    # Display character details and compounds
    for c in chars:
        entry = char_decomp.get(c, {})
        pinyin = entry.get("pinyin", "—")
        definition = entry.get("definition", "No definition available")
        st.write(f"**{c}** — {pinyin} — {definition}")

        compounds = entry.get("compounds", [])
        if compounds:
            st.markdown(f"**Compound Words for {c}:**")
            sorted_compounds = sorted(compounds, key=len)
            st.write(" ".join(sorted_compounds))
