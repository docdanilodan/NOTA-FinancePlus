
import streamlit as st
from services.db import query, execute, log
from services.utils import money, now_iso
from services.pdf import create_pdf

def aziende():
    d = query("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return d["ragione_sociale"].tolist() if len(d) else []

def render():
    st.markdown("<div class='fp-hero'><h1>Finance</h1><p>Gestione pratiche finanziarie e stato avanzamento.</p></div>", unsafe_allow_html=True)
    st.write("")
    t1,t2,t3 = st.tabs(["Nuova Pratica","Elenco","PDF"])
    with t1:
        az = st.selectbox("Azienda", [""] + aziende())
        strum = st.selectbox("Strumento", ["MUTUO","CHIROGRAFARIO","FACTORING","INVOICE TRADING","LEASING","CROWD","PRESTITO","FINANZA AGEVOLATA"])
        banca = st.text_input("Banca / Istituto")
        imp = st.text_input("Importo")
        durata = st.text_input("Durata")
        stato = st.selectbox("Stato", ["NUOVA","ISTRUTTORIA","DOCUMENTI RICHIESTI","DELIBERATA","RESPINTA","EROGATA"])
        priorita = st.selectbox("Priorità", ["ALTA","MEDIA","BASSA"])
        desc = st.text_area("Descrizione pratica", height=170)
        if st.button("Salva Pratica"):
            execute("INSERT INTO pratiche(azienda,strumento,banca,importo,durata,stato,priorita,descrizione,created_at) VALUES(?,?,?,?,?,?,?,?,?)",
                    (az,strum,banca,money(imp),durata,stato,priorita,desc,now_iso()))
            log("FINANCE","pratica creata",az)
            st.success("Pratica salvata.")
    with t2:
        st.dataframe(query("SELECT * FROM pratiche ORDER BY id DESC"), use_container_width=True)
    with t3:
        if st.button("Genera PDF Pratiche"):
            d = query("SELECT azienda,strumento,banca,importo,durata,stato,priorita,descrizione FROM pratiche ORDER BY id DESC")
            p = create_pdf("Report Pratiche FinancePlus", [("Pratiche", d)], "report_pratiche_financeplus.pdf")
            st.download_button("Scarica PDF", p.read_bytes(), file_name=p.name)
