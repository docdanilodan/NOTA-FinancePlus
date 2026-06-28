
import streamlit as st
from services.db import query, execute
from pathlib import Path

DB = Path("database/financeplus_360_enterprise.db")

def render():
    st.markdown("<div class='fp-hero'><h1>Admin</h1><p>Utenti, backup, log e manutenzione.</p></div>", unsafe_allow_html=True)
    st.write("")
    t1,t2,t3 = st.tabs(["Utenti","Backup","Log"])
    with t1:
        st.dataframe(query("SELECT id,username,ruolo,nome,attivo FROM utenti"), use_container_width=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        ruolo = st.selectbox("Ruolo", ["Admin","Gestore","Collaboratore"])
        nome = st.text_input("Nome")
        if st.button("Crea utente"):
            execute("INSERT INTO utenti(username,password,ruolo,nome) VALUES(?,?,?,?)", (u,p,ruolo,nome))
            st.success("Utente creato.")
    with t2:
        if DB.exists():
            st.download_button("Scarica backup database", DB.read_bytes(), file_name="financeplus_360_enterprise_backup.db")
        else:
            st.info("Database non ancora generato.")
    with t3:
        st.dataframe(query("SELECT * FROM logs ORDER BY id DESC LIMIT 200"), use_container_width=True)
