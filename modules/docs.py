
import streamlit as st
from services.db import query, execute, log
from services.utils import save_upload, safe_name, now_iso

def aziende():
    d = query("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return d["ragione_sociale"].tolist() if len(d) else []

def render():
    st.markdown("<div class='fp-hero'><h1>Docs</h1><p>Archivio documentale cloud-ready con categorie e ricerca.</p></div>", unsafe_allow_html=True)
    st.write("")
    az = st.selectbox("Azienda", [""] + aziende())
    cat = st.selectbox("Categoria", ["VISURA","BILANCIO","CENTRALE RISCHI","ESTRATTO CONTO","CONTRATTO","REPORT","IDENTITA","ALTRO"])
    f = st.file_uploader("Carica documento")
    desc = st.text_area("Descrizione documento")
    if st.button("Salva Documento"):
        if f:
            path = save_upload(f, safe_name(az))
            execute("INSERT INTO documenti(azienda,categoria,filename,path,descrizione,created_at) VALUES(?,?,?,?,?,?)",
                    (az,cat,f.name,path,desc,now_iso()))
            log("DOCS","documento salvato",f.name)
            st.success("Documento salvato.")
        else:
            st.warning("Caricare un documento.")
    d = query("SELECT azienda,categoria,filename,descrizione,created_at FROM documenti ORDER BY id DESC")
    r = st.text_input("Ricerca documenti")
    if r and len(d):
        d = d[d.astype(str).apply(lambda row: row.str.contains(r, case=False, na=False).any(), axis=1)]
    st.dataframe(d, use_container_width=True)
