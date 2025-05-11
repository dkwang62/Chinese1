import json
from collections import defaultdict
import streamlit as st
import streamlit.components.v1 as components
import random

st.set_page_config(layout="wide")

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

# --- Initialize session state ---
def init_session_state():
    config_options = [
        {"selected_comp": "爫", "stroke_count": 4, "selected_idc": "No Filter", "display_mode": "2-Character Phrases"},
        {"selected_comp": "心", "stroke_count": 4, "selected_idc": "No Filter", "display_mode": "3-Character Phrases"},
        {"selected_comp": "⺌", "stroke_count": 3, "selected_idc": "No Filter", "display_mode": "4-Character Phrases"}
    ]
    selected_config = random.choice(config_options)
    defaults = {
        "selected_comp": selected_config["selected_comp"],
        "stroke_count": selected_config["stroke_count"],
        "display_mode": selected_config["display_mode"],
        "selected_idc": selected_config["selected_idc"],
        "idc_refresh": False,
        "text_input_comp": selected_config["selected_comp"],
        "page": 1,
        "results_per_page": 50,
        "previous_selected_comp": selected_config["selected_comp"]
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

@st.cache_data
def load_char_decomp():
    try:
        with open("strokes1.json", "r", encoding="utf-8") as f:
            return {entry["character"]: entry for entry in json.load(f)}
    except Exception as e:
        st.error(f"Failed to load strokes1.json: {e}")
        return {}

char_decomp = load_char_decomp()

def is_valid_char(c):
    return ('一' <= c <= '鿿' or '⺀' <= c <= '⻿' or '㐀' <= c <= '䶿' or '𠀀' <= c <= '𪛟')

def get_stroke_count(char):
    return char_decomp.get(char, {}).get("strokes", -1)

def clean_field(field):
    if isinstance(field, list):
        return field[0] if field else "—"
    return field if field else "—"

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

@st.cache_data
def build_component_map(max_depth=5):
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

def on_text_input_change(component_map):
    text_value = st.session_state.text_input_comp.strip()
    if len(text_value) != 1:
        st.warning("Please enter exactly one character.")
        st.session_state.text_input_comp = st.session_state.selected_comp
        return
    if text_value in component_map or text_value in char_decomp:
        st.session_state.previous_selected_comp = st.session_state.selected_comp
        st.session_state.selected_comp = text_value
        st.session_state.idc_refresh = not st.session_state.idc_refresh
        st.session_state.page = 1
    else:
        st.warning("Invalid character. Please enter a valid component.")
        st.session_state.text_input_comp = st.session_state.selected_comp

def on_selectbox_change():
    st.session_state.previous_selected_comp = st.session_state.selected_comp
    st.session_state.idc_refresh = not st.session_state.idc_refresh
    st.session_state.page = 1

def on_output_char_select(component_map):
    selected_char = st.session_state.output_char_select
    if selected_char != "Select a character..." and selected_char in component_map:
        st.session_state.previous_selected_comp = st.session_state.selected_comp
        st.session_state.selected_comp = selected_char
        st.session_state.idc_refresh = not st.session_state.idc_refresh
        st.session_state.text_input_comp = selected_char
        st.session_state.page = 1
    else:
        if selected_char != "Select a character...":
            st.warning("Invalid character selected. Reverting to previous character.")
        st.session_state.selected_comp = st.session_state.previous_selected_comp
        st.session_state.text_input_comp = st.session_state.previous_selected_comp
        st.session_state.output_char_select = "Select a character..."
        st.session_state.idc_refresh = not st.session_state.idc_refresh
        st.session_state.page = 1

def render_controls(component_map):
    # Get unique stroke counts from component_map
    stroke_counts = sorted(set(get_stroke_count(comp) for comp in component_map if get_stroke_count(comp) != -1))
    if st.session_state.stroke_count not in stroke_counts:
        stroke_counts.append(st.session_state.stroke_count)
        stroke_counts.sort()

    filtered_components = [
        comp for comp in component_map
        if get_stroke_count(comp) == st.session_state.stroke_count
    ]
    sorted_components = sorted(filtered_components, key=get_stroke_count)
    if st.session_state.selected_comp not in sorted_components:
        sorted_components.insert(0, st.session_state.selected_comp)

    idc_chars = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}
    chars = [
        c for c in component_map.get(st.session_state.selected_comp, [])
        if get_stroke_count(c) == st.session_state.stroke_count and c in char_decomp
    ]
    dynamic_idc_options = {"No Filter"}
    for char in chars:
        decomposition = char_decomp.get(char, {}).get("decomposition", "")
        if decomposition and len(decomposition) > 0 and decomposition[0] in idc_chars:
            dynamic_idc_options.add(decomposition[0])
    idc_options = sorted(list(dynamic_idc_options))
    if st.session_state.selected_idc not in idc_options:
        st.session_state.selected_idc = "No Filter"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("Select a component:", options=sorted_components,
                     format_func=lambda c: f"{c} ({get_stroke_count(c)} strokes)",
                     index=sorted_components.index(st.session_state.selected_comp),
                     key="selected_comp",
                     on_change=on_selectbox_change)
    with col2:
        st.text_input("Or type a component:", value=st.session_state.selected_comp,
                      key="text_input_comp", on_change=on_text_input_change, args=(component_map,))
    with col3:
        st.selectbox("Select Stroke Count:", options=stroke_counts,
                     index=stroke_counts.index(st.session_state.stroke_count),
                     key="stroke_count")

    col4, col5 = st.columns(2)
    with col4:
        st.selectbox("Result filtered by IDC Character structure:", options=idc_options,
                     index=idc_options.index(st.session_state.selected_idc), key="selected_idc")
    with col5:
        st.radio("Compound Length:", options=["2-Character Phrases", "3-Character Phrases", "4-Character Phrases"],
                 key="display_mode")

