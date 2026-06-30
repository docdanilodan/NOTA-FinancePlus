
import sqlite3, base64, re, io, imaplib, email, html, smtplib, ssl, mimetypes, hashlib
from pathlib import Path
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime, parseaddr
from email import policy
from email.parser import BytesParser
from email.message import EmailMessage
from datetime import datetime, date
import pandas as pd
import streamlit as st
import plotly.express as px
from PyPDF2 import PdfReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm

APP_VERSION="TOP v6.2 GRAFICA ENTERPRISE"
DATA=Path("data"); UPLOADS=Path("uploads"); EXPORTS=Path("exports"); STATIC=Path("static"); MANUALS=Path("manuals"); MAILDIR=Path("mail")
for p in [DATA,UPLOADS,EXPORTS,STATIC,MANUALS,MAILDIR]: p.mkdir(parents=True,exist_ok=True)
DB=DATA/"financeplus_360_v6_1.db"
st.set_page_config(page_title="FinancePlus 360 Enterprise", page_icon="static/favicon.png", layout="wide")
st.markdown("""<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="F+.Tech">
<link rel="manifest" href="static/manifest.json">
<link rel="apple-touch-icon" href="static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="static/favicon.png">

<style>
:root{
  --fp-navy:#082746;
  --fp-navy-2:#0A315A;
  --fp-navy-3:#123C68;
  --fp-bg:#F3F6FA;
  --fp-card:#FFFFFF;
  --fp-border:#DDE6F1;
  --fp-copper:#B87333;
  --fp-copper-dark:#995F2A;
  --fp-text:#0E2742;
  --fp-muted:#7C8FA5;
  --fp-ok:#E9F8EF;
  --fp-ok-text:#217A46;
}

.stApp{
  background:var(--fp-bg)!important;
  color:var(--fp-text)!important;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
}

/* SIDEBAR */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#061E38 0%,#082746 45%,#05213E 100%)!important;
  border-right:1px solid rgba(255,255,255,.08);
  width:250px!important;
}
section[data-testid="stSidebar"] > div{
  padding-top:24px!important;
}
section[data-testid="stSidebar"] *{
  color:#FFFFFF!important;
}
section[data-testid="stSidebar"] img{
  background:#FFFFFF;
  border-radius:8px;
  padding:4px;
  box-shadow:0 10px 28px rgba(0,0,0,.25);
}
section[data-testid="stSidebar"] .stRadio > label{
  display:none!important;
}
section[data-testid="stSidebar"] [role="radiogroup"]{
  gap:8px;
}
section[data-testid="stSidebar"] [role="radiogroup"] label{
  background:rgba(255,255,255,.07)!important;
  border:1px solid rgba(255,255,255,.09)!important;
  border-radius:12px!important;
  padding:10px 12px!important;
  margin-bottom:7px!important;
  transition:all .18s ease;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover{
  background:rgba(255,255,255,.13)!important;
  border-color:rgba(184,115,51,.8)!important;
}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
  background:rgba(255,255,255,.13)!important;
  border:1px solid var(--fp-copper)!important;
  box-shadow:inset 0 0 0 1px rgba(184,115,51,.35);
}

/* MAIN */
.block-container{
  padding-top:28px!important;
  padding-left:34px!important;
  padding-right:34px!important;
  max-width:1500px!important;
}
h1,h2,h3{
  color:var(--fp-text)!important;
  letter-spacing:-.02em;
}
p,span,label,div{
  font-size:14px;
}

/* HEADER HERO stile schermata caricata */
.fp-hero{
  background:transparent!important;
  padding:0 0 14px 0!important;
  border-radius:0!important;
  color:var(--fp-text)!important;
  box-shadow:none!important;
  border-bottom:0!important;
}
.fp-hero h1{
  margin:0!important;
  font-size:28px!important;
  font-weight:800!important;
  color:var(--fp-text)!important;
}
.fp-hero p{
  margin-top:4px!important;
  color:var(--fp-muted)!important;
  font-size:14px!important;
}

/* CARDS */
.fp-card{
  background:var(--fp-card)!important;
  border:1px solid var(--fp-border)!important;
  border-radius:18px!important;
  padding:18px!important;
  box-shadow:0 8px 28px rgba(9,39,70,.06)!important;
}
.fp-metric{
  background:#FFFFFF!important;
  border:1px solid var(--fp-border)!important;
  border-radius:16px!important;
  padding:18px!important;
  border-left:0!important;
  box-shadow:0 8px 24px rgba(9,39,70,.06)!important;
  min-height:92px;
}
.fp-metric p{
  color:#7C8FA5!important;
  font-size:12px!important;
  font-weight:800!important;
  text-transform:uppercase;
  margin:0 0 8px 0!important;
  letter-spacing:.04em;
}
.fp-metric h2{
  color:#0B2E5B!important;
  margin:0!important;
  font-size:30px!important;
  font-weight:800!important;
}

/* STREAMLIT ELEMENTS */
div[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stMetric"]){
  background:#FFFFFF;
  border-radius:18px;
}
.stTabs [data-baseweb="tab-list"]{
  gap:16px;
  border-bottom:1px solid var(--fp-border);
}
.stTabs [data-baseweb="tab"]{
  color:var(--fp-text)!important;
  font-weight:700;
  padding:12px 2px;
}
.stTabs [aria-selected="true"]{
  color:var(--fp-copper)!important;
  border-bottom:2px solid var(--fp-copper)!important;
}
.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div,
.stDateInput input,
.stTimeInput input,
.stNumberInput input{
  background:#FFFFFF!important;
  border:1px solid #E0E8F2!important;
  border-radius:11px!important;
  color:var(--fp-text)!important;
  box-shadow:none!important;
}
.stTextInput input:focus,
.stTextArea textarea:focus{
  border-color:var(--fp-copper)!important;
  box-shadow:0 0 0 2px rgba(184,115,51,.12)!important;
}
.stButton > button,
.stDownloadButton > button{
  background:#EEF3FA!important;
  color:#183A5A!important;
  border:1px solid #DDE6F1!important;
  border-radius:10px!important;
  font-weight:800!important;
  min-height:38px;
  box-shadow:none!important;
}
.stButton > button:hover,
.stDownloadButton > button:hover{
  background:#DFEAF7!important;
  border-color:#C9D8E8!important;
}
.stButton > button[kind="primary"],
.stButton > button:focus,
.stDownloadButton > button:focus{
  background:linear-gradient(180deg,var(--fp-copper),var(--fp-copper-dark))!important;
  color:#FFFFFF!important;
  border-color:var(--fp-copper-dark)!important;
}
div[data-testid="stDataFrame"]{
  background:#FFFFFF!important;
  border:1px solid var(--fp-border)!important;
  border-radius:16px!important;
  overflow:hidden;
  box-shadow:0 8px 24px rgba(9,39,70,.05)!important;
}
.stAlert{
  border-radius:14px!important;
}
hr{
  margin:18px 0!important;
  border-color:#E1E9F2!important;
}

/* Stato aggiornato stile pill */
.fp-updated{
  display:inline-block;
  background:#FFF4E8;
  color:#9B5E20;
  border:1px solid #F1D4B6;
  border-radius:999px;
  padding:7px 13px;
  font-size:12px;
  font-weight:800;
  float:right;
}
</style>""",unsafe_allow_html=True)

