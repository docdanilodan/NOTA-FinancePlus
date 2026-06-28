
import streamlit as st
from datetime import datetime, date
from services.db import query, execute, log
from services.utils import money, save_upload, now_iso
from services.pdf import create_pdf

def people(tipo):
    d = query("SELECT nome || ' ' || cognome AS n FROM anagrafiche WHERE tipo=? ORDER BY cognome,nome", (tipo,))
    return d["n"].tolist() if len(d) else []

def aziende():
    d = query("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return d["ragione_sociale"].tolist() if len(d) else []

def render():
    st.markdown("<div class='fp-hero'><h1>NOTA</h1><p>Gestione note operative, stati, allegati e PDF.</p></div>", unsafe_allow_html=True)
    st.write("")
    t1,t2,t3 = st.tabs(["Nuova Nota","Elenco / Ricerca","PDF"])
    with t1:
        c1,c2 = st.columns(2)
        data = c1.date_input("Data", date.today())
        ora = c2.time_input("Ora", datetime.now().time().replace(second=0, microsecond=0))
        mt = st.selectbox("Mittente categoria", ["Collaboratore","Gestore"])
        mitt = st.selectbox("Mittente", people(mt) or [""])
        dt = st.selectbox("Destinatario categoria", ["Collaboratore","Gestore"])
        dest = st.selectbox("Destinatario", people(dt) or [""])
        az = st.selectbox("Azienda", [""] + aziende())
        banca = st.text_input("Banca")
        imp = st.text_input("Importo")
        strumento = st.selectbox("Strumento", ["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"])
        richiesta = st.text_area("Richiesta / descrizione", height=170)
        stato = st.selectbox("Stato", ["EVASA","INEVASA","IN ATTESA"])
        allegato = st.file_uploader("Allegato")
        if st.button("Salva Nota", use_container_width=True):
            path = save_upload(allegato, "note") if allegato else ""
            execute("""INSERT INTO note(data,ora,mittente_tipo,mittente,destinatario_tipo,destinatario,azienda,banca,importo,strumento,richiesta,stato,allegato,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (str(data),str(ora),mt,mitt,dt,dest,az,banca,money(imp),strumento,richiesta,stato,path,now_iso()))
            log("NOTA","creata",az)
            st.success("Nota salvata.")
    with t2:
        d = query("SELECT * FROM note ORDER BY id DESC")
        r = st.text_input("Ricerca globale")
        if r and len(d):
            d = d[d.astype(str).apply(lambda row: row.str.contains(r, case=False, na=False).any(), axis=1)]
        st.dataframe(d, use_container_width=True)
    with t3:
        if st.button("Genera PDF Note"):
            d = query("SELECT data,ora,mittente,destinatario,azienda,banca,importo,strumento,stato,richiesta FROM note ORDER BY id DESC")
            p = create_pdf("Report Note FinancePlus", [("Elenco Note", d)], "report_note_financeplus.pdf")
            st.download_button("Scarica PDF", p.read_bytes(), file_name=p.name)
