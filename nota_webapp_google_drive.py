
import streamlit as st
import base64
from pathlib import Path

from services.db import init_db, query, log
from modules import dashboard, nota, anagrafica, finance, docs, calendar_mod, report, ai, drive, manuale, admin

APP_NAME = "FinancePlus 360 Enterprise"
APP_VERSION = "TOP v3.0"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="static/favicon.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

def b64(path):
    p = Path(path)
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""

def logo(width=160):
    p = Path("static/financeplus_logo.jpeg")
    if p.exists():
        return f"<img src='data:image/jpeg;base64,{b64(p)}' width='{width}'>"
    return "<b>FinancePlus.Tech</b>"

def inject():
    st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="FinancePlus">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<link rel="manifest" href="static/manifest.json">
<link rel="apple-touch-icon" href="static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="static/favicon.png">
<style>
.stApp{background:linear-gradient(180deg,#F5F8FC 0%,#EDF3FA 100%)}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#071F3D,#0B2E5B)}
section[data-testid="stSidebar"] *{color:white!important}
.fp-hero{background:linear-gradient(135deg,#0B2E5B,#123E73 70%,#B87333);padding:24px;border-radius:22px;color:white;box-shadow:0 10px 30px rgba(11,46,91,.22)}
.fp-card{background:white;border:1px solid #D8E2EE;border-radius:20px;padding:18px;box-shadow:0 8px 24px rgba(10,35,66,.08)}
.fp-metric{background:white;border-radius:18px;padding:18px;border-left:6px solid #B87333;box-shadow:0 8px 22px rgba(10,35,66,.08)}
.fp-metric h2{color:#0B2E5B;margin:0;font-size:34px}
.fp-metric p{color:#5E7187;margin:0;font-weight:700}
</style>
""", unsafe_allow_html=True)

def login():
    c1,c2,c3 = st.columns([1,1.2,1])
    with c2:
        st.markdown("<div class='fp-card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown(logo(220), unsafe_allow_html=True)
        st.markdown("## FinancePlus 360 Enterprise")
        st.caption("Piattaforma cloud integrata")
        u = st.text_input("Utente")
        p = st.text_input("Password", type="password")
        if st.button("Entra", use_container_width=True):
            d = query("SELECT * FROM utenti WHERE username=? AND password=? AND attivo=1", (u,p))
            if len(d):
                st.session_state.auth = True
                st.session_state.user = d.iloc[0].to_dict()
                log("LOGIN","accesso",u)
                st.rerun()
            else:
                st.error("Credenziali non valide")
        st.info("Accesso iniziale: admin / admin123")
        st.markdown("</div>", unsafe_allow_html=True)

init_db()
inject()

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    login()
    st.stop()

with st.sidebar:
    st.markdown(logo(150), unsafe_allow_html=True)
    st.markdown("### FinancePlus 360 Enterprise")
    st.caption(APP_VERSION)
    menu = st.radio(
        "Menu",
        ["Dashboard","NOTA","Anagrafica","Finance","Docs","Report","Calendar","AI","Google Drive","Manuale","Admin"],
        label_visibility="collapsed"
    )
    st.divider()
    st.caption("Utente: " + str(st.session_state.user.get("nome","")))
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

routes = {
    "Dashboard": dashboard.render,
    "NOTA": nota.render,
    "Anagrafica": anagrafica.render,
    "Finance": finance.render,
    "Docs": docs.render,
    "Report": report.render,
    "Calendar": calendar_mod.render,
    "AI": ai.render,
    "Google Drive": drive.render,
    "Manuale": manuale.render,
    "Admin": admin.render,
}
routes[menu]()
