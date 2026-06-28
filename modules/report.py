
import streamlit as st
from services.db import query
from services.pdf import create_pdf

def aziende():
    d = query("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return d["ragione_sociale"].tolist() if len(d) else []

def render():
    st.markdown("<div class='fp-hero'><h1>Report</h1><p>PDF professionali con logo FinancePlus, KPI e tabelle.</p></div>", unsafe_allow_html=True)
    st.write("")
    az = st.selectbox("Azienda", ["Tutte"] + aziende())
    if st.button("Genera Report Completo", use_container_width=True):
        where = "" if az == "Tutte" else " WHERE azienda=?"
        params = () if az == "Tutte" else (az,)
        sections = [
            ("Note", query("SELECT data,ora,mittente,destinatario,azienda,banca,importo,strumento,stato FROM note" + where, params)),
            ("Pratiche", query("SELECT azienda,strumento,banca,importo,durata,stato,priorita FROM pratiche" + where, params)),
            ("Documenti", query("SELECT azienda,categoria,filename,descrizione FROM documenti" + where, params)),
            ("Eventi", query("SELECT tipo,data,ora,organizzatore,destinatario,azienda,banca,importo,strumento FROM eventi" + where, params)),
        ]
        p = create_pdf("Report Completo FinancePlus 360 Enterprise", sections, "report_completo_financeplus_360.pdf")
        st.download_button("Scarica Report PDF", p.read_bytes(), file_name=p.name)
