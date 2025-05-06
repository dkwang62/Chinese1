import json
from collections import defaultdict
import streamlit as st

# Set page configuration
st.set_page_config(layout="wide")

# Custom CSS for styling with mobile responsiveness
st.markdown("""
<style>
    .main-header {
        font-size: 2em;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 20px;
        text-align: center;
    }
    .controls-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .selected-card {
        background-color: #e8f4f8;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        display: flex;
        align-items: center;
        gap: 15px;
        border-left: 5px solid #3498db;
    }
    .selected-char {
        font-size: 2.5em;
        color: #e74c3c;
        margin: 0;
    }
    .selected-details {
        font-size: 1.1em;
        color: #34495e;
        margin: 0;
    }
    .selected-details strong {
        color: #2c3e50;
    }
    .results-header {
        font-size: 1.5em;
        color: #2c3e50;
        margin-top: 20px;
        margin-bottom: 10px;
    }
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
    .char-title {
        font-size: 1.4em;
        color: #e74c3c;
        margin: 0;
        display: inline;
    }
    .char-details {
        font-size: 1em;
        color: #34495e;
        margin: 5px 0;
    }
    .char-details strong {
        color: #2c3e50;
    }
    .compounds-section {
        background-color: #f1f8e9;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
    .compounds-title {
        font-size: 1.1em;
        color: #558b2f;
        margin: 0 0 5px 0;
    }
    .compounds-list {
        font-size: 1em;
        color: #34495e;
        margin: 0;
    }
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.5em;
            margin-bottom: 15px;
        }
        .controls-container {
            padding: 10px;
        }
        .selected-card {
            flex-direction: column;
            align-items: flex-start;
            padding: 15px;
        }
        .selected-char {
            font-size: 2em;
        }
        .selected-details {
            font-size: 0.95em;
            line-height: 1.5;
        }
        .results-header {
            font-size: 1.3em;
        }
        .char-card {
            padding: 10px;
        }
        .char-title {
            font-size: 1.2em;
        }
        .char-details {
            font-size: 0.9em;
            line-height: 1.5;
        }
        .compounds-title {
            font-size: 1em;
        }
        .compounds-list {
            font-size: 0.9em;
        }
        /* Stack columns vertically on mobile */
        .stColumn {
            display: block !important;
            width: 100% !important;
        }
        .stColumn > div {
            margin-bottom: 10px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Display the main header
st.markdown("<h1 class='main-header'>🧩 Character Decomposition Explorer</h1>", unsafe_allow_html=True)

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

# === Helper: Get stroke count ===
def get_stroke_count(char):
    strokes = char_decomp.get(char, {}).get("strokes", None)
    return strokes if strokes is not None else -1

# === Component selection ===
def on_text_input_change():
    text_value = st.session_state.text_input_comp.strip()
    if text_value and (text_value in component_map or text_value in char_decomp):
        st.session_state.selected_comp = text_value
    elif text_value:
        st.warning("Character not found in component map or dictionary. Please enter a valid character.")

# Compute component_map and sorted_components before controls
min_strokes, max_strokes = st.session_state.stroke_range
component_map = build_component_map(max_depth=st.session_state.max_depth)

# Filter dropdown options
filtered_components = [
    comp for comp in component_map
    if min_strokes <= get_stroke_count(comp) <= max_strokes
]
sorted_components = sorted(filtered_components, key=get_stroke_count)

if st.session_state.selected_comp and st.session_state.selected_comp not in sorted_components:
    sorted_components.insert(0, st.session_state.selected_comp)

# === Step 4: Controls ===
with st.container():
    st.markdown("<div class='controls-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.slider("Max Decomposition Depth", 0, 5, key="max_depth")
        st.radio(
            "Display Mode:",
            options=["Minimalist", "2-Character Phrases", "3-Character Phrases", "4-Character Idioms"],
            key="display_mode",
            help=(
                "Minimalist: Shows character, pinyin, definition, and strokes. "
                "2-Character Phrases: Shows characters with 2-character compound words. "
                "3-Character Phrases: Shows characters with 3-character compound words. "
                "4-Character Idioms: Shows characters with 4-character compound words."
            )
        )
    with col2:
        st.slider("Strokes Range", 0, 30, key="stroke_range")
        col_a, col_b = st.columns([1, 1])
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
    st.markdown("</div>", unsafe_allow_html=True)

# === Helper: Clean field display ===
def clean_field(field):
    if isinstance(field, list):
        return field[0] if field else "—"
    return field if field else "—"

# === Display current selection and decomposed characters ===
if st.session_state.selected_comp:
    # Fetch and clean fields for the selected component
    selected_entry = char_decomp.get(st.session_state.selected_comp, {})
    selected_pinyin = clean_field(selected_entry.get("pinyin", "—"))
    selected_definition = clean_field(selected_entry.get("definition", "No definition available"))
    selected_radical = clean_field(selected_entry.get("radical", "—"))
    selected_hint = clean_field(selected_entry.get("etymology", {}).get("hint", "No hint available"))
    selected_stroke_count = get_stroke_count(st.session_state.selected_comp)
    selected_stroke_text = f"{selected_stroke_count} strokes" if selected_stroke_count != -1 else "unknown strokes"

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
            elif st.session_state.display_mode == "4-Character Idioms":
                filtered_compounds = [comp for comp in compounds if len(comp) == 4]

            # Only include the character if it has compounds that match the filter
            if filtered_compounds:
                filtered_chars.append(c)
                char_compounds[c] = filtered_compounds

    chars = sorted(set(filtered_chars), key=get_stroke_count)

    # Display selected component with cleaned fields
    st.markdown(f"""
    <div class='selected-card'>
        <h2 class='selected-char'>{st.session_state.selected_comp}</h2>
        <p class='selected-details'>
            <strong>Pinyin:</strong> {selected_pinyin}   
            <strong>Definition:</strong> {selected_definition}   
            <strong>Radical:</strong> {selected_radical}   
            <strong>Hint:</strong> {selected_hint}   
            <strong>Strokes:</strong> {selected_stroke_text}   
            <strong>Depth:</strong> {st.session_state.max_depth}   
            <strong>Stroke Range:</strong> {min_strokes} – {max_strokes}
        </p>
    </div>
    <h2 class='results-header'>🧬 Characters with {st.session_state.selected_comp} — {len(chars)} result(s)</h2>
    """, unsafe_allow_html=True)

    # Display decomposed characters
    for c in chars:
        entry = char_decomp.get(c, {})
        pinyin = clean_field(entry.get("pinyin", "—"))
        definition = clean_field(entry.get("definition", "No definition available"))
        radical = clean_field(entry.get("radical", "—"))
        hint = clean_field(entry.get("etymology", {}).get("hint", "No hint available"))
        stroke_count = get_stroke_count(c)
        stroke_text = f"{stroke_count} strokes" if stroke_count != -1 else "unknown strokes"

        # Display character card
        st.markdown(f"""
        <div class='char-card'>
            <h3 class='char-title'>{c}</h3>
            <p class='char-details'>
                <strong>Pinyin:</strong> {pinyin}   
                <strong>Definition:</strong> {definition}   
                <strong>Radical:</strong> {radical}   
                <strong>Hint:</strong> {hint}   
                <strong>Strokes:</strong> {stroke_text}
            </p>
        """, unsafe_allow_html=True)

        # Display compounds if not in Minimalist mode
        if st.session_state.display_mode != "Minimalist":
            filtered_compounds = char_compounds.get(c, [])
            if filtered_compounds:
                sorted_compounds = sorted(filtered_compounds, key=lambda x: x[0])
                compounds_text = " ".join(sorted_compounds)
                st.markdown(f"""
                <div class='compounds-section'>
                    <p class='compounds-title'>{st.session_state.display_mode} for {c}:</p>
                    <p class='compounds-list'>{compounds_text}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