def render_char_card(char, compounds):
    entry = char_decomp.get(char, {})
    idc_chars = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}
    decomposition = entry.get("decomposition", "")
    idc = decomposition[0] if decomposition and decomposition[0] in idc_chars else "—"
    fields = {
        "Pinyin": clean_field(entry.get("pinyin", "—")),
        "Definition": clean_field(entry.get("definition", "No definition available")),
        "Radical": clean_field(entry.get("radical", "—")),
        "Hint": clean_field(entry.get("etymology", {}).get("hint", "No hint available")),
        "Strokes": f"{get_stroke_count(char)} strokes" if get_stroke_count(char) != -1 else "unknown strokes",
        "IDC": idc
    }
    details = " ".join(f"<strong>{k}:</strong> {v}  " for k, v in fields.items())
    st.markdown(f"""<div class='char-card'><h3 class='char-title'>{char}</h3><p class='details'>{details}</p>""", unsafe_allow_html=True)
    if compounds:
        compounds_text = " ".join(sorted(compounds, key=lambda x: x[0]))
        st.markdown(f"""<div class='compounds-section'><p class='compounds-title'>{st.session_state.display_mode} for {char}:</p><p class='compounds-list'>{compounds_text}</p></div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    component_map = build_component_map(max_depth=5)
    st.markdown("<h1>🧩 Character Decomposition Explorer</h1>", unsafe_allow_html=True)
    render_controls(component_map)

    if st.button("Reset App"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        init_session_state()
        st.warning("Please refresh the page")

    if not st.session_state.selected_comp:
        return

    entry = char_decomp.get(st.session_state.selected_comp, {})
    fields = {
        "Pinyin": clean_field(entry.get("pinyin", "—")),
        "Definition": clean_field(entry.get("definition", "No definition available")),
        "Radical": clean_field(entry.get("radical", "—")),
        "Hint": clean_field(entry.get("etymology", {}).get("hint", "No hint available")),
        "Strokes": f"{get_stroke_count(st.session_state.selected_comp)} strokes" if get_stroke_count(st.session_state.selected_comp) != -1 else "unknown strokes"
    }
    details = " ".join(f"<strong>{k}:</strong> {v}  " for k, v in fields.items())
    st.markdown(f"""<div class='selected-card'><h2 class='selected-char'>{st.session_state.selected_comp}</h2><p class='details'>{details}</p></div>""", unsafe_allow_html=True)

    chars = [c for c in component_map.get(st.session_state.selected_comp, [])
             if get_stroke_count(c) == st.session_state.stroke_count]
    if st.session_state.selected_idc != "No Filter":
        chars = [c for c in chars if char_decomp.get(c, {}).get("decomposition", "").startswith(st.session_state.selected_idc)]

    char_compounds = {}
    for c in chars:
        compounds = char_decomp.get(c, {}).get("compounds", [])
        length = int(st.session_state.display_mode[0])  # Extract 2, 3, or 4 from display_mode
        char_compounds[c] = [comp for comp in compounds if len(comp) == length]

    filtered_chars = [c for c in chars if char_compounds[c]]  # Only include chars with matching compounds

    if filtered_chars:
        options = ["Select a character..."] + sorted(filtered_chars, key=get_stroke_count)
        if (st.session_state.previous_selected_comp and 
            st.session_state.previous_selected_comp != st.session_state.selected_comp and 
            st.session_state.previous_selected_comp not in filtered_chars and 
            st.session_state.previous_selected_comp in component_map):
            options.insert(1, st.session_state.previous_selected_comp)
        st.selectbox(
            "Select a character from the list below:",
            options=options,
            key="output_char_select",
            on_change=lambda: on_output_char_select(component_map),
            format_func=lambda c: c if c == "Select a character..." else f"{c} ({clean_field(char_decomp.get(c, {}).get('pinyin', '—'))},{get_stroke_count(c)} strokes, {clean_field(char_decomp.get(c, {}).get('definition', 'No definition available'))})"
        )

    st.markdown(f"<h2 class='results-header'>🧬 Characters with {st.session_state.selected_comp} — {len(filtered_chars)} result(s)</h2>", unsafe_allow_html=True)

    for char in sorted(filtered_chars, key=get_stroke_count):
        render_char_card(char, char_compounds.get(char, []))

    if filtered_chars:
        export_text = "Give me the hanyu pinyin and meaning of each compound phrase in one line a phrase in a downloadable word file\n\n"
        export_text += "\n".join(
            f"{compound}"
            for char in filtered_chars
            for compound in char_compounds.get(char, [])
        )
        st.text_area("Right click, Select all, copy; paste to ChatGPT", export_text, height=300, key="export_text")

        components.html(f"""
            <textarea id="copyTarget" style="opacity:0;position:absolute;left:-9999px;">{export_text}</textarea>
            <script>
            const copyText = document target'select();
            document.execCommand("copy");
            </script>
        """, height=0)

if __name__ == "__main__":
    main()
