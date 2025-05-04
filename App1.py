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
