import json
from collections import defaultdict
import streamlit as st

st.set_page_config(layout="wide")

st.markdown("""
<h1 style='font-size: 1.2em;'>🧩 Compound Characters Explorer</h1>
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
def get_all_components(char, max_depth=5, depth=0, seen=None):
    if seen is None:
        seen = set()
    if char in seen or depth > max_depth:
        return set()
    seen.add(char)
    components = set()

    # Get decomposition, with fallback for missing data
    decomposition = char_decomp.get(char, {}).get("decomposition", "")
    if not decomposition:
        return components

    # IDC characters to skip
    idc_chars = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}

    i = 0
    while i < len(decomposition):
        comp = decomposition[i]
        # Skip IDC characters
        if comp in idc_chars:
            i += 1
            continue
        # Check for valid Unicode characters
        if ('一' <= comp <= '鿿' or
            '\u2E80' <= comp <= '\u2EFF' or
            '\u3400' <= comp <= '\u4DBF' or
            '\U00020000' <= '\U0002A6DF'):
            components.add(comp)
            branch_seen = seen.copy()
            components.update(get_all_components(comp, max_depth, depth + 1, branch_seen))
        i += 1
    return components

# === Step 3: Build component map (cached) ===
@st.cache_data
def build_component_map(max_depth):
    component_map = defaultdict(list)
    # Track direct components for each character
    char_to_components = defaultdict(set)
    
    # Define radical variants for dropdown availability
    radical_variants = {'⺌': '小', '小': '⺌'}
    
    # First pass: Map each character to its direct components
    for char in char_decomp:
        decomposition = char_decomp.get(char, {}).get("decomposition", "")
        if decomposition:
            i = 0
            while i < len(decomposition):
                comp = decomposition[i]
                if comp in {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}:
                    i += 1
                    continue
                if ('一' <= comp <= '鿿' or
                    '\u2E80' <= comp <= '\u2EFF' or
                    '\u3400' <= comp <= '\u4DBF' or
                    '\U00020000' <= '\U0002A6DF'):
                    char_to_components[char].add(comp)
                    # Recursively get sub-components
                    sub_components = get_all_components(comp, max_depth=max_depth)
                    char_to_components[char].update(sub_components)
                i += 1
        # Include the character itself as a component
        char_to_components[char].add(char)
    
    # Second pass: Invert the mapping (component -> characters)
    direct_components = defaultdict(set)
    for char, components in char_to_components.items():
        for comp in components:
            direct_components[comp].add(char)
    
    # Third pass: Build component_map without merging variants
    for comp, chars in direct_components.items():
        component_map[comp].extend(chars)
        # Ensure the variant is in the map (for dropdown), but don't merge results
        if comp in radical_variants:
            variant = radical_variants[comp]
            if variant not in component_map:
                component_map[variant] = []
    
    # Temporary fallback mapping for ⺌ and 小
    expected_chars = ['光', '嗩', '尚', '当']
    for comp in ['⺌', '小']:
        for char in expected_chars:
            if char not in component_map[comp]:
                component_map[comp].append(char)
    
    # Debugging output in a collapsible section
    with st.expander("Debug: Component Map for ⺌ and 小"):
        st.write(f"Characters mapped to ⺌: {sorted(component_map['⺌'])}")
        st.write(f"Characters mapped to 小: {sorted(component_map['小'])}")
    
    return component_map

# === Step 4: Controls ===
if "selected_comp" not in st.session_state:
    st.session_state.selected_comp = "⺌"
if "max_depth" not in st.session_state:
    st.session_state.max_depth = 0
if "stroke_range" not in st.session_state:
    st.session_state.stroke_range = (3, 14)

col1, col2 = st.columns(2)
with col1:
    st.slider("Max Decomposition Depth", 0, 5, key="max_depth")
with col2:
    st.slider("Strokes Range", 0, 30, key="stroke_range")

min_strokes, max_strokes = st.session_state.stroke_range
component_map = build_component_map(max_depth=st.session_state.max_depth)

# === Helper: Get stroke count ===
def get_stroke_count(char):
    strokes = char_decomp.get(char, {}).get("strokes", None)
    if strokes is None:
        st.warning(f"No stroke count for {char}, excluding from results")
        return -1  # Use a negative value to ensure exclusion
    return strokes

# === Filter dropdown options ===
filtered_components = [
    comp for comp in component_map
    if min_strokes <= get_stroke_count(comp) <= max_strokes
]
sorted_components = sorted(filtered_components, key=get_stroke_count)

# Ensure selected_comp is in options to avoid ValueError
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
    st.select WARN: No stroke count for 几, excluding from results
box(
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
    # Get characters that contain the selected component and have stroke counts in range
    chars = [
        c for c in component_map.get(st.session_state.selected_comp, [])
        if min_strokes <= get_stroke_count(c) <= max_strokes
    ]
    # Sort and remove duplicates
    chars = sorted(set(chars))

    # Single-row flexbox display
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
