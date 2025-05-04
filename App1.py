import json
from collections import defaultdict
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<h1 style='font-size: 1.8em;'>🧩 Character Decomposition Explorer</h1>
""", unsafe_allow_html=True)

# Initialize session state at the top
if "selected_comp" not in st.session_state:
    st.session_state.selected_comp = "⺌"
if "max_depth" not in st.session_state:
    st.session_state.max_depth = 0
if "stroke_range" not in st.session_state:
    st.session_state.stroke_range = (3, 14)
if "display_mode" not in st.session_state:
    st.session_state.display_mode = "Minimalist"

# Rest of your existing code for loading char_decomp, get_all_components, build_component_map, etc. remains unchanged...

# === Step 4: Controls ===
col1, col2 = st.columns(2)
with col1:
    st.slider("Max Decomposition Depth", 0, 5, key="max_depth")
with col2:
    st.slider("Strokes Range", 0, 30, key="stroke_range")

# Add display mode selection
st.radio(
    "Display Mode:",
    options=["Minimalist", "2-Character Phrases", "4-Character Idioms", "All Other Compounds"],
    key="display_mode",
    help=(
        "Minimalist: Shows character, pinyin, definition, and strokes. "
        "2-Character Phrases: Shows characters with 2-character compound words. "
        "4-Character Idioms: Shows characters with 4-character compound words. "
        "All Other Compounds: Shows characters with compound words of other lengths."
    )
)

min_strokes, max_strokes = st.session_state.stroke_range
component_map = build_component_map(max_depth=st.session_state.max_depth)

# === Helper: Get stroke count === (unchanged)
def get_stroke_count(char):
    strokes = char_decomp.get(char, {}).get("strokes", None)
    return strokes if strokes is not None else -1

# === Filter dropdown options === (unchanged)
filtered_components = [
    comp for comp in component_map
    if min_strokes <= get_stroke_count(comp) <= max_strokes
]
sorted_components = sorted(filtered_components, key=get_stroke_count)

if st.session_state.selected_comp and st.session_state.selected_comp not in sorted_components:
    sorted_components.insert(0, st.session_state.selected_comp)

# === Component selection === (unchanged)
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
        index=sorted_components.index(st.session_state.selected_comp),
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
    # Base character list for Minimalist mode
    chars = [
        c for c in component_map.get(st.session_state.selected_comp, [])
        if min_strokes <= get_stroke_count(c) <= max_strokes
    ]
    
    # Filter characters based on display mode
    if st.session_state.display_mode != "Minimalist":
        # For compound-based modes, only include characters with compounds
        chars = [
            c for c in chars
            if char_decomp.get(c, {}).get("compounds", [])
        ]
    
    chars = sorted(set(chars), key=get_stroke_count)

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

    for c in chars:
        entry = char_decomp.get(c, {})
        pinyin = entry.get("pinyin", "—")
        definition = entry.get("definition", "No definition available")
        stroke_count = get_stroke_count(c)
        stroke_text = f"{stroke_count} strokes" if stroke_count != -1 else "unknown strokes"
        st.write(f"**{c}** — {pinyin} — {definition} ({stroke_text})")

        if st.session_state.display_mode != "Minimalist":
            compounds = entry.get("compounds", [])
            if compounds:
                # Filter compounds based on display mode
                if st.session_state.display_mode == "2-Character Phrases":
                    filtered_compounds = [comp for comp in compounds if len(comp) == 2]
                elif st.session_state.display_mode == "4-Character Idioms":
                    filtered_compounds = [comp for comp in compounds if len(comp) == 4]
                else:  # All Other Compounds
                    filtered_compounds = [comp for comp in compounds if len(comp) not in (2, 4)]
                
                if filtered_compounds:
                    st.markdown(f"**{st.session_state.display_mode} for {c}:**")
                    sorted_compounds = sorted(filtered_compounds, key=len)
                    st.write(" ".join(sorted_compounds))
