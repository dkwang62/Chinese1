import json
from collections import defaultdict
import streamlit as st

# Set page configuration
st.set_page_config(layout="wide")

# Custom CSS for styling
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
    .details { font-size: 1.1em; color: #34495e; margin: 0; }
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
    @media (max-width: 768px) {
        .selected-card { flex-direction: column; align-items: flex-start; padding: 10px; }
        .selected-char { font-size: 2em; }
        .details, .compounds-list { font-size: 0.95em; line-height: 1.5; }
        .results-header { font-size: 1.3em; }
        .char-card { padding: 10px; }
        .char-title { font-size: 1.2em; }
        .compounds-title { font-size: 1em; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    defaults = {
        "selected_comp": "⺌",
        "max_depth": 0,
        "stroke_range": (3, 14),
        "display_mode": "Single Character",
        "selected_idc": "No Filter"  # Default IDC filter
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# Load character decomposition data
@st.cache_data
def load_char_decomp():
    try:
        with open("strokes1.json", "r", encoding="utf-8") as f:
            return {entry["character"]: entry for entry in json.load(f)}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        st.error(f"Error loading strokes1.json: {str(e)}")
        return {}

char_decomp = load_char_decomp()

# Utility functions
def is_valid_char(c):
    return ('一' <= c <= '鿿' or '\u2E80' <= c <= '\u2EFF' or
            '\u3400' <= c <= '\u4DBF' or '\U00020000' <= c <= '\U0002A6DF')

def get_stroke_count(char):
    return char_decomp.get(char, {}).get("strokes", -1)

def clean_field(field):
    if isinstance(field, list):
        return field[0] if field else "—"
    return field if field else "—"

# Recursive decomposition
def get_all_components(char, max_depth, depth=0, seen=None):
    if seen is None:
        seen = set()
    if char in seen or depth > max_depth:
        return set()
    seen.add(char)
    components = set()
    decomposition = char_decomp.get(char, {}).get("decomposition", "")
    idc_chars = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}
    
    for comp in decomposition:
        if comp in idc_chars or not is_valid_char(comp):
            continue
        components.add(comp)
        components.update(get_all_components(comp, max_depth, depth + 1, seen.copy()))
    return components

# Build component map
@st.cache_data
def build_component_map(max_depth):
    component_map = defaultdict(list)
    
    for char in char_decomp:
        components = set()
        decomposition = char_decomp.get(char, {}).get("decomposition", "")
        for comp in decomposition:
            if is_valid_char(comp):
                components.add(comp)
                components.update(get_all_components(comp, max_depth))
        components.add(char)
        
        for comp in components:
            component_map[comp].append(char)
    
    return component_map

# Component selection handler
def on_text_input_change(component_map):
    text_value = st.session_state.text_input_comp.strip()
    if text_value in component_map or text_value in char_decomp:
        st.session_state.selected_comp = text_value
    elif text_value:
        st.warning("Invalid character. Please enter a valid component.")

# UI Controls
def render_controls(component_map):
    min_strokes, max_strokes = st.session_state.stroke_range
    filtered_components = [
        comp for comp in component_map
        if min_strokes <= get_stroke_count(comp) <= max_strokes
    ]
    sorted_components = sorted(filtered_components, key=get_stroke_count)
    
    if st.session_state.selected_comp not in sorted_components:
        sorted_components.insert(0, st.session_state.selected_comp)
    
    st.slider("Max Decomposition Depth", 0, 5, key="max_depth")
    st.slider("Strokes Range", 0, 30, key="stroke_range")
    
    # IDC options
    idc_options = ["No Filter"] + sorted(['⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.selectbox(
            "Select a component:",
            options=sorted_components,
            format_func=lambda c: f"{c} ({get_stroke_count(c)} strokes)",
            index=sorted_components.index(st.session_state.selected_comp) if st.session_state.selected_comp in sorted_components else 0,
            key="selected_comp"
        )
    with col2:
        st.text_input(
            "Or type a component:",
            value=st.session_state.selected_comp,
            key="text_input_comp",
            on_change=on_text_input_change,
            args=(component_map,)
        )
    with col3:
        st.selectbox(
            "Result filtered by IDC Character structure:",
            options=idc_options,
            index=idc_options.index(st.session_state.selected_idc) if st.session_state.selected_idc in idc_options else 0,
            key="selected_idc"
        )
    
    st.radio(
        "Display Mode:",
        options=["Single Character", "2-Character Phrases", "3-Character Phrases", "4-Character Phrases"],
        key="display_mode"
    )

# Render character card
def render_char_card(char, compounds):
    entry = char_decomp.get(char, {})
    # Define valid IDC characters
    idc_chars = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}
    # Get IDC from decomposition
    decomposition = entry.get("decomposition", "")
    idc = decomposition[0] if decomposition and decomposition[0] in idc_chars else "—"
    
    fields = {
        "Pinyin": clean_field(entry.get("pinyin", "—")),
        "Definition": clean_field(entry.get("definition", "No definition available")),
        "Radical": clean_field(entry.get("radical", "—")),
        "Hint": clean_field(entry.get("etymology", {}).get("hint", "No hint available")),
        "Strokes": f"{get_stroke_count(char)} strokes" if get_stroke_count(char) != -1 else "unknown strokes",
        "IDC": idc  # Display IDC
    }
    
    details = " ".join(f"<strong>{k}:</strong> {v}  " for k, v in fields.items())
    st.markdown(f"""
    <div class='char-card'>
        <h3 class='char-title'>{char}</h3>
        <p class='details'>{details}</p>
    """, unsafe_allow_html=True)
    
    if compounds and st.session_state.display_mode != "Single Character":
        compounds_text = " ".join(sorted(compounds, key=lambda x: x[0]))
        st.markdown(f"""
        <div class='compounds-section'>
            <p class='compounds-title'>{st.session_state.display_mode} for {char}:</p>
            <p class='compounds-list'>{compounds_text}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# Main rendering
def main():
    component_map = build_component_map(st.session_state.max_depth)
    st.markdown("<h1>🧩 Character Decomposition Explorer</h1>", unsafe_allow_html=True)
    render_controls(component_map)

    # Reset button to clear session state
    if st.button("Reset App"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
    #   st.experimental_rerun()
        st.warning("App reset. Please rerun the app by refreshing the page or visiting https://chinese1-mcguwrauq4krutvfkyrbkg.streamlit.app/ again.")    
    if not st.session_state.selected_comp:
        return
    
    # Display selected component
    entry = char_decomp.get(st.session_state.selected_comp, {})
    fields = {
        "Pinyin": clean_field(entry.get("pinyin", "—")),
        "Definition": clean_field(entry.get("definition", "No definition available")),
        "Radical": clean_field(entry.get("radical", "—")),
        "Hint": clean_field(entry.get("etymology", {}).get("hint", "No hint available")),
        "Strokes": f"{get_stroke_count(st.session_state.selected_comp)} strokes" if get_stroke_count(st.session_state.selected_comp) != -1 else "unknown strokes",
        "Depth": str(st.session_state.max_depth),
        "Stroke Range": f"{st.session_state.stroke_range[0]} – {st.session_state.stroke_range[1]}"
    }
    details = " ".join(f"<strong>{k}:</strong> {v}  " for k, v in fields.items())
    
    st.markdown(f"""
    <div class='selected-card'>
        <h2 class='selected-char'>{st.session_state.selected_comp}</h2>
        <p class='details'>{details}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter characters by component and stroke range
    min_strokes, max_strokes = st.session_state.stroke_range
    chars = [
        c for c in component_map.get(st.session_state.selected_comp, [])
        if min_strokes <= get_stroke_count(c) <= max_strokes
    ]
    
    # Apply IDC filter
    if st.session_state.selected_idc != "No Filter":
        chars = [
            c for c in chars
            if char_decomp.get(c, {}).get("decomposition", "").startswith(st.session_state.selected_idc)
        ]
    
    char_compounds = {}
    for c in chars:
        compounds = char_decomp.get(c, {}).get("compounds", [])
        if st.session_state.display_mode == "Single Character":
            char_compounds[c] = []
        else:
            length = int(st.session_state.display_mode[0])
            char_compounds[c] = [comp for comp in compounds if len(comp) == length]
    
    filtered_chars = [c for c in chars if not char_compounds[c] == [] or st.session_state.display_mode == "Single Character"]
    st.markdown(f"<h2 class='results-header'>🧬 Characters with {st.session_state.selected_comp} — {len(filtered_chars)} result(s)</h2>", unsafe_allow_html=True)
    
    for char in sorted(filtered_chars, key=get_stroke_count):
        render_char_card(char, char_compounds.get(char, []))

if __name__ == "__main__":
    main()
