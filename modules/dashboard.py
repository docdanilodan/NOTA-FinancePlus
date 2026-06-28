
import streamlit as st
import plotly.express as px
from services.db import query

def render():
    st.markdown("<div class='fp-hero'><h1>Dashboard Direzionale</h1><p>Controllo unico di attività, pratiche, documenti, note e calendario.</p></div>", unsafe_allow_html=True)
    st.write("")
    items = [("Note","note"),("Aziende","aziende"),("Pratiche","pratiche"),("Documenti","documenti"),("Eventi","eventi")]
    cols = st.columns(5)
    for col, (label, table) in zip(cols, items):
        n = len(query(f"SELECT * FROM {table}"))
        col.markdown(f"<div class='fp-metric'><p>{label}</p><h2>{n}</h2></div>", unsafe_allow_html=True)
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Note per stato")
        d = query("SELECT stato, COUNT(*) AS totale FROM note GROUP BY stato")
        if len(d):
            st.plotly_chart(px.pie(d, names="stato", values="totale"), use_container_width=True)
        else:
            st.info("Nessuna nota.")
    with c2:
        st.subheader("Pratiche per stato")
        d = query("SELECT stato, COUNT(*) AS totale FROM pratiche GROUP BY stato")
        if len(d):
            st.plotly_chart(px.bar(d, x="stato", y="totale"), use_container_width=True)
        else:
            st.info("Nessuna pratica.")
    st.subheader("Ultime attività")
    st.dataframe(query("SELECT modulo,azione,dettaglio,created_at FROM logs ORDER BY id DESC LIMIT 30"), use_container_width=True)
