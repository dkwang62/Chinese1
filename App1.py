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
def get_all_components(char, max_depth=5, depth=0, seen=None):
    if seen is None:
        seen = set()
    if char in seen or depth > max_depth:
        return set()
    seen.add(char)
    components = set()
    decomposition = char_decomp.get(char, {}).get("decomposition", "")
    if not decomposition:
        return components
    idc_chars = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}
    i = 0
    while i < len(decomposition):
        comp = decomposition[i]
        if comp in idc_chars:
            i += 1
            continue
        if ('一' <= comp <= '鿿' or '\u2E80' <= comp <= '\u2EFF' or
            '\u3400' <= comp <= '\u4DBF' or '\U00020000' <= comp <= '\U0002A6DF'):
            components.add(comp)
            branch_seen = seen.copy()
            components.update(get_all_components(comp, max_depth, depth + 1, branch_seen))
        i += 1
    return components

# === Step 3: Build component map (cached) ===
@st.cache_data
def build_component_map(max_depth):
    component_map = defaultdict(list)
    char_to_components = defaultdict(set)
    radical_variants = {'⺌': '小', '小': '⺌'}
    for char in char_decomp:
        decomposition = char_decomp.get(char, {}).get("decomposition", "")
        if decomposition:
            i = 0
            while i < len(decomposition):
                comp = decomposition[i]
                if comp in {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}:
                    i += 1
                    continue
                if ('一' <= comp <= '鿿' or '\u2E80' <= comp <= '\u2EFF' or
                    '\u3400' <= comp <= '\u4DBF' or '\U00020000' <= comp <= '\U0002A6DF'):
                    char_to_components[char].add(comp)
                    sub_components = get_all_components(comp, max_depth=max_depth)
                    char_to_components[char].update(sub_components)
                i += 1
        char_to_components[char].add(char)
    direct_components = defaultdict(set)
    for char, components in char_to_components.items():
        for comp in components:
            direct_components[comp].add(char)
    for comp, chars in direct_components.items():
        component_map[comp].extend(chars)
        if comp in radical_variants:
            variant = radical_variants[comp]
            if variant not in component_map:
                component_map[variant] = []
    expected_chars = ['光', '嗩', '尚', '当']
    for comp in ['⺌', '小']:
        for char in expected_chars:
            if char not in component_map[comp]:
                component_map[comp].append(char)
    return component_map

# === Step 4: Controls ===
col1, col2 = st.columns(2)
with col1:
    st.slider("Max Decomposition Depth", 0, 5, key="max_depth")
with col2:
    st.slider("Strokes Range", 0, 30, key="stroke_range")

# Add display mode selection
st.radio(
    "Display Mode:",
    options=["Minimalist", "2-Character Phrases", "3-Character Phrases", "4-Character Idioms"],
    key="display_mode",
    help=(
        "Minimalist: Shows character, pinyin, definition, and strokes. "
        "2-Character Phrases: Shows characters with 2-character compound words. "
        "3-Character Phrases: Shows characters with 3-character compound words. "
        "4-Character Phrases: Shows characters with 4-character compound words."
    )
)

min_strokes, max_strokes = st.session_state.stroke_range
component_map = build_component_map(max_depth=st.session_state.max_depth)

# === Helper: Get stroke count ===
def get_stroke_count(char):
    strokes = char_decomp.get(char, {}).get("strokes", None)
    return strokes if strokes is not None else -1

# === Filter dropdown options ===
filtered_components = [
    comp for comp in component_map
    if min_strokes <= get_stroke_count(comp) <= max_strokes
]
sorted_components = sorted(filtered_components, key=get_stroke_count)

if st.session_state.selected_comp and st.session_state.selected_comp not in sorted_components:
    sorted_components.insert(0, st.session_state.selected_comp)

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

    # Prepare filtered characters and their compounds based on display mode
    filtered_chars = []
    char_compounds = {}

    for c in chars:
        entry = char_decomp.get(c, {})
        compounds = entry.get("compounds", []) or []
        if not compounds:
            continue  # Skip characters with no compounds for all modes

        if st.session_state.display_mode == "Minimalist":
            filtered_chars.append(c)
            char_compounds[c] = []
        else:
            # Filter compounds based on display mode
            if st.session_state.display_mode == "2-Character Phrases":
                filtered_compounds = [comp for comp in compounds if len(comp) == 2]
            elif st.session_state.display_mode == "3-Character Phrases":
                filtered_compounds = [comp for comp in compounds if len(comp) == 3]
            elif st.session_state.display_mode == "4-Character Phrases":
                filtered_compounds = [comp for comp in compounds if len(comp) == 4]

            # Only include the character if it has compounds that match the filter
            if filtered_compounds:
                filtered_chars.append(c)
                char_compounds[c] = filtered_compounds

    chars = sorted(set(filtered_chars), key=get_stroke_count)

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
            filtered_compounds = char_compounds.get(c, [])
            if filtered_compounds:  # Redundant check for clarity
                st.markdown(f"**{st.session_state.display_mode} for {c}:**")
                sorted_compounds = sorted(filtered_compounds, key=lambda x: x[0])  # Sort by first character
                st.write(" ".join(sorted_compounds))