def con(): return sqlite3.connect(DB)
def init():
    c=con();cur=c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS utenti(id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,password TEXT,ruolo TEXT,nome TEXT,attivo INTEGER DEFAULT 1)")
    cur.execute("CREATE TABLE IF NOT EXISTS anagrafiche(id INTEGER PRIMARY KEY AUTOINCREMENT,tipo TEXT,nome TEXT,cognome TEXT,mail TEXT,cell TEXT,note TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS aziende(id INTEGER PRIMARY KEY AUTOINCREMENT,ragione_sociale TEXT,piva TEXT,cf TEXT,rea TEXT,pec TEXT,sede TEXT,comune TEXT,provincia TEXT,amministratore TEXT,capitale_sociale TEXT,ateco TEXT,data_costituzione TEXT,stato_attivita TEXT,collaboratore TEXT,fonte TEXT,testo_estratto TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS note(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT,ora TEXT,mittente_tipo TEXT,mittente TEXT,destinatario_tipo TEXT,destinatario TEXT,azienda TEXT,banca TEXT,importo REAL,strumento TEXT,richiesta TEXT,stato TEXT,allegato TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS pratiche(id INTEGER PRIMARY KEY AUTOINCREMENT,azienda TEXT,strumento TEXT,banca TEXT,importo REAL,durata TEXT,stato TEXT,priorita TEXT,descrizione TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS documenti(id INTEGER PRIMARY KEY AUTOINCREMENT,azienda TEXT,categoria TEXT,filename TEXT,path TEXT,descrizione TEXT,testo_estratto TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS eventi(id INTEGER PRIMARY KEY AUTOINCREMENT,tipo TEXT,data TEXT,ora TEXT,organizzatore_tipo TEXT,organizzatore TEXT,destinatario_tipo TEXT,destinatario TEXT,luogo TEXT,azienda TEXT,banca TEXT,importo REAL,strumento TEXT,richiesta TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY AUTOINCREMENT,modulo TEXT,azione TEXT,dettaglio TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS mail_downloads(id INTEGER PRIMARY KEY AUTOINCREMENT,account_email TEXT,sender_filter TEXT,date_from TEXT,date_to TEXT,folder_path TEXT,messages_count INTEGER,attachments_count INTEGER,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS mail_messages(id INTEGER PRIMARY KEY AUTOINCREMENT,download_id INTEGER,account_email TEXT,mittente TEXT,destinatario TEXT,data TEXT,ora TEXT,oggetto TEXT,contenuto TEXT,allegati TEXT,folder_path TEXT,collaboratore TEXT,azienda TEXT,created_at TEXT)")
    cur.execute("INSERT OR IGNORE INTO utenti(username,password,ruolo,nome) VALUES('admin','admin123','Admin','Amministratore')")
    c.commit();c.close()
def q(sql,p=()): c=con();d=pd.read_sql_query(sql,c,params=p);c.close();return d
def x(sql,p=()): c=con();cur=c.cursor();cur.execute(sql,p);c.commit();c.close()
def log(m,a,d=""): x("INSERT INTO logs(modulo,azione,dettaglio,created_at) VALUES(?,?,?,?)",(m,a,d,datetime.now().isoformat()))
init()

def file_hash_bytes(data):
    try:
        return hashlib.md5(data).hexdigest()
    except Exception:
        return ""

def table_has_column(table, column):
    try:
        cols = q(f"PRAGMA table_info({table})")
        return column in cols["name"].tolist()
    except Exception:
        return False

def enhanced_schema():
    # Tabelle estese v6.1
    x("CREATE TABLE IF NOT EXISTS scadenze(id INTEGER PRIMARY KEY AUTOINCREMENT, azienda TEXT, tipo TEXT, descrizione TEXT, data_scadenza TEXT, stato TEXT, priorita TEXT, created_at TEXT)")
    x("CREATE TABLE IF NOT EXISTS banche_azienda(id INTEGER PRIMARY KEY AUTOINCREMENT, azienda TEXT, banca TEXT, referente TEXT, email TEXT, telefono TEXT, affidamento REAL, note TEXT, created_at TEXT)")
    x("CREATE TABLE IF NOT EXISTS rating_azienda(id INTEGER PRIMARY KEY AUTOINCREMENT, azienda TEXT, rating TEXT, score REAL, fascia TEXT, pd TEXT, note TEXT, created_at TEXT)")
    x("CREATE TABLE IF NOT EXISTS login_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, esito TEXT, ip TEXT, created_at TEXT)")
    # Colonne documento per anti-duplicati
    try:
        if not table_has_column("documenti","hash_md5"):
            x("ALTER TABLE documenti ADD COLUMN hash_md5 TEXT")
    except Exception:
        pass

def make_pdf_professional(title, sections, filename, subtitle="Report FinancePlus", firma="Dott. Danilo D’Angelo"):
    out=EXPORTS/filename
    styles=getSampleStyleSheet()
    story=[]
    if (STATIC/"financeplus_logo.jpeg").exists():
        story.append(Image(str(STATIC/"financeplus_logo.jpeg"), width=5*cm, height=5*cm))
    story += [
        Paragraph(title, styles["Title"]),
        Paragraph(subtitle, styles["Heading2"]),
        Paragraph("Generato il " + datetime.now().strftime("%d/%m/%Y %H:%M"), styles["Normal"]),
        Spacer(1,18),
        Paragraph("Riepilogo iniziale", styles["Heading2"])
    ]
    riepilogo=[]
    for h,c in sections:
        if isinstance(c,pd.DataFrame):
            riepilogo.append([h, str(len(c))])
        else:
            riepilogo.append([h, "-"])
    if riepilogo:
        tbl=Table([["Sezione","Elementi"]]+riepilogo, repeatRows=1)
        tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0B2E5B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),8)]))
        story.append(tbl)
    story.append(Spacer(1,18))

    for h,content in sections:
        story.append(Paragraph(h, styles["Heading2"]))
        if isinstance(content,pd.DataFrame):
            if len(content):
                d=content.fillna("").astype(str)
                # tronca testi lunghi per stabilità PDF
                for col in d.columns:
                    d[col] = d[col].apply(lambda v: v[:350] + "..." if len(v) > 350 else v)
                table=Table([d.columns.tolist()]+d.values.tolist(), repeatRows=1)
                table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0B2E5B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),6)]))
                story.append(table)
            else:
                story.append(Paragraph("Nessun dato.", styles["Normal"]))
        else:
            story.append(Paragraph(str(content).replace("\n","<br/>"), styles["Normal"]))
        story.append(Spacer(1,12))

    story.append(Spacer(1,24))
    story.append(Paragraph("Firma", styles["Heading2"]))
    story.append(Paragraph(firma, styles["Normal"]))
    SimpleDocTemplate(str(out)).build(story)
    return out

enhanced_schema()


def b64(p): p=Path(p); return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""
def logo(w=160):
    p=STATIC/"financeplus_logo.jpeg"
    return f"<img src='data:image/jpeg;base64,{b64(p)}' width='{w}'>" if p.exists() else "<b>FinancePlus.Tech</b>"
def hero(t,s):
    st.markdown(f"<span class='fp-updated'>Aggiornato: {datetime.now().strftime('%d/%m/%Y %H:%M')}</span><div class='fp-hero'><h1>{t}</h1><p>{s}</p></div>", unsafe_allow_html=True)
    st.write("")

def money(v):
    try:return float(str(v).replace(".","").replace(",","."))
    except:return 0.0
def safe(s): return re.sub(r"[^A-Za-z0-9_ -]","_",s or "Senza_Azienda").strip().replace(" ","_")
def save_file(f,sub):
    if not f:return ""
    folder=UPLOADS/safe(sub);folder.mkdir(parents=True,exist_ok=True);p=folder/f.name;p.write_bytes(f.getvalue());return str(p)
def people(t=None):
    d=q("SELECT nome||' '||cognome n FROM anagrafiche WHERE tipo=? ORDER BY cognome,nome",(t,)) if t else q("SELECT nome||' '||cognome n FROM anagrafiche ORDER BY cognome,nome")
    return d.n.tolist() if len(d) else []
