
import streamlit as st
from services.db import query, execute, log
from services.utils import save_upload, now_iso

def people(tipo):
    d = query("SELECT nome || ' ' || cognome AS n FROM anagrafiche WHERE tipo=? ORDER BY cognome,nome", (tipo,))
    return d["n"].tolist() if len(d) else []

def render():
    st.markdown("<div class='fp-hero'><h1>Anagrafica</h1><p>Collaboratori, gestori, aziende e schede cliente.</p></div>", unsafe_allow_html=True)
    st.write("")
    t1,t2,t3,t4 = st.tabs(["Collaboratore","Gestore","Azienda","Elenchi"])
    for tab, tipo in [(t1,"Collaboratore"),(t2,"Gestore")]:
        with tab:
            nome = st.text_input("Nome", key=tipo+"nome")
            cognome = st.text_input("Cognome", key=tipo+"cognome")
            mail = st.text_input("Mail", key=tipo+"mail")
            cell = st.text_input("Cell", key=tipo+"cell")
            note = st.text_area("Note", key=tipo+"note")
            if st.button("Salva " + tipo, key=tipo+"btn"):
                execute("INSERT INTO anagrafiche(tipo,nome,cognome,mail,cell,note,created_at) VALUES(?,?,?,?,?,?,?)", (tipo,nome,cognome,mail,cell,note,now_iso()))
                log("ANAGRAFICA","salvato",tipo)
                st.success(tipo + " salvato.")
    with t3:
        f = st.file_uploader("Inserisci Visura / Report PDF", type=["pdf"])
        rag = st.text_input("Ragione sociale")
        piva = st.text_input("P.IVA")
        cf = st.text_input("Codice Fiscale")
        amm = st.text_input("Nome Cognome Amministratore")
        sede = st.text_input("Sede legale")
        pec = st.text_input("PEC")
        settore = st.text_input("Settore / ATECO")
        coll = st.selectbox("Collaboratore", people("Collaboratore") or [""])
        note = st.text_area("Note azienda")
        if f:
            save_upload(f, "visure")
            st.info("OCR automatico previsto nella prossima release; ora compila i campi manualmente.")
        if st.button("Salva Azienda"):
            execute("INSERT INTO aziende(ragione_sociale,piva,cf,amministratore,sede,pec,collaboratore,settore,note,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (rag,piva,cf,amm,sede,pec,coll,settore,note,now_iso()))
            log("AZIENDA","salvata",rag)
            st.success("Azienda salvata.")
    with t4:
        st.subheader("Collaboratori / Gestori")
        st.dataframe(query("SELECT tipo,nome,cognome,mail,cell,note FROM anagrafiche ORDER BY tipo,cognome"), use_container_width=True)
        st.subheader("Aziende")
        st.dataframe(query("SELECT ragione_sociale,piva,cf,amministratore,sede,pec,collaboratore,settore,note FROM aziende ORDER BY ragione_sociale"), use_container_width=True)
