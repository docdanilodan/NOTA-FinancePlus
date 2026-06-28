
import streamlit as st
from services.google_drive import DRIVE_FOLDER_URL, DRIVE_STRUCTURE

def render():
    st.markdown("<div class='fp-hero'><h1>Google Drive</h1><p>Archivio cloud, backup e struttura documentale.</p></div>", unsafe_allow_html=True)
    st.write("")
    st.write("Cartella Google Drive configurata:")
    st.code(DRIVE_FOLDER_URL)
    st.write("Struttura consigliata:")
    st.code(DRIVE_STRUCTURE)
    st.warning("Sincronizzazione reale da completare con credenziali Google OAuth / Service Account.")