def azs():
    d=q("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return d.ragione_sociale.tolist() if len(d) else []
def pdf_text(f):
    txt=""
    try:
        r=PdfReader(io.BytesIO(f.getvalue()))
        for p in r.pages: txt+=(p.extract_text() or "")+"\n"
    except Exception: pass
    return txt
def m(text, pats):
    for pat in pats:
        mm=re.search(pat,text,flags=re.I|re.M)
        if mm:return " ".join(mm.group(1).strip().split())
    return ""
def parse(text):
    t=re.sub(r"[ \t]+"," ",text or "")
    return {
        "ragione_sociale":m(t,[r"denominazione\s*[:\-]?\s*([A-Z0-9\s\.\-&']{3,80})",r"ragione\s+sociale\s*[:\-]?\s*([A-Z0-9\s\.\-&']{3,80})",r"([A-Z0-9\s\.\-&']{3,80}\s+S\.?R\.?L\.?)"]),
        "piva":m(t,[r"partita\s+iva\s*[:\-]?\s*([0-9]{11})",r"p\.?\s*iva\s*[:\-]?\s*([0-9]{11})"]),
        "cf":m(t,[r"codice\s+fiscale\s*[:\-]?\s*([A-Z0-9]{11,16})",r"c\.?\s*f\.?\s*[:\-]?\s*([A-Z0-9]{11,16})"]),
        "rea":m(t,[r"r\.?e\.?a\.?\s*[:\-]?\s*([A-Z]{2}\s*[-]?\s*[0-9]{3,10})",r"rea\s*[:\-]?\s*([A-Z]{2}\s*[-]?\s*[0-9]{3,10})"]),
        "pec":m(t,[r"pec\s*[:\-]?\s*([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})"]),
        "sede":m(t,[r"sede\s+legale\s*[:\-]?\s*(.{5,140}?)(?:\s+pec|\s+rea|\s+codice|\s+partita|\n|$)"]),
        "amministratore":m(t,[r"amministratore\s+unico\s*[:\-]?\s*([A-ZÀ-Ü'\s]{5,80})",r"legale\s+rappresentante\s*[:\-]?\s*([A-ZÀ-Ü'\s]{5,80})"]),
        "capitale_sociale":m(t,[r"capitale\s+sociale\s*[:\-]?\s*(?:euro|€)?\s*([0-9\.\,]+)"]),
        "ateco":m(t,[r"codice\s+ateco\s*[:\-]?\s*([0-9]{2}\.?[0-9]{0,2}\.?[0-9]{0,2})",r"ateco\s*[:\-]?\s*([0-9]{2}\.?[0-9]{0,2}\.?[0-9]{0,2})"]),
        "data_costituzione":m(t,[r"data\s+costituzione\s*[:\-]?\s*([0-9]{1,2}[\/\.-][0-9]{1,2}[\/\.-][0-9]{2,4})"]),
        "stato_attivita":m(t,[r"stato\s+attivit[aà]\s*[:\-]?\s*([A-ZÀ-Ü\s]{3,60})"]),
        "comune":m(t,[r"comune\s*[:\-]?\s*([A-ZÀ-Ü\s']{3,60})"]),
        "provincia":m(t,[r"provincia\s*[:\-]?\s*([A-Z]{2})"])
    }
def doctype(text,name=""):
    s=(text+" "+name).lower()
    if "visura" in s or "registro imprese" in s or "camera di commercio" in s:return "VISURA CCIAA"
    if "centrale rischi" in s or "banca d'italia" in s:return "CENTRALE RISCHI"
    if "bilancio" in s or "stato patrimoniale" in s:return "BILANCIO"
    if "estratto conto" in s or "movimenti" in s:return "ESTRATTO CONTO"
    return "REPORT / ALTRO"
def make_pdf(title,sections,filename):
    out=EXPORTS/filename;styles=getSampleStyleSheet();story=[]
    if (STATIC/"financeplus_logo.jpeg").exists():story.append(Image(str(STATIC/"financeplus_logo.jpeg"),width=4*cm,height=4*cm))
    story += [Paragraph(title,styles["Title"]),Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"),styles["Normal"]),Spacer(1,12)]
    for h,c in sections:
        story.append(Paragraph(h,styles["Heading2"]))
        if isinstance(c,pd.DataFrame):
            if len(c):
                d=c.fillna("").astype(str); tbl=Table([d.columns.tolist()]+d.values.tolist(),repeatRows=1)
                tbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0B2E5B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),7)])); story.append(tbl)
            else:story.append(Paragraph("Nessun dato.",styles["Normal"]))
        else:story.append(Paragraph(str(c).replace("\n","<br/>"),styles["Normal"]))
        story.append(Spacer(1,12))
    SimpleDocTemplate(str(out)).build(story);return out
def login():
    c1,c2,c3=st.columns([1,1.2,1])
    with c2:
        st.markdown("<div class='fp-card' style='text-align:center'>",unsafe_allow_html=True)
        st.markdown(logo(220),unsafe_allow_html=True)
        st.markdown("## F+.Tech")
        st.caption(APP_VERSION)
        u=st.text_input("Utente")
        p=st.text_input("Password",type="password")
        if st.button("Entra",use_container_width=True):
            d=q("SELECT * FROM utenti WHERE username=? AND password=? AND attivo=1",(u,p))
            if len(d):
                st.session_state.auth=True
                st.session_state.user=d.iloc[0].to_dict()
                x("INSERT INTO login_attempts(username,esito,ip,created_at) VALUES(?,?,?,?)", (u,"OK","",datetime.now().isoformat()))
                log("LOGIN","accesso",u)
                st.rerun()
            else:
                x("INSERT INTO login_attempts(username,esito,ip,created_at) VALUES(?,?,?,?)", (u,"KO","",datetime.now().isoformat()))
                st.error("Credenziali non valide")
        with st.expander("Recupero password"):
            st.info("Per sicurezza il recupero password è gestito dall'Admin nel modulo Admin > Cambio password.")
        st.warning("Al primo accesso cambia la password admin da Admin > Cambio password.")
        st.markdown("</div>",unsafe_allow_html=True)

def clean_mail_text(s):
    s = s or ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()

def decode_mime(s):
    try:
        return str(make_header(decode_header(s or ""))).strip()
    except Exception:
        return str(s or "").strip()

def imap_date(d):
    months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    return f"{d.day:02d}-{months[d.month-1]}-{d.year}"

def folder_period(start, end):
    return f"{start.strftime('%d-%m-%Y')}_{end.strftime('%d-%m-%Y')}"

def next_mail_start(account_email="", sender_filter=""):
    try:
        d = q("SELECT MAX(date_to) ultimo FROM mail_downloads WHERE account_email=? AND sender_filter=?", (account_email, sender_filter))
        val = d.iloc[0]["ultimo"] if len(d) else None
        if val:
            return (pd.to_datetime(val).date() + pd.Timedelta(days=1)).date()
    except Exception:
        pass
    return date(2026,1,1)

def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = str(part.get_content_disposition() or "")
            if disp == "attachment":
                continue
            if ctype == "text/plain":
                try:
                    body += part.get_content() + "\n"
                except Exception:
                    pass
        if not body:
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    try:
                        body += clean_mail_text(part.get_content()) + "\n"
                    except Exception:
                        pass
    else:
        try:
            body = msg.get_content()
        except Exception:
            body = ""
    return clean_mail_text(body)

def detect_collaboratore(text):
    text_low = (text or "").lower()
    rows = q("SELECT nome,cognome,mail FROM anagrafiche WHERE tipo='Collaboratore'")
    for _,r in rows.iterrows():
        full = f"{r.get('nome','')} {r.get('cognome','')}".strip()
        mail = str(r.get("mail","") or "")
        if (full and full.lower() in text_low) or (mail and mail.lower() in text_low):
            return full
    return ""

def detect_azienda(text):
    text_low = (text or "").lower()
    rows = q("SELECT ragione_sociale,piva,cf,pec FROM aziende")
    for _,r in rows.iterrows():
        rag = str(r.get("ragione_sociale","") or "")
        piva = str(r.get("piva","") or "")
        cf = str(r.get("cf","") or "")
        pec = str(r.get("pec","") or "")
        if (rag and rag.lower() in text_low) or (piva and piva in text_low) or (cf and cf.lower() in text_low) or (pec and pec.lower() in text_low):
            return rag
    return ""

def company_candidate_from_mail(mittente_mail, oggetto, body, allegati=None):
    full = f"{oggetto or ''} {body or ''} {' '.join(allegati or [])}"
    parsed = parse(full)
    rag = parsed.get("ragione_sociale", "").strip()
    if rag and len(rag) >= 3:
        return rag[:120]

    subject = (oggetto or "").strip()
    subject = re.sub(r"(?i)\b(richiesta|documenti|visura|bilancio|centrale rischi|report|allegati|pratica|finanziamento|fwd|fw|re)\b", " ", subject)
    subject = re.sub(r"[\[\]\(\):;,_\-]+", " ", subject)
    subject = re.sub(r"\s+", " ", subject).strip()
    if len(subject) >= 6 and len(subject.split()) <= 5:
        return subject[:120]

    mittente_mail = (mittente_mail or "").lower()
    domain = mittente_mail.split("@")[-1] if "@" in mittente_mail else ""
    generic = ["gmail.com","outlook.com","hotmail.com","yahoo.com","libero.it","icloud.com","proton.me","protonmail.com","aruba.it","pec.it","tiscali.it","virgilio.it"]
    if domain and domain not in generic:
        name = domain.split(".")[0].replace("-", " ").replace("_", " ").upper()
        return f"{name} - cliente da mail"

    return f"Cliente automatico - {mittente_mail or 'mittente sconosciuto'}"

