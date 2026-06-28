
import streamlit as st

def render():
    st.markdown("<div class='fp-hero'><h1>AI</h1><p>Assistente intelligente predisposto per analisi documenti e generazione note.</p></div>", unsafe_allow_html=True)
    st.write("")
    st.info("Modulo TOP predisposto. Le integrazioni OCR/AI reali saranno nella release successiva.")
    testo = st.text_area("Incolla testo pratica/documento", height=220)
    if st.button("Crea bozza nota"):
        if testo:
            st.success("Bozza operativa generata:")
            st.write("Sintesi operativa: " + testo[:1200])
        else:
            st.warning("Inserire testo.")
