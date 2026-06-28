
import streamlit as st
from datetime import datetime, date
from services.db import query, execute, log
from services.utils import money, now_iso

def people(tipo):
    d = query("SELECT nome || ' ' || cognome AS n FROM anagrafiche WHERE tipo=? ORDER BY cognome,nome", (tipo,))
    return d["n"].tolist() if len(d) else []

def aziende():
    d = query("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return d["ragione_sociale"].tolist() if len(d) else []

def render():
    st.markdown("<div class='fp-hero'><h1>Calendar</h1><p>Call, video call, appuntamenti e agenda.</p></div>", unsafe_allow_html=True)
    st.write("")
    t1,t2 = st.tabs(["Nuovo Evento","Elenco"])
    with t1:
        tipo = st.selectbox("Tipo", ["VIDEO CALL - PRATICA","VIDEO CALL - AGGIORNAMENTO","APPUNTAMENTO"])
        data = st.date_input("Data", date.today())
        ora = st.time_input("Ora", datetime.now().time().replace(second=0, microsecond=0))
        ot = st.selectbox("Organizzatore categoria", ["Collaboratore","Gestore"])
        org = st.selectbox("Organizzatore", people(ot) or [""])
        dt = st.selectbox("Destinatario categoria", ["Collaboratore","Gestore"])
        dest = st.selectbox("Destinatario", people(dt) or [""])
        luogo = st.text_input("Luogo")
        az = st.selectbox("Azienda", [""] + aziende())
        banca = st.text_input("Banca")
        imp = st.text_input("Importo")
        strumento = st.selectbox("Strumento", ["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"])
        richiesta = st.text_area("Richiesta / Oggetto", height=150)
        if st.button("Salva Evento"):
            execute("INSERT INTO eventi(tipo,data,ora,organizzatore_tipo,organizzatore,destinatario_tipo,destinatario,luogo,azienda,banca,importo,strumento,richiesta,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (tipo,str(data),str(ora),ot,org,dt,dest,luogo,az,banca,money(imp),strumento,richiesta,now_iso()))
            log("CALENDAR","evento salvato",az)
            st.success("Evento salvato.")
    with t2:
        st.dataframe(query("SELECT tipo,data,ora,organizzatore,destinatario,luogo,azienda,banca,importo,strumento,richiesta FROM eventi ORDER BY data DESC, ora DESC"), use_container_width=True)
