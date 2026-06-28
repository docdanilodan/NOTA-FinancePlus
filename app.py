
import os
import sqlite3
import base64
import json
from datetime import datetime, date, time, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

APP_NAME = "NOTA FinancePlus"
DB_PATH = Path("data/financeplus_360.db")
REPORT_DIR = Path("data/report")
UPLOAD_DIR = Path("data/uploads")
MANUAL_DIR = Path("manuali")
STATIC_DIR = Path("static")
for p in [DB_PATH.parent, REPORT_DIR, UPLOAD_DIR, MANUAL_DIR, STATIC_DIR]:
    p.mkdir(exist_ok=True, parents=True)

st.set_page_config(
    page_title="NOTA FinancePlus",
    page_icon="static/favicon.png" if Path("static/favicon.png").exists() else "💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

def inject_pwa_links():
    """Inject PWA/iPhone icon links without breaking Streamlit if files are missing."""
    manifest = "static/manifest.json"
    apple = "static/apple-touch-icon.png"
    favicon = "static/favicon.png"
    html = []
    if Path(manifest).exists():
        html.append(f'<link rel="manifest" href="{manifest}">')
    if Path(apple).exists():
        html.append(f'<link rel="apple-touch-icon" href="{apple}">')
    if Path(favicon).exists():
        html.append(f'<link rel="icon" type="image/png" href="{favicon}">')
    html.append('<meta name="apple-mobile-web-app-capable" content="yes">')
    html.append('<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">')
    html.append('<meta name="apple-mobile-web-app-title" content="NOTA FinancePlus">')
    st.markdown("\n".join(html), unsafe_allow_html=True)

inject_pwa_links()

def css():
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(180deg, #F7F9FC 0%, #EEF3F9 100%);}
    section[data-testid="stSidebar"] {background: #0B2E5B;}
    section[data-testid="stSidebar"] * {color: white !important;}
    .fp-card {background:#fff; border:1px solid #d9e2ef; border-radius:18px; padding:18px; box-shadow:0 6px 20px rgba(11,46,91,.08);}
    .fp-title {color:#0B2E5B; font-weight:800; letter-spacing:.3px;}
    .fp-bronze {color:#B87333;}
    .metric-card {background:#fff; border-radius:16px; padding:16px; border-left:5px solid #B87333; box-shadow:0 4px 16px rgba(0,0,0,.06);}
    </style>
    """, unsafe_allow_html=True)

css()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS utenti(
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, ruolo TEXT, nome TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS persone(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, nome TEXT, cognome TEXT, mail TEXT, cell TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS aziende(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ragione_sociale TEXT, piva TEXT, amministratore TEXT, sede TEXT, pec TEXT, collaboratore TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS note(
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ora TEXT, mittente_tipo TEXT, mittente TEXT, destinatario_tipo TEXT, destinatario TEXT,
        azienda TEXT, banca TEXT, importo TEXT, strumento TEXT, richiesta TEXT, stato TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS pratiche(
        id INTEGER PRIMARY KEY AUTOINCREMENT, azienda TEXT, tipo TEXT, banca TEXT, importo TEXT, stato TEXT, descrizione TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS eventi(
        id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, data TEXT, ora TEXT, organizzatore_tipo TEXT, organizzatore TEXT,
        destinatario_tipo TEXT, destinatario TEXT, luogo TEXT, azienda TEXT, banca TEXT, importo TEXT, strumento TEXT, richiesta TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS documenti(
        id INTEGER PRIMARY KEY AUTOINCREMENT, azienda TEXT, categoria TEXT, filename TEXT, path TEXT, note TEXT, created_at TEXT)""")
    c.execute("INSERT OR IGNORE INTO utenti(username,password,ruolo,nome) VALUES('admin','admin123','Admin','Amministratore')")
    conn.commit()
    conn.close()

def q(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def execute(sql, params=()):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(sql, params)
    conn.commit()
    conn.close()

init_db()

def logo_html(width=180):
    logo = STATIC_DIR / "financeplus_logo.jpeg"
    if logo.exists():
        data = base64.b64encode(logo.read_bytes()).decode()
        return f'<img src="data:image/jpeg;base64,{data}" width="{width}">'
    return "<h2>FinancePlus.Tech</h2>"

def login():
    col1, col2, col3 = st.columns([1,1.2,1])
    with col2:
        st.markdown("<div class='fp-card' style='text-align:center'>", unsafe_allow_html=True)
        st.markdown(logo_html(210), unsafe_allow_html=True)
        st.markdown("<h2 class='fp-title'>NOTA FinancePlus Cloud</h2>", unsafe_allow_html=True)
        u = st.text_input("Utente")
        p = st.text_input("Password", type="password")
        if st.button("Entra", use_container_width=True):
            df = q("SELECT * FROM utenti WHERE username=? AND password=?", (u,p))
            if len(df):
                st.session_state["auth"] = True
                st.session_state["user"] = df.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Credenziali non valide")
        st.caption("Accesso iniziale: admin / admin123")
        st.markdown("</div>", unsafe_allow_html=True)

def persona_select(label, tipo=None):
    if tipo:
        df = q("SELECT nome || ' ' || cognome AS nominativo FROM persone WHERE tipo=? ORDER BY cognome,nome", (tipo,))
    else:
        df = q("SELECT nome || ' ' || cognome AS nominativo FROM persone ORDER BY cognome,nome")
    opts = df["nominativo"].tolist() if len(df) else []
    if not opts:
        st.info("Nessun nominativo presente. Inserire prima Collaboratori o Gestori in Anagrafica.")
        return ""
    return st.selectbox(label, opts)

def aziende_options():
    df = q("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return df["ragione_sociale"].tolist() if len(df) else []

def save_pdf(title, sections, filename):
    path = REPORT_DIR / filename
    styles = getSampleStyleSheet()
    story = []
    logo = STATIC_DIR / "financeplus_logo.jpeg"
    if logo.exists():
        story.append(Image(str(logo), width=4*cm, height=4*cm))
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))
    for h, body in sections:
        story.append(Paragraph(h, styles["Heading2"]))
        if isinstance(body, pd.DataFrame):
            if len(body):
                table_data = [body.columns.tolist()] + body.astype(str).values.tolist()
                tbl = Table(table_data, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0B2E5B")),
                    ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                    ("GRID",(0,0),(-1,-1),0.25,colors.grey),
                    ("FONTSIZE",(0,0),(-1,-1),7),
                ]))
                story.append(tbl)
            else:
                story.append(Paragraph("Nessun dato disponibile.", styles["BodyText"]))
        else:
            story.append(Paragraph(str(body).replace("\n","<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 10))
    SimpleDocTemplate(str(path)).build(story)
    return path

def dashboard():
    st.markdown("<h1 class='fp-title'>Dashboard Direzionale</h1>", unsafe_allow_html=True)
    note = q("SELECT * FROM note")
    az = q("SELECT * FROM aziende")
    pers = q("SELECT * FROM persone")
    pr = q("SELECT * FROM pratiche")
    ev = q("SELECT * FROM eventi")
    c1,c2,c3,c4,c5 = st.columns(5)
    for col, label, val in [(c1,"Note",len(note)),(c2,"Aziende",len(az)),(c3,"Persone",len(pers)),(c4,"Pratiche",len(pr)),(c5,"Eventi",len(ev))]:
        col.markdown(f"<div class='metric-card'><b>{label}</b><h2>{val}</h2></div>", unsafe_allow_html=True)
    st.divider()
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Stato Note")
        if len(note):
            fig = px.pie(note, names="stato")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nessuna nota inserita.")
    with colB:
        st.subheader("Pratiche per stato")
        if len(pr):
            fig = px.bar(pr, x="stato", color="tipo")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nessuna pratica inserita.")

def page_note():
    st.header("NOTA")
    tab1, tab2, tab3 = st.tabs(["Nuova Nota", "Elenco Note", "PDF"])
    with tab1:
        now = datetime.now()
        col1,col2 = st.columns(2)
        data = col1.date_input("Data", now.date())
        ora = col2.time_input("Ora", now.time().replace(second=0, microsecond=0))
        mt = st.selectbox("Mittente - categoria", ["Collaboratore","Gestore"])
        mitt = persona_select("Mittente", mt)
        dt = st.selectbox("Destinatario - categoria", ["Collaboratore","Gestore"])
        dest = persona_select("Destinatario", dt)
        azienda = st.text_input("Azienda")
        banca = st.text_input("Banca")
        importo = st.text_input("Importo")
        strumento = st.selectbox("Strumento", ["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"])
        richiesta = st.text_area("Richiesta / descrizione nota", height=160)
        stato = st.selectbox("Stato", ["EVASA","INEVASA","IN ATTESA"])
        if st.button("Salva Nota", use_container_width=True):
            execute("""INSERT INTO note(data,ora,mittente_tipo,mittente,destinatario_tipo,destinatario,azienda,banca,importo,strumento,richiesta,stato,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""", (str(data),str(ora),mt,mitt,dt,dest,azienda,banca,importo,strumento,richiesta,stato,datetime.now().isoformat()))
            st.success("Nota salvata.")
    with tab2:
        df=q("SELECT * FROM note ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
    with tab3:
        if st.button("Genera PDF Note"):
            path=save_pdf("Elenco Note", [("Note", q("SELECT data,ora,mittente,destinatario,azienda,banca,importo,strumento,stato FROM note ORDER BY id DESC"))], "elenco_note.pdf")
            st.download_button("Scarica PDF", path.read_bytes(), file_name=path.name)

def page_anagrafica():
    st.header("ANAGRAFICA")
    tab1,tab2,tab3,tab4=st.tabs(["Collaboratore","Gestore","Azienda","Elenchi"])
    for tab, tipo in [(tab1,"Collaboratore"),(tab2,"Gestore")]:
        with tab:
            nome=st.text_input(f"Nome {tipo}", key=f"nome_{tipo}")
            cognome=st.text_input(f"Cognome {tipo}", key=f"cognome_{tipo}")
            mail=st.text_input(f"Mail {tipo}", key=f"mail_{tipo}")
            cell=st.text_input(f"Cell {tipo}", key=f"cell_{tipo}")
            if st.button(f"Salva {tipo}", key=f"salva_{tipo}"):
                execute("INSERT INTO persone(tipo,nome,cognome,mail,cell,created_at) VALUES(?,?,?,?,?,?)",(tipo,nome,cognome,mail,cell,datetime.now().isoformat()))
                st.success(f"{tipo} salvato.")
    with tab3:
        uploaded=st.file_uploader("Inserisci Visura/Report PDF", type=["pdf"])
        rag=st.text_input("Ragione sociale")
        piva=st.text_input("P.IVA")
        amm=st.text_input("Nome Cognome Amministratore")
        sede=st.text_input("Sede legale")
        pec=st.text_input("PEC")
        collabs=q("SELECT nome || ' ' || cognome AS nominativo FROM persone WHERE tipo='Collaboratore'")
        coll=st.selectbox("Collaboratore", collabs["nominativo"].tolist() if len(collabs) else [""])
        if uploaded:
            saved=UPLOAD_DIR / uploaded.name
            saved.write_bytes(uploaded.getvalue())
            st.info("PDF caricato. L'estrazione OCR avanzata sarà nella v2; ora puoi completare i campi manualmente.")
        if st.button("Salva Azienda"):
            execute("INSERT INTO aziende(ragione_sociale,piva,amministratore,sede,pec,collaboratore,created_at) VALUES(?,?,?,?,?,?,?)",(rag,piva,amm,sede,pec,coll,datetime.now().isoformat()))
            st.success("Azienda salvata.")
    with tab4:
        st.subheader("Collaboratori e Gestori")
        st.dataframe(q("SELECT tipo,nome,cognome,mail,cell FROM persone ORDER BY tipo,cognome"), use_container_width=True)
        st.subheader("Aziende")
        st.dataframe(q("SELECT ragione_sociale,piva,amministratore,sede,pec,collaboratore FROM aziende ORDER BY ragione_sociale"), use_container_width=True)
        if st.button("PDF Anagrafiche"):
            path=save_pdf("Anagrafiche FinancePlus", [("Persone",q("SELECT tipo,nome,cognome,mail,cell FROM persone")),("Aziende",q("SELECT ragione_sociale,piva,amministratore,sede,pec,collaboratore FROM aziende"))], "anagrafiche.pdf")
            st.download_button("Scarica PDF", path.read_bytes(), file_name=path.name)

def page_finance():
    st.header("FINANCE - Pratiche")
    tab1,tab2=st.tabs(["Nuova Pratica","Elenco"])
    with tab1:
        az=st.selectbox("Azienda", aziende_options() or [""])
        tipo=st.selectbox("Tipo pratica", ["MUTUO","CHIROGRAFARIO","FACTORING","INVOICE TRADING","CROWD","PRESTITO"])
        banca=st.text_input("Banca / Istituto")
        importo=st.text_input("Importo richiesto")
        stato=st.selectbox("Stato avanzamento", ["NUOVA","ISTRUTTORIA","DOCUMENTI RICHIESTI","DELIBERATA","RESPINTA","EROGATA"])
        descrizione=st.text_area("Descrizione", height=130)
        if st.button("Salva Pratica"):
            execute("INSERT INTO pratiche(azienda,tipo,banca,importo,stato,descrizione,created_at) VALUES(?,?,?,?,?,?,?)",(az,tipo,banca,importo,stato,descrizione,datetime.now().isoformat()))
            st.success("Pratica salvata.")
    with tab2:
        st.dataframe(q("SELECT * FROM pratiche ORDER BY id DESC"), use_container_width=True)

def page_docs():
    st.header("DOCS - Archivio Documentale")
    az=st.selectbox("Azienda", aziende_options() or [""])
    cat=st.selectbox("Categoria", ["VISURA","BILANCIO","CENTRALE RISCHI","REPORT","CONTRATTO","IDENTITA","ALTRO"])
    file=st.file_uploader("Carica documento", type=["pdf","docx","xlsx","csv","png","jpg","jpeg"])
    note=st.text_area("Note documento")
    if st.button("Salva Documento"):
        if file:
            folder=UPLOAD_DIR / re_safe(az or "Senza_Azienda")
            folder.mkdir(exist_ok=True, parents=True)
            path=folder/file.name
            path.write_bytes(file.getvalue())
            execute("INSERT INTO documenti(azienda,categoria,filename,path,note,created_at) VALUES(?,?,?,?,?,?)",(az,cat,file.name,str(path),note,datetime.now().isoformat()))
            st.success("Documento salvato.")
        else:
            st.warning("Caricare un file.")
    st.dataframe(q("SELECT azienda,categoria,filename,note,created_at FROM documenti ORDER BY id DESC"), use_container_width=True)

def re_safe(s):
    return "".join(c if c.isalnum() or c in (" ","_","-") else "_" for c in s).strip().replace(" ","_")

def page_calendar():
    st.header("CALENDAR - Agenda")
    tab1,tab2,tab3=st.tabs(["Nuova Video Call","Nuovo Appuntamento","Calendario"])
    with tab1:
        tipo=st.selectbox("Tipo Video Call", ["PRATICA","AGGIORNAMENTO"])
        data=st.date_input("Data", date.today(), key="vc_data")
        ora=st.time_input("Ora", datetime.now().time().replace(second=0,microsecond=0), key="vc_ora")
        org_t=st.selectbox("Organizzatore categoria", ["Collaboratore","Gestore"], key="vc_org_t")
        org=persona_select("Organizzatore", org_t)
        richiesta=""
        dest_t=dest=azienda=banca=importo=strumento=luogo=""
        if tipo=="PRATICA":
            dest_t=st.selectbox("Destinatario categoria", ["Collaboratore","Gestore"], key="vc_dest_t")
            dest=persona_select("Destinatario", dest_t)
            azienda=st.selectbox("Azienda", aziende_options() or [""])
            banca=st.text_input("Banca")
            importo=st.text_input("Importo")
            strumento=st.selectbox("Strumento", ["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"])
            richiesta=st.text_area("Richiesta", height=120)
        else:
            richiesta=st.text_area("Oggetto aggiornamento", height=120)
        if st.button("Salva Video Call"):
            execute("INSERT INTO eventi(categoria,data,ora,organizzatore_tipo,organizzatore,destinatario_tipo,destinatario,luogo,azienda,banca,importo,strumento,richiesta,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("VIDEO CALL - "+tipo,str(data),str(ora),org_t,org,dest_t,dest,luogo,azienda,banca,importo,strumento,richiesta,datetime.now().isoformat()))
            st.success("Video Call salvata.")
    with tab2:
        data=st.date_input("Data", date.today(), key="ap_data")
        ora=st.time_input("Ora", datetime.now().time().replace(second=0,microsecond=0), key="ap_ora")
        org_t=st.selectbox("Organizzatore categoria", ["Collaboratore","Gestore"], key="ap_org_t")
        org=persona_select("Organizzatore", org_t)
        dest_t=st.selectbox("Destinatario categoria", ["Collaboratore","Gestore"], key="ap_dest_t")
        dest=persona_select("Destinatario", dest_t)
        luogo=st.text_input("Luogo")
        azienda=st.selectbox("Azienda", aziende_options() or [""], key="ap_az")
        banca=st.text_input("Banca", key="ap_banca")
        importo=st.text_input("Importo", key="ap_imp")
        strumento=st.selectbox("Strumento", ["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"], key="ap_str")
        richiesta=st.text_area("Richiesta", height=120, key="ap_rich")
        if st.button("Salva Appuntamento"):
            execute("INSERT INTO eventi(categoria,data,ora,organizzatore_tipo,organizzatore,destinatario_tipo,destinatario,luogo,azienda,banca,importo,strumento,richiesta,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    ("APPUNTAMENTO",str(data),str(ora),org_t,org,dest_t,dest,luogo,azienda,banca,importo,strumento,richiesta,datetime.now().isoformat()))
            st.success("Appuntamento salvato.")
    with tab3:
        df=q("SELECT categoria,data,ora,organizzatore,destinatario,luogo,azienda,banca,importo,strumento,richiesta FROM eventi ORDER BY data DESC, ora DESC")
        st.dataframe(df, use_container_width=True)
        if st.button("PDF Calendario"):
            path=save_pdf("Elenco Video Call e Appuntamenti", [("Agenda",df)], "calendario_eventi.pdf")
            st.download_button("Scarica PDF", path.read_bytes(), file_name=path.name)

def page_report():
    st.header("REPORT")
    az=st.selectbox("Seleziona azienda", ["Tutte"] + aziende_options())
    if st.button("Genera Report FinancePlus"):
        filtro="" if az=="Tutte" else " WHERE azienda=?"
        params=() if az=="Tutte" else (az,)
        sections=[
            ("Note", q("SELECT data,mittente,destinatario,azienda,banca,importo,strumento,stato FROM note"+filtro+" ORDER BY id DESC", params)),
            ("Pratiche", q("SELECT azienda,tipo,banca,importo,stato,descrizione FROM pratiche"+filtro+" ORDER BY id DESC", params)),
            ("Eventi", q("SELECT categoria,data,ora,organizzatore,destinatario,azienda,banca,importo,strumento FROM eventi"+filtro+" ORDER BY data DESC", params)),
            ("Documenti", q("SELECT azienda,categoria,filename,note FROM documenti"+filtro+" ORDER BY id DESC", params)),
        ]
        path=save_pdf("Report NOTA FinancePlus", sections, "report_financeplus.pdf")
        st.success("Report generato.")
        st.download_button("Scarica Report PDF", path.read_bytes(), file_name=path.name)

def page_ai():
    st.header("AI - Assistente FinancePlus")
    st.info("Modulo predisposto. Nella v2 sarà collegato a OCR, analisi visure, bilanci e Centrale Rischi.")
    txt=st.text_area("Testo nota o pratica da sintetizzare")
    if st.button("Genera bozza nota"):
        st.write("Bozza:")
        st.success(f"Nota operativa: {txt[:500]}")

def page_drive():
    st.header("Google Drive")
    st.info("In questa v1 è predisposta la struttura. Per la sincronizzazione reale servono credenziali Google OAuth / Service Account.")
    structure = """
FinancePlus_360
- Clienti
- Aziende
- Pratiche
- Visure
- Bilanci
- Centrale_Rischi
- Report
- Note
- Backup
- Manuali
"""
    st.code(structure)
    st.write("Cartella Drive indicata:")
    st.code("https://drive.google.com/drive/folders/1PMMcslCfxkTrxEenal0fKuc39njN_yfv")

def page_manuale():
    st.header("Manuale Integrato")
    st.write("Manuali PDF e guide operative del progetto.")
    pdfs=list(MANUAL_DIR.glob("*.pdf"))+list(Path(".").glob("*.pdf"))
    if pdfs:
        for p in pdfs:
            st.download_button(f"Scarica {p.name}", p.read_bytes(), file_name=p.name)
    else:
        st.info("Caricare i manuali PDF nella cartella manuali/.")

if "auth" not in st.session_state:
    st.session_state["auth"] = False
if not st.session_state["auth"]:
    login()
    st.stop()

with st.sidebar:
    st.markdown(logo_html(140), unsafe_allow_html=True)
    st.markdown("### FinancePlus 360 Enterprise")
    choice = st.radio("Menu", ["Dashboard","NOTA","ANAGRAFICA","FINANCE","DOCS","REPORT","CALENDAR","AI","GOOGLE DRIVE","MANUALE"], label_visibility="collapsed")
    st.divider()
    if st.button("Logout"):
        st.session_state["auth"] = False
        st.rerun()

if choice=="Dashboard": dashboard()
elif choice=="NOTA": page_note()
elif choice=="ANAGRAFICA": page_anagrafica()
elif choice=="FINANCE": page_finance()
elif choice=="DOCS": page_docs()
elif choice=="REPORT": page_report()
elif choice=="CALENDAR": page_calendar()
elif choice=="AI": page_ai()
elif choice=="GOOGLE DRIVE": page_drive()
elif choice=="MANUALE": page_manuale()
