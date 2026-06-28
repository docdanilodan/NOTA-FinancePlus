
import streamlit as st
from pathlib import Path

def render():
    st.markdown("<div class='fp-hero'><h1>Manuale Integrato</h1><p>Guide PDF e assistenza interna.</p></div>", unsafe_allow_html=True)
    st.write("")
    pdfs = list(Path("manuals").glob("*.pdf"))
    if not pdfs:
        st.info("Nessun manuale PDF presente.")
    for p in pdfs:
        st.download_button("Scarica " + p.name, p.read_bytes(), file_name=p.name)
