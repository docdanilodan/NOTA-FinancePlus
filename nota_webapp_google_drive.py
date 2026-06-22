# -*- coding: utf-8 -*-
import os, sqlite3, datetime as dt, io, base64
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

APP_TITLE = "NOTA FinancePlus Cloud"
DB_PATH = "nota_financeplus.db"
LOGO = "financeplus_logo.jpeg"
STRUMENTI = ["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"]
STATI = ["EVASA","INEVASA","IN ATTESA"]

st.set_page_config(page_title=APP_TITLE, page_icon=LOGO if os.path.exists(LOGO) else "📌", layout="wide", initial_sidebar_state="expanded")

# CSS mobile + brand
st.markdown('''
<style>
:root { --fp-blue:#0B2E5B; --fp-red:#E84B4B; }
.block-container {padding-top: 1.4rem;}
[data-testid="stSidebar"] {background: linear-gradient(180deg,#08284f,#0b3c73); color:white;}
[data-testid="stSidebar"] * {color:white !important;}
.stButton>button {border-radius:10px; font-weight:700;}
.card {border:1px solid #e7eaf0; border-radius:18px; padding:20px; background:white; box-shadow:0 4px 18px rgba(8,40,79,.08);}
.fp-title {font-size:42px; font-weight:800; color:#252936;}
.fp-muted {color:#6b7280;}
@media(max-width: 760px){.fp-title{font-size:34px}.block-container{padding-left:1rem;padding-right:1rem}}
</style>
''', unsafe_allow_html=True)

# Safe PWA hints: non blocca mai l'app
try:
    st.markdown('''
    <link rel="manifest" href="manifest.json">
    <link rel="apple-touch-icon" href="apple-touch-icon.png">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-title" content="NOTA FinancePlus">
    ''', unsafe_allow_html=True)
except Exception:
    pass


def conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    c = conn(); cur = c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS collaboratori(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,cognome TEXT,mail TEXT,cell TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS gestori(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,cognome TEXT,mail TEXT,cell TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS aziende(id INTEGER PRIMARY KEY AUTOINCREMENT,ragione_sociale TEXT,piva TEXT,amministratore TEXT,collaboratore TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS note(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT,ora TEXT,mittente_tipo TEXT,mittente TEXT,destinatario_tipo TEXT,destinatario TEXT,azienda TEXT,banca TEXT,importo TEXT,strumento TEXT,richiesta TEXT,stato TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS eventi(id INTEGER PRIMARY KEY AUTOINCREMENT,tipo TEXT,sottotipo TEXT,data TEXT,ora TEXT,organizzatore_tipo TEXT,organizzatore TEXT,destinatario_tipo TEXT,destinatario TEXT,luogo TEXT,azienda TEXT,banca TEXT,importo TEXT,strumento TEXT,richiesta TEXT,oggetto TEXT)")
    c.commit(); c.close()

def df(table):
    c=conn()
    try: return pd.read_sql_query(f"SELECT * FROM {table}", c)
    finally: c.close()

def names(kind):
    table = "collaboratori" if kind == "Collaboratore" else "gestori"
    d = df(table)
    if d.empty: return ["Nessun nominativo presente"]
    return (d["nome"].fillna("") + " " + d["cognome"].fillna("")).str.strip().tolist()

def aziende_list():
    d=df("aziende")
    return ["Nessuna azienda presente"] if d.empty else d["ragione_sociale"].fillna("").tolist()

def insert(table, values):
    c=conn(); cur=c.cursor()
    keys=','.join(values.keys()); q=','.join(['?']*len(values))
    cur.execute(f"INSERT INTO {table}({keys}) VALUES({q})", list(values.values()))
    c.commit(); c.close()

def pdf_bytes(title, rows):
    bio=io.BytesIO(); doc=SimpleDocTemplate(bio,pagesize=A4); styles=getSampleStyleSheet(); story=[]
    story.append(Paragraph(f"<b>{title}</b>", styles['Title'])); story.append(Spacer(1,12))
    if os.path.exists(LOGO):
        story.append(Paragraph("FinancePlus.Tech - Data. Strategy. Results.", styles['Normal'])); story.append(Spacer(1,10))
    if rows:
        tbl=Table(rows, repeatRows=1)
        tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0B2E5B')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),7)]))
        story.append(tbl)
    doc.build(story); bio.seek(0); return bio.getvalue()

def sidebar():
    if os.path.exists(LOGO): st.sidebar.image(LOGO, use_container_width=True)
    st.sidebar.title("FinancePlus.Tech")
    return st.sidebar.radio("Menu", ["Dashboard","NOTA","ANAGRAFICA","CALL/VCALL","REPORT","CALENDARIO","GOOGLE DRIVE","IMPOSTAZIONI"])

def login():
    st.markdown('<div class="fp-title">NOTA FinancePlus Cloud</div>', unsafe_allow_html=True)
    st.caption("Accesso riservato - PC, iPhone, iPad e desktop")
    u=st.text_input("Utente"); p=st.text_input("Password", type="password")
    st.info("Credenziali demo: admin / admin123")
    if st.button("Entra", use_container_width=True):
        if u=="admin" and p=="admin123": st.session_state.auth=True; st.rerun()
        else: st.error("Credenziali non corrette")

def dashboard():
    st.markdown('<div class="fp-title">Dashboard</div>', unsafe_allow_html=True)
    cols=st.columns(4)
    vals=[("Note",len(df('note'))),("Aziende",len(df('aziende'))),("Video Call",len(df('eventi')[df('eventi').get('tipo','')=='Video Call']) if not df('eventi').empty else 0),("Appuntamenti",len(df('eventi')[df('eventi').get('tipo','')=='Appuntamento']) if not df('eventi').empty else 0)]
    for c,(k,v) in zip(cols,vals): c.metric(k,v)
    st.info("Usa il menu laterale per inserire note, anagrafiche, call, appuntamenti e generare report.")

def page_nota():
    tab1, tab2 = st.tabs(["Nuova nota", "Elenco note PDF / video"])
    with tab1:
        st.header("Nuova nota")
        today=dt.datetime.now()
        mt=st.selectbox("Mittente tipo", ["Collaboratore","Gestore"]); mitt=st.selectbox("Mittente", names(mt))
        dtp=st.selectbox("Destinatario tipo", ["Collaboratore","Gestore"]); dest=st.selectbox("Destinatario", names(dtp))
        azienda=st.text_input("Azienda"); banca=st.text_input("Banca"); importo=st.text_input("Importo")
        strum=st.selectbox("Strumento", STRUMENTI); richiesta=st.text_area("Richiesta", height=170); stato=st.selectbox("Stato", STATI)
        if st.button("Salva nota", type="primary", use_container_width=True):
            insert('note', {"data":today.strftime('%d/%m/%Y'),"ora":today.strftime('%H:%M'),"mittente_tipo":mt,"mittente":mitt,"destinatario_tipo":dtp,"destinatario":dest,"azienda":azienda,"banca":banca,"importo":importo,"strumento":strum,"richiesta":richiesta,"stato":stato})
            st.success("Nota salvata")
    with tab2:
        d=df('note'); st.dataframe(d, use_container_width=True)
        if not d.empty:
            rows=[list(d.columns)]+d.astype(str).values.tolist()
            st.download_button("Scarica PDF note", pdf_bytes("Elenco Note", rows), "note_financeplus.pdf", "application/pdf")

def page_anagrafica():
    tabs=st.tabs(["Inserisci Collaboratore","Inserisci Gestore","Inserisci Azienda","Elenchi PDF / video"])
    for tab,table,label in [(tabs[0],'collaboratori','Collaboratore'),(tabs[1],'gestori','Gestore')]:
        with tab:
            st.header(f"Inserisci {label}"); nome=st.text_input(f"Nome {label}"); cognome=st.text_input(f"Cognome {label}"); mail=st.text_input(f"Mail {label}"); cell=st.text_input(f"Cell {label}")
            if st.button(f"Salva {label}", key=label): insert(table,{"nome":nome,"cognome":cognome,"mail":mail,"cell":cell}); st.success("Salvato")
    with tabs[2]:
        st.header("Inserisci Azienda")
        up=st.file_uploader("Inserisci Visura/Report PDF", type=['pdf'])
        rag=st.text_input("Ragione sociale"); piva=st.text_input("P.IVA"); amm=st.text_input("Nome Cognome Amministratore")
        coll=st.selectbox("Collaboratore", names("Collaboratore"))
        if up: st.info("PDF caricato. Estrazione automatica avanzata da attivare nella prossima versione.")
        if st.button("Salva Azienda", type="primary"): insert('aziende',{"ragione_sociale":rag,"piva":piva,"amministratore":amm,"collaboratore":coll}); st.success("Azienda salvata")
    with tabs[3]:
        for t in ['collaboratori','gestori','aziende']:
            st.subheader(t.title()); d=df(t); st.dataframe(d, use_container_width=True)
            if not d.empty: st.download_button(f"PDF {t}", pdf_bytes(t.title(), [list(d.columns)]+d.astype(str).values.tolist()), f"{t}.pdf", "application/pdf")

def page_call():
    tabs=st.tabs(["Nuova Video Call","Nuovo Appuntamento","Elenco PDF / video"])
    with tabs[0]:
        sottotipo=st.selectbox("Tipo", ["PRATICA","AGGIORNAMENTO"]); now=dt.datetime.now(); orgt=st.selectbox("Organizzatore tipo", ["Collaboratore","Gestore"], key='vorgt'); org=st.selectbox("Organizzatore", names(orgt), key='vorg')
        vals={"tipo":"Video Call","sottotipo":sottotipo,"data":now.strftime('%d/%m/%Y'),"ora":now.strftime('%H:%M'),"organizzatore_tipo":orgt,"organizzatore":org}
        if sottotipo=="PRATICA":
            destt=st.selectbox("Destinatario tipo", ["Collaboratore","Gestore"], key='vdestt'); dest=st.selectbox("Destinatario", names(destt), key='vdest')
            vals.update({"destinatario_tipo":destt,"destinatario":dest,"azienda":st.selectbox("Azienda", aziende_list()),"banca":st.text_input("Banca"),"importo":st.text_input("Importo"),"strumento":st.selectbox("Strumento",STRUMENTI),"richiesta":st.text_area("Richiesta")})
        else: vals.update({"oggetto":st.text_area("Oggetto")})
        if st.button("Salva Video Call"): insert('eventi', vals); st.success("Video Call salvata")
    with tabs[1]:
        now=dt.datetime.now(); orgt=st.selectbox("Organizzatore tipo", ["Collaboratore","Gestore"], key='aorgt'); org=st.selectbox("Organizzatore", names(orgt), key='aorg'); destt=st.selectbox("Destinatario tipo", ["Collaboratore","Gestore"], key='adestt'); dest=st.selectbox("Destinatario", names(destt), key='adest')
        vals={"tipo":"Appuntamento","sottotipo":"APPUNTAMENTO","data":now.strftime('%d/%m/%Y'),"ora":now.strftime('%H:%M'),"organizzatore_tipo":orgt,"organizzatore":org,"destinatario_tipo":destt,"destinatario":dest,"luogo":st.text_input("Luogo"),"azienda":st.selectbox("Azienda", aziende_list(), key='aaz'),"banca":st.text_input("Banca", key='ab'),"importo":st.text_input("Importo", key='ai'),"strumento":st.selectbox("Strumento",STRUMENTI, key='as'),"richiesta":st.text_area("Richiesta", key='ar')}
        if st.button("Salva Appuntamento"): insert('eventi', vals); st.success("Appuntamento salvato")
    with tabs[2]:
        d=df('eventi'); st.dataframe(d, use_container_width=True)
        if not d.empty: st.download_button("PDF Call/Appuntamenti", pdf_bytes("Call e Appuntamenti", [list(d.columns)]+d.astype(str).values.tolist()), "call_appuntamenti.pdf", "application/pdf")

def page_report():
    st.header("Report")
    az=st.selectbox("Genera report per azienda", aziende_list())
    notes=df('note')
    if az and not notes.empty: notes=notes[notes['azienda'].astype(str).str.contains(str(az), case=False, na=False)]
    st.dataframe(notes, use_container_width=True)
    if st.button("Genera PDF Report"):
        rows=[list(notes.columns)]+notes.astype(str).values.tolist() if not notes.empty else [["Nessun dato"]]
        st.download_button("Scarica Report PDF", pdf_bytes("Report FinancePlus", rows), "report_financeplus.pdf", "application/pdf")

def page_calendario():
    st.header("Calendario")
    vista=st.radio("Vista", ["Mensile","Settimanale"], horizontal=True)
    d=df('eventi')
    st.dataframe(d, use_container_width=True)

def page_drive():
    st.header("Google Drive")
    st.write("Struttura consigliata: FinancePlus_NOTA / Aziende / Visure / Note / Report / Backup")
    st.warning("Collegamento API Drive avanzato da configurare con credenziali Google Cloud. Per ora puoi scaricare PDF e caricarli in Drive.")

def settings():
    st.header("Impostazioni")
    st.write("Dominio previsto: nota.financeplus.tech")
    st.write("Icona iPhone: usare 'Aggiungi a schermata Home' dopo refresh/cancellazione cache.")

def main():
    init_db()
    if 'auth' not in st.session_state: st.session_state.auth=False
    if not st.session_state.auth: login(); return
    menu=sidebar()
    {"Dashboard":dashboard,"NOTA":page_nota,"ANAGRAFICA":page_anagrafica,"CALL/VCALL":page_call,"REPORT":page_report,"CALENDARIO":page_calendario,"GOOGLE DRIVE":page_drive,"IMPOSTAZIONI":settings}[menu]()

if __name__ == "__main__": main()