def ensure_company_from_mail(mittente_mail, oggetto, body, allegati=None):
    full_text = f"{mittente_mail or ''} {oggetto or ''} {body or ''} {' '.join(allegati or [])}"
    existing = detect_azienda(full_text)
    if existing:
        return existing, False

    rows = q("SELECT ragione_sociale FROM aziende WHERE lower(pec)=lower(?)", (mittente_mail or "",))
    if len(rows):
        return rows.iloc[0]["ragione_sociale"], False

    rag = company_candidate_from_mail(mittente_mail, oggetto, body, allegati)
    parsed = parse(full_text)
    x("""INSERT INTO aziende(ragione_sociale,piva,cf,rea,pec,sede,comune,provincia,amministratore,capitale_sociale,ateco,data_costituzione,stato_attivita,collaboratore,fonte,testo_estratto,created_at)
         VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
      (rag, parsed.get("piva",""), parsed.get("cf",""), parsed.get("rea",""), mittente_mail or parsed.get("pec",""),
       parsed.get("sede",""), parsed.get("comune",""), parsed.get("provincia",""), parsed.get("amministratore",""),
       parsed.get("capitale_sociale",""), parsed.get("ateco",""), parsed.get("data_costituzione",""),
       parsed.get("stato_attivita",""), "", "MAIL AUTO", full_text[:50000], datetime.now().isoformat()))
    log("ANAGRAFICA", "cliente creato automaticamente da mail", rag)
    return rag, True

def send_documents_smtp(smtp_host, smtp_port, use_ssl, username, password, to_email, subject, body, docs_df, cc=""):
    msg = EmailMessage()
    msg["From"] = username
    msg["To"] = to_email
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject or "Documenti F+.Tech"
    msg.set_content(body or "In allegato i documenti selezionati.")

    attached = 0
    for _, row in docs_df.iterrows():
        path = Path(str(row.get("path","")))
        if path.exists() and path.is_file():
            ctype, encoding = mimetypes.guess_type(str(path))
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            msg.add_attachment(path.read_bytes(), maintype=maintype, subtype=subtype, filename=path.name)
            attached += 1

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, int(smtp_port), context=context) as server:
            server.login(username, password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(username, password)
            server.send_message(msg)

    log("DOCS", "invio documenti via mail", f"{attached} allegati inviati a {to_email}")
    return attached

def download_mail_imap(host, port, use_ssl, account_email, password, mailbox, sender_filter, start_date, end_date, auto_create_client=True):
    base_folder = MAILDIR / folder_period(start_date, end_date)
    base_folder.mkdir(parents=True, exist_ok=True)
    if use_ssl:
        M = imaplib.IMAP4_SSL(host, int(port))
    else:
        M = imaplib.IMAP4(host, int(port))
    M.login(account_email, password)
    M.select(mailbox or "INBOX")

    before_date = end_date + pd.Timedelta(days=1)
    if hasattr(before_date, "date"):
        before_date = before_date.date()

    criteria = f'(SINCE {imap_date(start_date)} BEFORE {imap_date(before_date)}'
    if sender_filter:
        criteria += f' FROM "{sender_filter}"'
    criteria += ')'

    status, data = M.search(None, criteria)
    if status != "OK":
        status, data = M.search(None, f'(SINCE {imap_date(start_date)} BEFORE {imap_date(before_date)})')
    ids = data[0].split() if data and data[0] else []

    x("INSERT INTO mail_downloads(account_email,sender_filter,date_from,date_to,folder_path,messages_count,attachments_count,created_at) VALUES(?,?,?,?,?,?,?,?)",
      (account_email, sender_filter, str(start_date), str(end_date), str(base_folder), 0, 0, datetime.now().isoformat()))
    download_id = q("SELECT MAX(id) id FROM mail_downloads").iloc[0]["id"]

    msg_count = 0
    att_count = 0
    auto_clients = 0

    for num in ids:
        status, msg_data = M.fetch(num, "(RFC822)")
        if status != "OK" or not msg_data:
            continue
        raw = msg_data[0][1]
        msg = BytesParser(policy=policy.default).parsebytes(raw)

        mittente_nome, mittente_mail = parseaddr(str(msg.get("From","")))
        destinatario = str(msg.get("To","") or "")
        oggetto = decode_mime(msg.get("Subject",""))
        body = get_body(msg)
        try:
            dt = parsedate_to_datetime(msg.get("Date"))
            dmail = dt.date().isoformat()
            omail = dt.strftime("%H:%M")
        except Exception:
            dmail = ""
            omail = ""

        sender_folder_name = safe(mittente_mail or mittente_nome or "mittente_sconosciuto")
        sender_folder = base_folder / sender_folder_name
        sender_folder.mkdir(parents=True, exist_ok=True)

        allegati = []
        allegati_paths = []
        for part in msg.iter_attachments():
            fname = decode_mime(part.get_filename() or "allegato")
            fname = safe(fname)
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    out = sender_folder / fname
                    if out.exists():
                        stem, suffix = out.stem, out.suffix
                        k = 2
                        while (sender_folder / f"{stem}_{k}{suffix}").exists():
                            k += 1
                        out = sender_folder / f"{stem}_{k}{suffix}"
                    out.write_bytes(payload)
                    allegati.append(out.name)
                    allegati_paths.append(str(out))
                    att_count += 1
            except Exception:
                pass

        full_text = f"{mittente_mail} {destinatario} {oggetto} {body} {' '.join(allegati)}"
        coll = detect_collaboratore(full_text)
        az = detect_azienda(full_text)

        if auto_create_client and not az:
            az, created = ensure_company_from_mail(mittente_mail or mittente_nome, oggetto, body, allegati)
            if created:
                auto_clients += 1

        for apath, aname in zip(allegati_paths, allegati):
            x("INSERT INTO documenti(azienda,categoria,filename,path,descrizione,testo_estratto,created_at) VALUES(?,?,?,?,?,?,?)",
              (az, "MAIL", aname, apath, f"Allegato mail da {mittente_mail or mittente_nome} - {oggetto}", body[:10000], datetime.now().isoformat()))

        x("INSERT INTO mail_messages(download_id,account_email,mittente,destinatario,data,ora,oggetto,contenuto,allegati,folder_path,collaboratore,azienda,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (int(download_id), account_email, mittente_mail or mittente_nome, destinatario, dmail, omail, oggetto, body[:10000], ", ".join(allegati), str(sender_folder), coll, az, datetime.now().isoformat()))
        msg_count += 1

    x("UPDATE mail_downloads SET messages_count=?, attachments_count=? WHERE id=?", (msg_count, att_count, int(download_id)))
    M.close()
    M.logout()
    log("MAIL", "scarico completato", f"{msg_count} mail, {att_count} allegati, {auto_clients} clienti creati")
    return msg_count, att_count, str(base_folder), auto_clients

def page_mail():
    hero("📥 Scarica Mail", "Scarico email e allegati, creazione automatica cliente e report PDF.")
    t1,t2,t3,t4 = st.tabs(["Scarica Mail", "R/Mail", "R/Collaboratori", "R/Aziende"])

    with t1:
        st.subheader("Parametri casella mail")
        c1,c2 = st.columns(2)
        host = c1.text_input("Server IMAP", value="imaps.aruba.it")
        port = c2.number_input("Porta", value=993, step=1)
        use_ssl = st.checkbox("Usa SSL", value=True)
        account_email = c1.text_input("Email account da cui scaricare")
        password = c2.text_input("Password / App Password", type="password")
        mailbox = st.text_input("Cartella IMAP", value="INBOX")
        sender_filter = st.text_input("Scarica solo mail ricevute da questo mittente", placeholder="lascia vuoto per tutte")
        auto_create = st.checkbox("Se non trova il cliente in anagrafica, crealo automaticamente", value=True)

        suggested = next_mail_start(account_email, sender_filter) if account_email else date(2026,1,1)
        c3,c4 = st.columns(2)
        start = c3.date_input("Data inizio scarico", value=suggested)
        end = c4.date_input("Data fine scarico", value=date.today())

        st.caption("Le cartelle vengono create in: mail / data_inizio_data_fine / mittente. Gli allegati entrano anche in Docs.")

        cbtn1,cbtn2 = st.columns(2)
        scarica = cbtn1.button("Scarica Mail", use_container_width=True)
        scarica_tutte = cbtn2.button("Scarica tutte le mail nuove", use_container_width=True)

        if scarica_tutte and account_email:
            start = next_mail_start(account_email, "")
            sender_filter = ""
            end = date.today()

        if scarica or scarica_tutte:
            if not host or not account_email or not password:
                st.error("Inserisci server IMAP, email account e password/app password.")
            elif end < start:
                st.error("La data fine non può essere precedente alla data inizio.")
            else:
                with st.spinner("Scarico mail e allegati in corso..."):
                    try:
                        n, a, folder, auto_clients = download_mail_imap(host, port, use_ssl, account_email, password, mailbox, sender_filter, start, end, auto_create)
                        st.success(f"Scarico completato: {n} mail, {a} allegati, {auto_clients} clienti creati automaticamente.")
                        st.code(folder)
                    except Exception as e:
                        st.error("Errore durante lo scarico mail.")
                        st.exception(e)

        st.divider()
        st.subheader("Storico scarichi")
        st.dataframe(q("SELECT account_email,sender_filter,date_from,date_to,folder_path,messages_count,attachments_count,created_at FROM mail_downloads ORDER BY id DESC"), use_container_width=True)

    with t2:
        st.subheader("R/Mail - report completo")
        d = q("SELECT data,ora,mittente,azienda,oggetto,contenuto,allegati,folder_path FROM mail_messages ORDER BY data DESC, ora DESC")
        st.dataframe(d, use_container_width=True)
        if st.button("Genera PDF R/Mail", use_container_width=True):
            p = make_pdf_professional("R/Mail - Report mail scaricate", [("Mail scaricate", d)], "R_Mail_report.pdf", "Report completo mail e allegati")
            st.download_button("Scarica PDF R/Mail", p.read_bytes(), file_name=p.name)

    with t3:
        st.subheader("R/Collaboratori")
        collaboratori = people("Collaboratore")
        coll = st.selectbox("Scegli collaboratore", [""] + collaboratori)
        if coll:
            d = q("SELECT data,ora,mittente,azienda,oggetto,contenuto,allegati,folder_path FROM mail_messages WHERE collaboratore=? OR contenuto LIKE ? OR oggetto LIKE ? ORDER BY data DESC, ora DESC", (coll, f"%{coll}%", f"%{coll}%"))
        else:
            d = pd.DataFrame()
        st.dataframe(d, use_container_width=True)
        if len(d) and st.button("Genera PDF R/Collaboratori", use_container_width=True):
            p = make_pdf_professional(f"R/Collaboratori - {coll}", [("Mail collaboratore", d)], f"R_Collaboratore_{safe(coll)}.pdf", "Report mail per collaboratore")
            st.download_button("Scarica PDF Collaboratore", p.read_bytes(), file_name=p.name)

    with t4:
        st.subheader("R/Aziende")
        aziende = azs()
        az = st.selectbox("Scegli azienda", [""] + aziende)
        if az:
            d = q("SELECT data,ora,mittente,oggetto,contenuto,allegati,folder_path FROM mail_messages WHERE azienda=? OR contenuto LIKE ? OR oggetto LIKE ? ORDER BY data DESC, ora DESC", (az, f"%{az}%", f"%{az}%"))
        else:
            d = pd.DataFrame()
        st.dataframe(d, use_container_width=True)
        if len(d) and st.button("Genera PDF R/Aziende", use_container_width=True):
            p = make_pdf_professional(f"R/Aziende - {az}", [("Mail azienda", d)], f"R_Azienda_{safe(az)}.pdf", "Report mail per azienda")
            st.download_button("Scarica PDF Azienda", p.read_bytes(), file_name=p.name)

def dashboard():
    hero("Dashboard Direzionale","Pannello operativo F+.Tech: pratiche, mail, documenti, aziende, report, scadenze e rating.")
    st.markdown("### Azioni rapide")
    r1 = st.columns(4)
    for col,(label,target) in zip(r1,[("Nuova Nota","📝 NOTA"),("Nuova Pratica","💼 Pratiche"),("📁 Smart Import","📁 Smart Import"),("Scarica Mail","📥 Scarica Mail")]):
        if col.button(label, use_container_width=True):
            st.session_state["main_menu"] = target
            st.rerun()
    r2 = st.columns(4)
    for col,(label,target) in zip(r2,[("🏢 Anagrafica","🏢 Anagrafica"),("📌 Scheda Azienda","📌 Scheda Azienda"),("Documenti","📂 Documenti"),("📄 Report PDF","📄 Report PDF")]):
        if col.button(label, use_container_width=True):
            st.session_state["main_menu"] = target
            st.rerun()

    st.divider()
    pratiche_aperte = len(q("SELECT * FROM pratiche WHERE stato NOT IN ('EROGATA','RESPINTA')"))
    pratiche_delib = len(q("SELECT * FROM pratiche WHERE stato='DELIBERATA'"))
    pratiche_resp = len(q("SELECT * FROM pratiche WHERE stato='RESPINTA'"))
    mail_scaricate = len(q("SELECT * FROM mail_messages"))
    docs_caricati = len(q("SELECT * FROM documenti"))
    aziende_censite = len(q("SELECT * FROM aziende"))
    note_inevase = len(q("SELECT * FROM note WHERE stato='INEVASA'"))
    scad_prossime = len(q("SELECT * FROM scadenze WHERE stato!='EVASA' AND date(data_scadenza) <= date('now','+30 day')"))

    metrics = [
        ("Pratiche aperte", pratiche_aperte),
        ("Deliberate", pratiche_delib),
        ("Respinte", pratiche_resp),
        ("📥 Scarica Mail", mail_scaricate),
        ("Documenti", docs_caricati),
        ("Aziende", aziende_censite),
        ("Note inevase", note_inevase),
        ("Scadenze 30gg", scad_prossime),
    ]
    cols=st.columns(4)
    for i,(lab,val) in enumerate(metrics):
        cols[i%4].markdown(f"<div class='fp-metric'><p>{lab}</p><h2>{val}</h2></div>",unsafe_allow_html=True)

    st.divider()
    c1,c2=st.columns(2)
    with c1:
        st.subheader("Pratiche per stato")
        d=q("SELECT stato,COUNT(*) totale FROM pratiche GROUP BY stato")
        if len(d): st.plotly_chart(px.bar(d,x="stato",y="totale"),use_container_width=True)
        else: st.info("Nessuna pratica.")
    with c2:
        st.subheader("Scadenze per priorità")
        d=q("SELECT priorita,COUNT(*) totale FROM scadenze WHERE stato!='EVASA' GROUP BY priorita")
        if len(d): st.plotly_chart(px.pie(d,names="priorita",values="totale"),use_container_width=True)
        else: st.info("Nessuna scadenza aperta.")

    st.subheader("Scadenze prossime")
    st.dataframe(q("SELECT azienda,tipo,descrizione,data_scadenza,stato,priorita FROM scadenze WHERE stato!='EVASA' ORDER BY data_scadenza ASC LIMIT 20"), use_container_width=True)
    st.subheader("Ultime mail scaricate")
    st.dataframe(q("SELECT data,ora,mittente,azienda,oggetto,allegati FROM mail_messages ORDER BY id DESC LIMIT 10"), use_container_width=True)

def smart_import():
    hero("Smart Import Enterprise","Carica Visura/Report PDF: legge testo, riconosce il documento ed estrae i dati aziendali.")
    f=st.file_uploader("Carica PDF",type=["pdf"])
    if f:
        path=save_file(f,"smart_import"); text=pdf_text(f); typ=doctype(text,f.name); data=parse(text)
        st.success("Documento caricato: "+f.name); st.info("Tipo riconosciuto: "+typ)
        if not text.strip(): st.warning("PDF scannerizzato/non testuale: serve OCR server nella prossima release.")
        with st.expander("Testo estratto"): st.text_area("Testo",text[:15000],height=280)
        c1,c2=st.columns(2)
        rag=c1.text_input("Ragione sociale",data["ragione_sociale"]); piva=c2.text_input("P.IVA",data["piva"]); cf=c1.text_input("Codice fiscale",data["cf"]); rea=c2.text_input("REA",data["rea"])
        pec=c1.text_input("PEC",data["pec"]); sede=c2.text_input("Sede legale",data["sede"]); comune=c1.text_input("Comune",data["comune"]); provincia=c2.text_input("Provincia",data["provincia"])
        amm=c1.text_input("Amministratore",data["amministratore"]); cap=c2.text_input("Capitale sociale",data["capitale_sociale"]); ateco=c1.text_input("ATECO",data["ateco"]); dc=c2.text_input("Data costituzione",data["data_costituzione"])
        stato=c1.text_input("Stato attività",data["stato_attivita"]); coll=st.selectbox("Collaboratore assegnato",[""]+people("Collaboratore"))
        if st.button("Salva / Aggiorna Azienda da Smart Import",use_container_width=True):
            x("INSERT INTO aziende(ragione_sociale,piva,cf,rea,pec,sede,comune,provincia,amministratore,capitale_sociale,ateco,data_costituzione,stato_attivita,collaboratore,fonte,testo_estratto,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(rag,piva,cf,rea,pec,sede,comune,provincia,amm,cap,ateco,dc,stato,coll,typ,text[:50000],datetime.now().isoformat()))
            x("INSERT INTO documenti(azienda,categoria,filename,path,descrizione,testo_estratto,created_at) VALUES(?,?,?,?,?,?,?)",(rag,typ,f.name,path,"Documento acquisito da Smart Import",text[:50000],datetime.now().isoformat()))
            log("SMART IMPORT","azienda salvata",rag); st.success("Azienda e documento salvati.")

def anagrafica():
    hero("🏢 Anagrafica","Collaboratori, gestori e aziende.")
    t1,t2,t3,t4=st.tabs(["Collaboratore","Gestore","Azienda manuale","Elenchi"])
    for tab,tipo in [(t1,"Collaboratore"),(t2,"Gestore")]:
        with tab:
            nome=st.text_input("Nome",key=tipo+"n"); cog=st.text_input("Cognome",key=tipo+"c"); mail=st.text_input("📥 Scarica Mail",key=tipo+"m"); cell=st.text_input("Cell",key=tipo+"cell"); note=st.text_area("Note",key=tipo+"note")
            if st.button("Salva "+tipo,key=tipo+"btn"): x("INSERT INTO anagrafiche(tipo,nome,cognome,mail,cell,note,created_at) VALUES(?,?,?,?,?,?,?)",(tipo,nome,cog,mail,cell,note,datetime.now().isoformat())); st.success(tipo+" salvato.")
    with t3:
        rag=st.text_input("Ragione sociale"); piva=st.text_input("P.IVA"); cf=st.text_input("Codice fiscale"); pec=st.text_input("PEC"); sede=st.text_input("Sede"); amm=st.text_input("Amministratore"); coll=st.selectbox("Collaboratore",[""]+people("Collaboratore"))
        if st.button("Salva Azienda manuale"): x("INSERT INTO aziende(ragione_sociale,piva,cf,pec,sede,amministratore,collaboratore,fonte,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(rag,piva,cf,pec,sede,amm,coll,"MANUALE",datetime.now().isoformat())); st.success("Azienda salvata.")
    with t4:
        st.dataframe(q("SELECT tipo,nome,cognome,mail,cell,note FROM anagrafiche ORDER BY tipo,cognome"),use_container_width=True)
        st.dataframe(q("SELECT ragione_sociale,piva,cf,rea,pec,sede,amministratore,ateco,collaboratore,fonte FROM aziende ORDER BY id DESC"),use_container_width=True)

def nota():
    hero("📝 NOTA","Note operative con stati, strumenti e PDF.")
    t1,t2,t3=st.tabs(["Nuova Nota","Elenco / Ricerca","PDF"])
    with t1:
        c1,c2=st.columns(2); data=c1.date_input("Data",date.today()); ora=c2.time_input("Ora",datetime.now().time().replace(second=0,microsecond=0))
        mt=st.selectbox("Mittente categoria",["Collaboratore","Gestore"]); mitt=st.selectbox("Mittente",people(mt) or [""]); dt=st.selectbox("Destinatario categoria",["Collaboratore","Gestore"]); dest=st.selectbox("Destinatario",people(dt) or [""])
        az=st.selectbox("Azienda",[""]+azs()); banca=st.text_input("Banca"); imp=st.text_input("Importo"); strum=st.selectbox("Strumento",["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"]); richiesta=st.text_area("Richiesta",height=160); stato=st.selectbox("Stato",["EVASA","INEVASA","IN ATTESA"]); allegato=st.file_uploader("Allegato")
        if st.button("Salva Nota",use_container_width=True):
            path=save_file(allegato,"note") if allegato else ""; x("INSERT INTO note(data,ora,mittente_tipo,mittente,destinatario_tipo,destinatario,azienda,banca,importo,strumento,richiesta,stato,allegato,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(data),str(ora),mt,mitt,dt,dest,az,banca,money(imp),strum,richiesta,stato,path,datetime.now().isoformat())); st.success("Nota salvata.")
    with t2:
        d=q("SELECT * FROM note ORDER BY id DESC"); r=st.text_input("Ricerca")
        if r and len(d): d=d[d.astype(str).apply(lambda row: row.str.contains(r,case=False,na=False).any(),axis=1)]
        st.dataframe(d,use_container_width=True)
    with t3:
        if st.button("Genera PDF Note"): p=make_pdf("Report Note FinancePlus",[("Note",q("SELECT data,ora,mittente,destinatario,azienda,banca,importo,strumento,stato,richiesta FROM note"))],"report_note.pdf"); st.download_button("Scarica PDF",p.read_bytes(),file_name=p.name)

def finance():
    hero("💼 Pratiche","Pratiche finanziarie.")
    t1,t2,t3=st.tabs(["Nuova pratica","Elenco","PDF"])
    with t1:
        az=st.selectbox("Azienda",[""]+azs()); strum=st.selectbox("Strumento",["MUTUO","CHIROGRAFARIO","FACTORING","INVOICE TRADING","LEASING","CROWD","PRESTITO","FINANZA AGEVOLATA"]); banca=st.text_input("Banca"); imp=st.text_input("Importo"); durata=st.text_input("Durata"); stato=st.selectbox("Stato",["NUOVA","ISTRUTTORIA","DOCUMENTI RICHIESTI","DELIBERATA","RESPINTA","EROGATA"]); priorita=st.selectbox("Priorità",["ALTA","MEDIA","BASSA"]); desc=st.text_area("Descrizione")
        if st.button("Salva Pratica"): x("INSERT INTO pratiche(azienda,strumento,banca,importo,durata,stato,priorita,descrizione,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(az,strum,banca,money(imp),durata,stato,priorita,desc,datetime.now().isoformat())); st.success("Pratica salvata.")
    with t2: st.dataframe(q("SELECT * FROM pratiche ORDER BY id DESC"),use_container_width=True)
    with t3:
        if st.button("PDF Pratiche"): p=make_pdf("Report Pratiche",[("Pratiche",q("SELECT azienda,strumento,banca,importo,durata,stato,priorita,descrizione FROM pratiche"))],"report_pratiche.pdf"); st.download_button("Scarica PDF",p.read_bytes(),file_name=p.name)

def docs():
    hero("📂 Documenti","Archivio documentale, cartelle automatiche, anti-duplicati, ricerca, OCR testuale e invio via mail.")
    t1,t2,t3 = st.tabs(["Carica / Archivio", "Ricerca documenti", "Invia documenti via mail"])

    with t1:
        az=st.selectbox("Azienda",[""]+azs(), key="docs_azienda")
        cat=st.selectbox("Categoria",["VISURA","BILANCIO","CENTRALE RISCHI","ESTRATTO CONTO","CONTRATTO","REPORT","MAIL","IDENTITA","ALTRO"], key="docs_cat")
        f=st.file_uploader("Carica documento")
        desc=st.text_area("Descrizione")
        if st.button("Salva Documento"):
            if f:
                data_bytes = f.getvalue()
                h = file_hash_bytes(data_bytes)
                dup = q("SELECT id,azienda,filename FROM documenti WHERE hash_md5=?", (h,)) if h else pd.DataFrame()
                if len(dup):
                    st.warning(f"Documento duplicato già presente: ID {dup.iloc[0]['id']} - {dup.iloc[0]['filename']}")
                else:
                    if not az:
                        az = "Documenti senza azienda"
                        rows = q("SELECT id FROM aziende WHERE ragione_sociale=?", (az,))
                        if not len(rows):
                            x("INSERT INTO aziende(ragione_sociale,fonte,created_at) VALUES(?,?,?)", (az, "AUTO DOCS", datetime.now().isoformat()))
                    path=save_file(f,safe(az))
                    text=pdf_text(f) if f.name.lower().endswith(".pdf") else ""
                    x("INSERT INTO documenti(azienda,categoria,filename,path,descrizione,testo_estratto,created_at,hash_md5) VALUES(?,?,?,?,?,?,?,?)",(az,cat,f.name,path,desc,text[:50000],datetime.now().isoformat(),h))
                    st.success("Documento salvato.")
            else:
                st.warning("Carica un documento.")

        st.subheader("Archivio documenti")
        d = q("SELECT id,azienda,categoria,filename,path,descrizione,created_at FROM documenti ORDER BY id DESC")
        st.dataframe(d.drop(columns=["path"]) if len(d) else d, use_container_width=True)

    with t2:
        st.subheader("Ricerca globale documenti")
        term = st.text_input("Cerca in azienda, categoria, nome file, descrizione, testo OCR")
        d = q("SELECT id,azienda,categoria,filename,descrizione,testo_estratto,created_at FROM documenti ORDER BY id DESC")
        if term and len(d):
            mask = d.astype(str).apply(lambda row: row.str.contains(term, case=False, na=False).any(), axis=1)
            d = d[mask]
        st.dataframe(d.drop(columns=["testo_estratto"]) if len(d) else d, use_container_width=True)

    with t3:
        st.subheader("Selezione documenti")
        d = q("SELECT id,azienda,categoria,filename,path,descrizione,created_at FROM documenti ORDER BY id DESC")
        if not len(d):
            st.info("Nessun documento disponibile.")
            return

        filtro_az = st.selectbox("Filtra per azienda", ["Tutte"] + azs(), key="send_filter_az")
        filtro_cat = st.selectbox("Filtra per categoria", ["Tutte","VISURA","BILANCIO","CENTRALE RISCHI","ESTRATTO CONTO","CONTRATTO","REPORT","MAIL","IDENTITA","ALTRO"], key="send_filter_cat")
        df = d.copy()
        if filtro_az != "Tutte":
            df = df[df["azienda"] == filtro_az]
        if filtro_cat != "Tutte":
            df = df[df["categoria"] == filtro_cat]

        df["label"] = df.apply(lambda r: f"{r['id']} | {r['azienda']} | {r['categoria']} | {r['filename']}", axis=1)
        labels = st.multiselect("Seleziona uno o più documenti da inviare", df["label"].tolist())
        selected_ids = [int(x.split("|")[0].strip()) for x in labels]
        selected = df[df["id"].isin(selected_ids)]

        st.write(f"Documenti selezionati: {len(selected)}")
        if len(selected):
            st.dataframe(selected[["id","azienda","categoria","filename","descrizione","created_at"]], use_container_width=True)

        st.divider()
        st.subheader("Invio email con allegati selezionati")
        c1,c2 = st.columns(2)
        smtp_host = c1.text_input("Server SMTP", value="smtps.aruba.it")
        smtp_port = c2.number_input("Porta SMTP", value=465, step=1)
        smtp_ssl = st.checkbox("SMTP SSL", value=True)
        smtp_user = c1.text_input("Email mittente / username SMTP")
        smtp_pass = c2.text_input("Password SMTP", type="password")
        to_email = st.text_input("Destinatario")
        cc = st.text_input("CC", value="")
        subject = st.text_input("Oggetto", value="Documenti F+.Tech")
        body = st.text_area("Testo email", value="Gentile Cliente,\nsi trasmettono in allegato i documenti selezionati.\n\nCordiali saluti\nF+.Tech")
        if st.button("Invia documenti selezionati via mail", use_container_width=True):
            if not len(selected):
                st.error("Seleziona almeno un documento.")
            elif not smtp_host or not smtp_user or not smtp_pass or not to_email:
                st.error("Compila server SMTP, mittente, password e destinatario.")
            else:
                try:
                    attached = send_documents_smtp(smtp_host, smtp_port, smtp_ssl, smtp_user, smtp_pass, to_email, subject, body, selected, cc)
                    st.success(f"Email inviata con {attached} allegati.")
                except Exception as e:
                    st.error("Errore durante l'invio email.")
                    st.exception(e)

def calendar():
    hero("Calendar","Eventi e agenda.")
    t1,t2=st.tabs(["Nuovo Evento","Elenco"])
    with t1:
        tipo=st.selectbox("Tipo",["VIDEO CALL - PRATICA","VIDEO CALL - AGGIORNAMENTO","APPUNTAMENTO"]); data=st.date_input("Data",date.today()); ora=st.time_input("Ora",datetime.now().time().replace(second=0,microsecond=0)); ot=st.selectbox("Organizzatore categoria",["Collaboratore","Gestore"]); org=st.selectbox("Organizzatore",people(ot) or [""]); dt=st.selectbox("Destinatario categoria",["Collaboratore","Gestore"]); dest=st.selectbox("Destinatario",people(dt) or [""]); luogo=st.text_input("Luogo"); az=st.selectbox("Azienda",[""]+azs()); banca=st.text_input("Banca"); imp=st.text_input("Importo"); strum=st.selectbox("Strumento",["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"]); richiesta=st.text_area("Richiesta")
        if st.button("Salva Evento"): x("INSERT INTO eventi(tipo,data,ora,organizzatore_tipo,organizzatore,destinatario_tipo,destinatario,luogo,azienda,banca,importo,strumento,richiesta,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(tipo,str(data),str(ora),ot,org,dt,dest,luogo,az,banca,money(imp),strum,richiesta,datetime.now().isoformat())); st.success("Evento salvato.")
    with t2: st.dataframe(q("SELECT * FROM eventi ORDER BY data DESC, ora DESC"),use_container_width=True)

def scheda_azienda():
    hero("📌 Scheda Azienda","Vista unica cliente: anagrafica, documenti, mail, note, pratiche, report, scadenze, banche e rating.")
    aziende = azs()
    if not aziende:
        st.info("Nessuna azienda presente. Usa Smart Import, Anagrafica o Mail con creazione automatica cliente.")
        return
    az = st.selectbox("Scegli azienda", aziende)
    if not az:
        return

    t0,t1,t2,t3,t4,t5,t6,t7 = st.tabs(["Sintesi","🏢 Anagrafica","Documenti","📥 Scarica Mail","Note","Pratiche","Scadenze/Banche/Rating","PDF"])

    dati = q("SELECT * FROM aziende WHERE ragione_sociale=? ORDER BY id DESC LIMIT 1", (az,))
    docs_df = q("SELECT id,categoria,filename,descrizione,created_at FROM documenti WHERE azienda=? ORDER BY id DESC", (az,))
    mail_df = q("SELECT data,ora,mittente,oggetto,allegati FROM mail_messages WHERE azienda=? ORDER BY id DESC", (az,))
    note_df = q("SELECT data,ora,mittente,destinatario,banca,importo,strumento,stato,richiesta FROM note WHERE azienda=? ORDER BY id DESC", (az,))
    pr_df = q("SELECT strumento,banca,importo,durata,stato,priorita,descrizione,created_at FROM pratiche WHERE azienda=? ORDER BY id DESC", (az,))
    sc_df = q("SELECT tipo,descrizione,data_scadenza,stato,priorita FROM scadenze WHERE azienda=? ORDER BY data_scadenza ASC", (az,))
    ba_df = q("SELECT banca,referente,email,telefono,affidamento,note FROM banche_azienda WHERE azienda=? ORDER BY banca", (az,))
    ra_df = q("SELECT rating,score,fascia,pd,note,created_at FROM rating_azienda WHERE azienda=? ORDER BY id DESC", (az,))

    with t0:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Documenti", len(docs_df))
        c2.metric("📥 Scarica Mail", len(mail_df))
        c3.metric("Pratiche", len(pr_df))
        c4.metric("Scadenze", len(sc_df))
        if len(ra_df):
            st.info(f"Ultimo rating: {ra_df.iloc[0]['rating']} - Score {ra_df.iloc[0]['score']} - Fascia {ra_df.iloc[0]['fascia']}")
        st.dataframe(dati.T.rename(columns={0:"Valore"}) if len(dati) else dati, use_container_width=True)

    with t1:
        st.dataframe(dati.T.rename(columns={0:"Valore"}) if len(dati) else dati, use_container_width=True)

    with t2:
        st.dataframe(docs_df, use_container_width=True)

    with t3:
        st.dataframe(mail_df, use_container_width=True)

    with t4:
        st.dataframe(note_df, use_container_width=True)

    with t5:
        st.dataframe(pr_df, use_container_width=True)

    with t6:
        st.subheader("Nuova scadenza")
        c1,c2,c3 = st.columns(3)
        tipo = c1.text_input("Tipo scadenza")
        data_scad = c2.date_input("Data scadenza", value=date.today())
        priorita = c3.selectbox("Priorità", ["ALTA","MEDIA","BASSA"])
        desc = st.text_area("Descrizione scadenza")
        stato = st.selectbox("Stato scadenza", ["APERTA","IN LAVORAZIONE","EVASA"])
        if st.button("Salva scadenza"):
            x("INSERT INTO scadenze(azienda,tipo,descrizione,data_scadenza,stato,priorita,created_at) VALUES(?,?,?,?,?,?,?)", (az,tipo,desc,str(data_scad),stato,priorita,datetime.now().isoformat()))
            st.success("Scadenza salvata.")
            st.rerun()

        st.subheader("Banca / referente")
        c1,c2,c3 = st.columns(3)
        banca = c1.text_input("Banca")
        referente = c2.text_input("Referente")
        affid = c3.text_input("Affidamento")
        email_b = c1.text_input("Email referente")
        tel_b = c2.text_input("Telefono referente")
        note_b = st.text_area("Note banca")
        if st.button("Salva banca"):
            x("INSERT INTO banche_azienda(azienda,banca,referente,email,telefono,affidamento,note,created_at) VALUES(?,?,?,?,?,?,?,?)", (az,banca,referente,email_b,tel_b,money(affid),note_b,datetime.now().isoformat()))
            st.success("Banca salvata.")
            st.rerun()

        st.subheader("Rating")
        c1,c2,c3,c4 = st.columns(4)
        rating = c1.text_input("Rating", value="")
        score = c2.text_input("Score", value="")
        fascia = c3.text_input("Fascia", value="")
        pd_val = c4.text_input("PD", value="")
        note_r = st.text_area("Note rating")
        if st.button("Salva rating"):
            x("INSERT INTO rating_azienda(azienda,rating,score,fascia,pd,note,created_at) VALUES(?,?,?,?,?,?,?)", (az,rating,money(score),fascia,pd_val,note_r,datetime.now().isoformat()))
            st.success("Rating salvato.")
            st.rerun()

        st.subheader("Scadenze")
        st.dataframe(sc_df, use_container_width=True)
        st.subheader("Banche")
        st.dataframe(ba_df, use_container_width=True)
        st.subheader("Rating storico")
        st.dataframe(ra_df, use_container_width=True)

    with t7:
        if st.button("Genera PDF Scheda Azienda", use_container_width=True):
            p = make_pdf_professional(f"Scheda Azienda - {az}", [
                ("🏢 Anagrafica", dati),
                ("Documenti", docs_df),
                ("📥 Scarica Mail", mail_df),
                ("Note", note_df),
                ("Pratiche", pr_df),
                ("Scadenze", sc_df),
                ("Banche", ba_df),
                ("Rating", ra_df),
            ], f"Scheda_Azienda_{safe(az)}.pdf", "Dossier aziendale completo")
            st.download_button("Scarica PDF Scheda Azienda", p.read_bytes(), file_name=p.name)

def report():
    hero("📄 Report PDF","Report PDF professionali con copertina, logo, riepilogo e firma.")
    az=st.selectbox("Azienda",["Tutte"]+azs())
    tipo=st.selectbox("Tipo report",["Completo","Cliente/Azienda","Banca","Collaboratore","📥 Scarica Mail","Documenti"])
    if st.button("Genera Report PDF",use_container_width=True):
        pp=() if az=="Tutte" else (az,)
        wh="" if az=="Tutte" else " WHERE azienda=?"
        sections=[]
        if tipo in ["Completo","Cliente/Azienda"]:
            sections.append(("Aziende",q("SELECT ragione_sociale,piva,cf,rea,pec,sede,amministratore,ateco,fonte FROM aziende"+("" if az=="Tutte" else " WHERE ragione_sociale=?"),pp)))
        if tipo in ["Completo","📥 Scarica Mail"]:
            sections.append(("📥 Scarica Mail",q("SELECT data,ora,mittente,azienda,oggetto,allegati FROM mail_messages"+wh+" ORDER BY data DESC",pp)))
        if tipo in ["Completo","Documenti"]:
            sections.append(("Documenti",q("SELECT azienda,categoria,filename,descrizione,created_at FROM documenti"+wh+" ORDER BY id DESC",pp)))
        if tipo in ["Completo","Cliente/Azienda","Banca","Collaboratore"]:
            sections.append(("Note",q("SELECT data,mittente,destinatario,azienda,banca,importo,strumento,stato,richiesta FROM note"+wh+" ORDER BY id DESC",pp)))
            sections.append(("Pratiche",q("SELECT azienda,strumento,banca,importo,durata,stato,priorita FROM pratiche"+wh+" ORDER BY id DESC",pp)))
            sections.append(("Scadenze",q("SELECT azienda,tipo,descrizione,data_scadenza,stato,priorita FROM scadenze"+wh+" ORDER BY data_scadenza ASC",pp)))
            sections.append(("Banche",q("SELECT azienda,banca,referente,email,telefono,affidamento,note FROM banche_azienda"+wh+" ORDER BY banca",pp)))
            sections.append(("Rating",q("SELECT azienda,rating,score,fascia,pd,note,created_at FROM rating_azienda"+wh+" ORDER BY id DESC",pp)))
        p=make_pdf_professional(f"Report {tipo} - F+.Tech", sections, f"Report_{safe(tipo)}_{safe(az)}.pdf", "Report professionale FinancePlus")
        st.download_button("Scarica Report PDF",p.read_bytes(),file_name=p.name)

def ai():
    hero("AI","Assistente intelligente predisposto.")
    st.info("In v4.0 Smart Import usa parsing automatico dei PDF testuali. OCR immagini/scansioni sarà attivabile con motore OCR server.")
    txt=st.text_area("Testo documento/pratica")
    if st.button("Crea bozza nota"): st.success("Sintesi operativa: "+(txt[:1200] if txt else "Inserire testo."))

def drive():
    hero("Google Drive","Archivio cloud e backup.")
    st.code("https://drive.google.com/drive/folders/1PMMcslCfxkTrxEenal0fKuc39njN_yfv")
    st.code("FinancePlus_360\\n├── Clienti\\n├── Aziende\\n├── Pratiche\\n├── Visure\\n├── Bilanci\\n├── Centrale_Rischi\\n├── Report\\n├── Note\\n├── Backup\\n└── Manuali")
    st.warning("Sincronizzazione reale richiede credenziali Google.")

def manual():
    hero("Manuale Integrato","Manuali PDF.")
    for p in MANUALS.glob("*.pdf"): st.download_button("Scarica "+p.name,p.read_bytes(),file_name=p.name)

def admin():
    hero("Admin","Utenti, backup, sicurezza e log.")
    t1,t2,t3,t4,t5=st.tabs(["Utenti","Cambio password","Permessi","Backup","Log"])
    with t1:
        st.dataframe(q("SELECT id,username,ruolo,nome,attivo FROM utenti"),use_container_width=True)
        u=st.text_input("Username")
        p=st.text_input("Password",type="password")
        ruolo=st.selectbox("Ruolo",["Admin","Gestore","Collaboratore"])
        nome=st.text_input("Nome")
        if st.button("Crea utente"):
            x("INSERT INTO utenti(username,password,ruolo,nome) VALUES(?,?,?,?)",(u,p,ruolo,nome))
            st.success("Utente creato.")
    with t2:
        st.subheader("Cambio password utente")
        users = q("SELECT username FROM utenti ORDER BY username")
        user_list = users.username.tolist() if len(users) else []
        sel = st.selectbox("Utente", user_list)
        newpass = st.text_input("Nuova password", type="password")
        if st.button("Aggiorna password"):
            if sel and newpass:
                x("UPDATE utenti SET password=? WHERE username=?", (newpass, sel))
                log("ADMIN", "password aggiornata", sel)
                st.success("Password aggiornata.")
            else:
                st.error("Seleziona utente e inserisci nuova password.")
    with t3:
        st.subheader("Attiva / Disattiva utenti")
        users = q("SELECT id,username,ruolo,nome,attivo FROM utenti ORDER BY username")
        st.dataframe(users, use_container_width=True)
        uid = st.number_input("ID utente", min_value=1, step=1)
        stato = st.selectbox("Nuovo stato", [1,0], format_func=lambda x: "Attivo" if x==1 else "Disattivato")
        if st.button("Aggiorna stato utente"):
            x("UPDATE utenti SET attivo=? WHERE id=?", (stato, int(uid)))
            st.success("Stato aggiornato.")
    with t4:
        if DB.exists():
            st.download_button("Scarica backup database",DB.read_bytes(),file_name="financeplus_360_v6_1_backup.db")
    with t5:
        st.subheader("Accessi")
        st.dataframe(q("SELECT username,esito,ip,created_at FROM login_attempts ORDER BY id DESC LIMIT 100"),use_container_width=True)
        st.subheader("Log attività")
        st.dataframe(q("SELECT * FROM logs ORDER BY id DESC LIMIT 200"),use_container_width=True)

if "auth" not in st.session_state: st.session_state.auth=False
if not st.session_state.auth: login(); st.stop()
with st.sidebar:
    st.markdown(logo(150),unsafe_allow_html=True); st.markdown("### FinancePlus"); st.caption("Mail Archive Enterprise")
    menu=st.radio("Menu",["📊 Dashboard","📥 Scarica Mail","📁 Smart Import","📝 NOTA","🏢 Anagrafica","📌 Scheda Azienda","💼 Pratiche","📂 Documenti","📄 Report PDF","📅 Calendario","🤖 AI","☁️ Google Drive","📘 Manuale","⚙️ Impostazioni"],label_visibility="collapsed", key="main_menu")
    st.divider()
    if st.button("Logout"): st.session_state.auth=False; st.rerun()
{"📊 Dashboard":dashboard,"📥 Scarica Mail":page_mail,"📁 Smart Import":smart_import,"📝 NOTA":nota,"🏢 Anagrafica":anagrafica,"📌 Scheda Azienda":scheda_azienda,"💼 Pratiche":finance,"📂 Documenti":docs,"📄 Report PDF":report,"📅 Calendario":calendar,"🤖 AI":ai,"☁️ Google Drive":drive,"📘 Manuale":manual,"⚙️ Impostazioni":admin}[menu]()
