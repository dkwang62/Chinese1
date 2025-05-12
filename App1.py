import json
import random
from collections import defaultdict
import streamlit as st
import streamlit.components.v1 as components

# Set page configuration
st.set_page_config(layout="wide")

# Global IDC characters
IDC_CHARS = {'⿰', '⿱', '⿲', '⿳', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'}

# Custom CSS
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
    config_options = [
        {"selected_comp": "爫", "stroke_count": 4, "selected_idc": "No Filter", "component_idc": "No Filter", "display_mode": "Single Character"},
        {"selected_comp": "心", "stroke_count": 4, "selected_idc": "No Filter", "component_idc": "⿱", "display_mode": "2-Character Phrases"},
        {"selected_comp": "⺌", "stroke_count": 3, "selected_idc": "No Filter", "component_idc": "No Filter", "display_mode": "3-Character Phrases"},
        {"selected_comp": "㐱", "stroke_count": 5, "selected_idc": "No Filter", "component_idc": "No Filter", "display_mode": "Single Character"},
        {"selected_comp": "覀", "stroke_count": 6, "selected_idc": "No Filter", "component_idc": "No Filter", "display_mode": "2-Character Phrases"},
        {"selected_comp": "豕", "stroke_count": 7, "selected_idc": "No Filter", "component_idc": "⿰", "display_mode": "3-Character Phrases"}
    ]
    selected_config = random.choice(config_options)
    defaults = {
        "selected_comp": selected_config["selected_comp"],
        "stroke_count": selected_config["stroke_count"],
        "display_mode": selected_config["display_mode"],
        "selected_idc": selected_config["selected_idc"],
        "component_idc": selected_config["component_idc"],
        "idc_refresh": False,
        "text_input_comp": selected_config["selected_comp"],
        "page": 1,
        "results_per_page": 50,
        "previous_selected_comp": selected_config["selected_comp"]
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

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
    return field[0] if isinstance(field, list) and field else field or "—"

def get_all_components(char, max_depth, depth=0, seen=None):
    if seen is None:
        seen = set()
    if char in seen or depth > max_depth or not is_valid_char(char):
        return set()
    seen.add(char)
    components = set()
    decomposition = char_decomp.get(char, {}).get("decomposition", "")
    for comp in decomposition:
        if comp in IDC_CHARS:
            continue
        components.add(comp)
        components.update(get_all_components(comp, max_depth, depth + 1, seen.copy()))
    return components

@st.cache_data
def build_component_map(max_depth=5):
    component_map = defaultdict(list)
    for char in char_decomp:
        components = {char}
        decomposition = char_decomp.get(char, {}).get("decomposition", "")
        for comp in decomposition:
            if is_valid_char(comp):
                components.add(comp)
                components.update(get_all_components(comp, max_depth))
        for comp in components:
            component_map[comp].append(char)
    return component_map

def on_text_input_change(component_map):
    text_value = st.session_state.text_input_comp.strip()
    if len(text_value) != 1:
        st.warning("Please enter exactly one character.")
        return
    if text_value in component_map or text_value in char_decomp:
        st.session_state.previous_selected_comp = st.session_state.selected_comp
        st.session_state.selected_comp = text_value
        st.session_state.page = 1
        st.session_state.idc_refresh = not st.session_state.idc_refresh
    else:
        st.warning("Invalid character. Please enter a valid component.")
        st.session_state.text_input_comp = st.session_state.selected_comp

def on_selectbox_change():
    st.session_state.previous_selected_comp = st.session_state.selected_comp
    st.session_state.page = 1
    st.session_state.idc_refresh = not st.session_state.idc_refresh
    st.session_state.text_input_comp = st.session_state.selected_comp

def on_output_char_select(component_map):
    selected_char = st.session_state.output_char_select
    if selected_char == "Select a character..." or selected_char not in component_map:
        if selected_char != "Select a character...":
            st.warning("Invalid character selected.")
        st.session_state.output_char_select = "Select a character..."
        return
    st.session_state.previous_selected_comp = st.session_state.selected_comp
    st.session_state.selected_comp = selected_char
    st.session_state.text_input_comp = selected_char
    st.session_state.page = 1
    st.session_state.idc_refresh = not st.session_state.idc_refresh

def on_reset_filters():
    st.session_state.stroke_count = 0
    st.session_state.component_idc = "No Filter"
    st.session_state.selected_idc = "No Filter"
    st.session_state.text_input_comp = st.session_state.selected_comp
    st.session_state.page = 1
    st.session_state.idc_refresh = not st.session_state.idc_refresh

def is_reset_needed():
    return (
        st.session_state.stroke_count != 0 or
        st.session_state.component_idc != "No Filter" or
        st.session_state.selected_idc != "No Filter"
    )

def render_controls(component_map):
    idc_descriptions = {
        "No Filter": "No Filter",
        "⿰": "Left Right",
        "⿱": "Top Bottom",
        "⿲": "Left Middle Right",
        "⿳": "Top Middle Bottom",
        "⿴": "Surround",
        "⿵": "Surround Top",
        "⿶": "Surround Bottom",
        "⿷": "Surround Left",
        "⿸": "Top Left Corner",
        "⿹": "Top Right Corner",
        "⿺": "Bottom Left Corner",
        "⿻": "Overlaid"
    }

    with st.container():
        st.markdown("### Select Input Component")
        st.caption("Choose or type a single character to explore its related characters.")
        col1, col2, col3, col4 = st.columns([1.5, 0.2, 0.4, 0.9])

        with col1:
            stroke_counts = sorted(set(get_stroke_count(comp) for comp in component_map if get_stroke_count(comp) != -1))
            component_idc_options = {"No Filter"} | {
                char_decomp.get(comp, {}).get("decomposition", "")[0]
                for comp in component_map
                if char_decomp.get(comp, {}).get("decomposition", "") and char_decomp.get(comp, {}).get("decomposition", "")[0] in IDC_CHARS
            }
            filtered_components = [
                comp for comp in component_map
                if (st.session_state.stroke_count == 0 or get_stroke_count(comp) == st.session_state.stroke_count) and
                (st.session_state.component_idc == "No Filter" or
                 char_decomp.get(comp, {}).get("decomposition", "").startswith(st.session_state.component_idc)) and
                get_stroke_count(comp) > 1
            ]
            sorted_components = sorted(filtered_components, key=get_stroke_count)
            # Ensure selected_comp is valid; if not, reset to first valid option or empty string
            if st.session_state.selected_comp not in sorted_components and sorted_components:
                st.session_state.selected_comp = sorted_components[0]
                st.session_state.text_input_comp = sorted_components[0]
            elif not sorted_components:
                st.session_state.selected_comp = ""
                st.session_state.text_input_comp = ""
                st.warning("No components match the current filters. Please adjust the stroke count or IDC filters.")

            st.selectbox(
                "Select a component:",
                options=sorted_components,
                value=st.session_state.selected_comp,
                format_func=lambda c: (
                    f"{c} ({clean_field(char_decomp.get(c, {}).get('pinyin', '—'))}, "
                    f"{char_decomp.get(c, {}).get('decomposition', '—')[0] if char_decomp.get(c, {}).get('decomposition', '') and char_decomp.get(c, {}).get('decomposition', '')[0] in IDC_CHARS else '—'}, "
                    f"{get_stroke_count(c)} strokes, {clean_field(char_decomp.get(c, {}).get('definition', 'No definition available'))})"
                ),
                key="selected_comp",
                on_change=on_selectbox_change
            )

        with col2:
            st.text_input("Or type:", key="text_input_comp", on_change=on_text_input_change, args=(component_map,))

        with col3:
            st.selectbox("Filter by Strokes:", options=[0] + stroke_counts, key="stroke_count")

        with col4:
            component_idc_options = ["No Filter"] + sorted(component_idc_options - {"No Filter"})
            st.selectbox(
                "Filter by Structure IDC:",
                options=component_idc_options,
                format_func=lambda x: f"{x} ({idc_descriptions[x]})" if x != "No Filter" else x,
                key="component_idc"
            )

    with st.container():
        st.button("Reset Filters", on_click=on_reset_filters, disabled=not is_reset_needed())

    with st.container():
        st.markdown("### Filter Output Characters")
        st.caption("Customize the output by character structure and display mode.")
        col5, col6 = st.columns(2)
        with col5:
            chars = component_map.get(st.session_state.selected_comp, [])
            dynamic_idc_options = {"No Filter"} | {
                char_decomp.get(char, {}).get("decomposition", "")[0]
                for char in chars
                if char_decomp.get(char, {}).get("decomposition", "") and char_decomp.get(char, {}).get("decomposition", "")[0] in IDC_CHARS
            }
            idc_options = ["No Filter"] + sorted(dynamic_idc_options - {"No Filter"})
            st.selectbox(
                "Result IDC:",
                options=idc_options,
                format_func=lambda x: f"{x} ({idc_descriptions.get(x, x)})" if x != "No Filter" else x,
                index=idc_options.index(st.session_state.selected_idc) if st.session_state.selected_idc in idc_options else 0,
                key="selected_idc"
            )
        with col6:
            st.radio("Output Type:", options=["Single Character", "2-Character Phrases", "3-Character Phrases", "4-Character Phrases"], key="display_mode")

def render_char_card(char, compounds):
    entry = char_decomp.get(char, {})
    decomposition = entry.get("decomposition", "")
    idc = decomposition[0] if decomposition and decomposition[0] in IDC_CHARS else "—"
    fields = {
        "Pinyin": clean_field(entry.get("pinyin", "—")),
        "Definition": clean_field(entry.get("definition", "No definition available")),
        "Radical": clean_field(entry.get("radical", "—")),
        "Hint": clean_field(entry.get("etymology", {}).get("hint", "No hint available")),
        "Strokes": f"{get_stroke_count(char)} strokes" if get_stroke_count(char) != -1 else "unknown strokes",
        "IDC": idc
    }
    details = " ".join(f"<strong>{k}:</strong> {v}" for k, v in fields.items())
    st.markdown(f"""<div class='char-card'><h3 class='char-title'>{char}</h3><p class='details'>{details}</p>""", unsafe_allow_html=True)
    if compounds and st.session_state.display_mode != "Single Character":
        compounds_text = " ".join(sorted(compounds))
        st.markdown(f"""<div class='compounds-section'><p class='compounds-title'>{st.session_state.display_mode} for {char}:</p><p class='compounds-list'>{compounds_text}</p></div>""", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    component_map = build_component_map(max_depth=5)
    st.markdown("<h1>🧩 Character Decomposition Explorer</h1>", unsafe_allow_html=True)

    render_controls(component_map)
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
    details = " ".join(f"<strong>{k}:</strong> {v}" for k, v in fields.items())
    st.markdown(f"""<div class='selected-card'><h2 class='selected-char'>{st.session_state.selected_comp}</h2><p class='details'>{details}</p></div>""", unsafe_allow_html=True)

    chars = [c for c in component_map.get(st.session_state.selected_comp, []) if c in char_decomp]
    if st.session_state.selected_idc != "No Filter":
        chars = [c for c in chars if char_decomp.get(c, {}).get("decomposition", "").startswith(st.session_state.selected_idc)]

    char_compounds = {
        c: [] if st.session_state.display_mode == "Single Character" else [
            comp for comp in char_decomp.get(c, {}).get("compounds", [])
            if len(comp) == int(st.session_state.display_mode[0])
        ]
        for c in chars
    }
    filtered_chars = chars if st.session_state.display_mode == "Single Character" else [c for c in chars if char_compounds[c]]

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
            on_change=on_output_char_select,
            args=(component_map,),
            format_func=lambda c: (
                c if c == "Select a character..." else
                f"{c} ({clean_field(char_decomp.get(c, {}).get('pinyin', '—'))}, {get_stroke_count(c)} strokes, "
                f"{clean_field(char_decomp.get(c, {}).get('definition', 'No definition available'))})"
            )
        )

    st.markdown(f"<h2 class='results-header'>🧬 Results for {st.session_state.selected_comp} — {len(filtered_chars)} result(s)</h2>", unsafe_allow_html=True)
    for char in sorted(filtered_chars, key=get_stroke_count):
        render_char_card(char, char_compounds.get(char, []))

    if filtered_chars and st.session_state.display_mode != "Single Character":
        with st.expander("Export Compounds"):
            st.caption("Copy this text to get pinyin and meanings for the displayed compounds.")
            export_text = "Give me the hanyu pinyin and meaning of each compound phrase in one line a phrase in a downloadable word file\n\n"
            export_text += "\n".join(
                compound
                for char in filtered_chars
                for compound in char_compounds.get(char, [])
            )
            st.text_area("Export Text", export_text, height=200, key="export_text")
            components.html(f"""
                <textarea id="copyTarget" style="opacity:0;position:absolute;left:-9999px;">{export_text}</textarea>
                <script>
                const copyText = document.getElementById("copyTarget");
                copyText.select();
                document.execCommand("copy");
                </script>
            """, height=0)

if __name__ == "__main__":
    main()
