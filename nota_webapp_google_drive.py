
import sqlite3, base64, re, io, imaplib, email, html
from pathlib import Path
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime, parseaddr
from datetime import datetime, date
import pandas as pd
import streamlit as st
import plotly.express as px
from PyPDF2 import PdfReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm

APP_VERSION="TOP v4.0 SMART IMPORT"
DATA=Path("data"); UPLOADS=Path("uploads"); EXPORTS=Path("exports"); STATIC=Path("static"); MANUALS=Path("manuals"); MAILDIR=Path("mail")
for p in [DATA,UPLOADS,EXPORTS,STATIC,MANUALS,MAILDIR]: p.mkdir(parents=True,exist_ok=True)
DB=DATA/"financeplus_360_v4.db"
st.set_page_config(page_title="FinancePlus 360 Enterprise", page_icon="static/favicon.png", layout="wide")
st.markdown("""<meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="FinancePlus"><link rel="manifest" href="static/manifest.json"><link rel="apple-touch-icon" href="static/apple-touch-icon.png"><link rel="icon" type="image/png" href="static/favicon.png"><style>.stApp{background:linear-gradient(180deg,#F5F8FC 0%,#EDF3FA 100%)}section[data-testid="stSidebar"]{background:linear-gradient(180deg,#071F3D,#0B2E5B)}section[data-testid="stSidebar"] *{color:white!important}.fp-hero{background:linear-gradient(135deg,#0B2E5B,#123E73 70%,#B87333);padding:24px;border-radius:22px;color:white;box-shadow:0 10px 30px rgba(11,46,91,.22)}.fp-card{background:white;border:1px solid #D8E2EE;border-radius:20px;padding:18px;box-shadow:0 8px 24px rgba(10,35,66,.08)}.fp-metric{background:white;border-radius:18px;padding:18px;border-left:6px solid #B87333;box-shadow:0 8px 22px rgba(10,35,66,.08)}.fp-metric h2{color:#0B2E5B;margin:0;font-size:34px}.fp-metric p{color:#5E7187;margin:0;font-weight:700}</style>""",unsafe_allow_html=True)

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

def b64(p): p=Path(p); return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""
def logo(w=160):
    p=STATIC/"financeplus_logo.jpeg"
    return f"<img src='data:image/jpeg;base64,{b64(p)}' width='{w}'>" if p.exists() else "<b>FinancePlus.Tech</b>"
def hero(t,s): st.markdown(f"<div class='fp-hero'><h1>{t}</h1><p>{s}</p></div>",unsafe_allow_html=True); st.write("")
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
        st.markdown("<div class='fp-card' style='text-align:center'>",unsafe_allow_html=True);st.markdown(logo(220),unsafe_allow_html=True)
        st.markdown("## FinancePlus 360 Enterprise"); st.caption(APP_VERSION)
        u=st.text_input("Utente"); p=st.text_input("Password",type="password")
        if st.button("Entra",use_container_width=True):
            d=q("SELECT * FROM utenti WHERE username=? AND password=? AND attivo=1",(u,p))
            if len(d): st.session_state.auth=True; st.session_state.user=d.iloc[0].to_dict(); log("LOGIN","accesso",u); st.rerun()
            else: st.error("Credenziali non valide")
        st.info("Accesso iniziale: admin / admin123"); st.markdown("</div>",unsafe_allow_html=True)


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
    rows = q("SELECT ragione_sociale,piva,cf FROM aziende")
    for _,r in rows.iterrows():
        rag = str(r.get("ragione_sociale","") or "")
        piva = str(r.get("piva","") or "")
        cf = str(r.get("cf","") or "")
        if (rag and rag.lower() in text_low) or (piva and piva in text_low) or (cf and cf.lower() in text_low):
            return rag
    return ""

def download_mail_imap(host, port, use_ssl, account_email, password, mailbox, sender_filter, start_date, end_date):
    base_folder = MAILDIR / folder_period(start_date, end_date)
    base_folder.mkdir(parents=True, exist_ok=True)
    if use_ssl:
        M = imaplib.IMAP4_SSL(host, int(port))
    else:
        M = imaplib.IMAP4(host, int(port))
    M.login(account_email, password)
    M.select(mailbox or "INBOX")

    before = end_date + pd.Timedelta(days=1)
    criteria = f'(SINCE {imap_date(start_date)} BEFORE {imap_date(before.date())}'
    if sender_filter:
        criteria += f' FROM "{sender_filter}"'
    criteria += ')'

    status, data = M.search(None, criteria)
    if status != "OK":
        # fallback senza filtro mittente se il server IMAP non accetta il criterio composto
        status, data = M.search(None, f'(SINCE {imap_date(start_date)} BEFORE {imap_date(before.date())})')
    ids = data[0].split() if data and data[0] else []

    x("INSERT INTO mail_downloads(account_email,sender_filter,date_from,date_to,folder_path,messages_count,attachments_count,created_at) VALUES(?,?,?,?,?,?,?,?)",
      (account_email, sender_filter, str(start_date), str(end_date), str(base_folder), 0, 0, datetime.now().isoformat()))
    download_id = q("SELECT MAX(id) id FROM mail_downloads").iloc[0]["id"]

    msg_count = 0
    att_count = 0

    for num in ids:
        status, msg_data = M.fetch(num, "(RFC822)")
        if status != "OK" or not msg_data:
            continue
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw, policy=email.policy.default)

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
        for part in msg.iter_attachments():
            fname = decode_mime(part.get_filename() or "allegato")
            fname = safe(fname)
            try:
                payload = part.get_payload(decode=True)
                if payload:
                    out = sender_folder / fname
                    # evita sovrascrittura
                    if out.exists():
                        stem, suffix = out.stem, out.suffix
                        k = 2
                        while (sender_folder / f"{stem}_{k}{suffix}").exists():
                            k += 1
                        out = sender_folder / f"{stem}_{k}{suffix}"
                    out.write_bytes(payload)
                    allegati.append(out.name)
                    att_count += 1
            except Exception:
                pass

        full_text = f"{mittente_mail} {destinatario} {oggetto} {body}"
        coll = detect_collaboratore(full_text)
        az = detect_azienda(full_text)

        x("INSERT INTO mail_messages(download_id,account_email,mittente,destinatario,data,ora,oggetto,contenuto,allegati,folder_path,collaboratore,azienda,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
          (int(download_id), account_email, mittente_mail or mittente_nome, destinatario, dmail, omail, oggetto, body[:10000], ", ".join(allegati), str(sender_folder), coll, az, datetime.now().isoformat()))
        msg_count += 1

    x("UPDATE mail_downloads SET messages_count=?, attachments_count=? WHERE id=?", (msg_count, att_count, int(download_id)))
    M.close()
    M.logout()
    log("MAIL", "scarico completato", f"{msg_count} mail, {att_count} allegati")
    return msg_count, att_count, str(base_folder)

def page_mail():
    hero("Mail", "Scarico email e allegati, archivio per periodo/mittente e report PDF.")
    t1,t2,t3,t4 = st.tabs(["Scarica Mail", "R/Mail", "R/Collaboratori", "R/Aziende"])

    with t1:
        st.subheader("Parametri casella mail")
        c1,c2 = st.columns(2)
        host = c1.text_input("Server IMAP", value="imap.gmail.com")
        port = c2.number_input("Porta", value=993, step=1)
        use_ssl = st.checkbox("Usa SSL", value=True)
        account_email = c1.text_input("Email account da cui scaricare")
        password = c2.text_input("Password / App Password", type="password")
        mailbox = st.text_input("Cartella IMAP", value="INBOX")
        sender_filter = st.text_input("Scarica solo mail ricevute da questo mittente", placeholder="esempio@email.it")

        suggested = next_mail_start(account_email, sender_filter) if account_email else date(2026,1,1)
        c3,c4 = st.columns(2)
        start = c3.date_input("Data inizio scarico", value=suggested)
        end = c4.date_input("Data fine scarico", value=date.today())

        st.caption("Le cartelle vengono create in: mail / data_inizio_data_fine / mittente")
        if st.button("Scarica Mail", use_container_width=True):
            if not host or not account_email or not password:
                st.error("Inserisci server IMAP, email account e password/app password.")
            elif end < start:
                st.error("La data fine non può essere precedente alla data inizio.")
            else:
                with st.spinner("Scarico mail e allegati in corso..."):
                    try:
                        n, a, folder = download_mail_imap(host, port, use_ssl, account_email, password, mailbox, sender_filter, start, end)
                        st.success(f"Scarico completato: {n} mail e {a} allegati.")
                        st.code(folder)
                    except Exception as e:
                        st.error("Errore durante lo scarico mail.")
                        st.exception(e)

        st.divider()
        st.subheader("Storico scarichi")
        st.dataframe(q("SELECT account_email,sender_filter,date_from,date_to,folder_path,messages_count,attachments_count,created_at FROM mail_downloads ORDER BY id DESC"), use_container_width=True)

    with t2:
        st.subheader("R/Mail - report completo")
        d = q("SELECT data,ora,mittente,oggetto,contenuto,allegati,folder_path FROM mail_messages ORDER BY data DESC, ora DESC")
        st.dataframe(d, use_container_width=True)
        if st.button("Genera PDF R/Mail", use_container_width=True):
            p = make_pdf("R/Mail - Report mail scaricate", [("Mail scaricate", d)], "R_Mail_report.pdf")
            st.download_button("Scarica PDF R/Mail", p.read_bytes(), file_name=p.name)

    with t3:
        st.subheader("R/Collaboratori")
        collaboratori = people("Collaboratore")
        coll = st.selectbox("Scegli collaboratore", [""] + collaboratori)
        if coll:
            d = q("SELECT data,ora,mittente,oggetto,contenuto,allegati,folder_path FROM mail_messages WHERE collaboratore=? OR contenuto LIKE ? OR oggetto LIKE ? ORDER BY data DESC, ora DESC", (coll, f"%{coll}%", f"%{coll}%"))
        else:
            d = pd.DataFrame()
        st.dataframe(d, use_container_width=True)
        if len(d) and st.button("Genera PDF R/Collaboratori", use_container_width=True):
            p = make_pdf(f"R/Collaboratori - {coll}", [("Mail collaboratore", d)], f"R_Collaboratore_{safe(coll)}.pdf")
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
            p = make_pdf(f"R/Aziende - {az}", [("Mail azienda", d)], f"R_Azienda_{safe(az)}.pdf")
            st.download_button("Scarica PDF Azienda", p.read_bytes(), file_name=p.name)


def dashboard():
    hero("Dashboard Direzionale","KPI, attività, pratiche, documenti, mail e Smart Import.")
    if st.button("Apri Mail", use_container_width=True):
        st.session_state["main_menu"]="Mail"
        st.rerun()
    cols=st.columns(6)
    for col,(lab,tab) in zip(cols,[("Note","note"),("Aziende","aziende"),("Pratiche","pratiche"),("Documenti","documenti"),("Eventi","eventi"),("Mail","mail_messages")]):
        col.markdown(f"<div class='fp-metric'><p>{lab}</p><h2>{len(q(f'SELECT * FROM {tab}'))}</h2></div>",unsafe_allow_html=True)
    st.divider(); c1,c2=st.columns(2)
    with c1:
        d=q("SELECT stato,COUNT(*) totale FROM note GROUP BY stato"); st.subheader("Note per stato")
        if len(d): st.plotly_chart(px.pie(d,names="stato",values="totale"),use_container_width=True)
    with c2:
        d=q("SELECT stato,COUNT(*) totale FROM pratiche GROUP BY stato"); st.subheader("Pratiche per stato")
        if len(d): st.plotly_chart(px.bar(d,x="stato",y="totale"),use_container_width=True)
    st.dataframe(q("SELECT modulo,azione,dettaglio,created_at FROM logs ORDER BY id DESC LIMIT 50"),use_container_width=True)

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
    hero("Anagrafica","Collaboratori, gestori e aziende.")
    t1,t2,t3,t4=st.tabs(["Collaboratore","Gestore","Azienda manuale","Elenchi"])
    for tab,tipo in [(t1,"Collaboratore"),(t2,"Gestore")]:
        with tab:
            nome=st.text_input("Nome",key=tipo+"n"); cog=st.text_input("Cognome",key=tipo+"c"); mail=st.text_input("Mail",key=tipo+"m"); cell=st.text_input("Cell",key=tipo+"cell"); note=st.text_area("Note",key=tipo+"note")
            if st.button("Salva "+tipo,key=tipo+"btn"): x("INSERT INTO anagrafiche(tipo,nome,cognome,mail,cell,note,created_at) VALUES(?,?,?,?,?,?,?)",(tipo,nome,cog,mail,cell,note,datetime.now().isoformat())); st.success(tipo+" salvato.")
    with t3:
        rag=st.text_input("Ragione sociale"); piva=st.text_input("P.IVA"); cf=st.text_input("Codice fiscale"); pec=st.text_input("PEC"); sede=st.text_input("Sede"); amm=st.text_input("Amministratore"); coll=st.selectbox("Collaboratore",[""]+people("Collaboratore"))
        if st.button("Salva Azienda manuale"): x("INSERT INTO aziende(ragione_sociale,piva,cf,pec,sede,amministratore,collaboratore,fonte,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(rag,piva,cf,pec,sede,amm,coll,"MANUALE",datetime.now().isoformat())); st.success("Azienda salvata.")
    with t4:
        st.dataframe(q("SELECT tipo,nome,cognome,mail,cell,note FROM anagrafiche ORDER BY tipo,cognome"),use_container_width=True)
        st.dataframe(q("SELECT ragione_sociale,piva,cf,rea,pec,sede,amministratore,ateco,collaboratore,fonte FROM aziende ORDER BY id DESC"),use_container_width=True)

def nota():
    hero("NOTA","Note operative con stati, strumenti e PDF.")
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
    hero("Finance","Pratiche finanziarie.")
    t1,t2,t3=st.tabs(["Nuova pratica","Elenco","PDF"])
    with t1:
        az=st.selectbox("Azienda",[""]+azs()); strum=st.selectbox("Strumento",["MUTUO","CHIROGRAFARIO","FACTORING","INVOICE TRADING","LEASING","CROWD","PRESTITO","FINANZA AGEVOLATA"]); banca=st.text_input("Banca"); imp=st.text_input("Importo"); durata=st.text_input("Durata"); stato=st.selectbox("Stato",["NUOVA","ISTRUTTORIA","DOCUMENTI RICHIESTI","DELIBERATA","RESPINTA","EROGATA"]); priorita=st.selectbox("Priorità",["ALTA","MEDIA","BASSA"]); desc=st.text_area("Descrizione")
        if st.button("Salva Pratica"): x("INSERT INTO pratiche(azienda,strumento,banca,importo,durata,stato,priorita,descrizione,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(az,strum,banca,money(imp),durata,stato,priorita,desc,datetime.now().isoformat())); st.success("Pratica salvata.")
    with t2: st.dataframe(q("SELECT * FROM pratiche ORDER BY id DESC"),use_container_width=True)
    with t3:
        if st.button("PDF Pratiche"): p=make_pdf("Report Pratiche",[("Pratiche",q("SELECT azienda,strumento,banca,importo,durata,stato,priorita,descrizione FROM pratiche"))],"report_pratiche.pdf"); st.download_button("Scarica PDF",p.read_bytes(),file_name=p.name)

def docs():
    hero("Docs","Archivio documentale.")
    az=st.selectbox("Azienda",[""]+azs()); cat=st.selectbox("Categoria",["VISURA","BILANCIO","CENTRALE RISCHI","ESTRATTO CONTO","CONTRATTO","REPORT","IDENTITA","ALTRO"]); f=st.file_uploader("Carica documento"); desc=st.text_area("Descrizione")
    if st.button("Salva Documento"):
        if f:
            path=save_file(f,safe(az)); text=pdf_text(f) if f.name.lower().endswith(".pdf") else ""; x("INSERT INTO documenti(azienda,categoria,filename,path,descrizione,testo_estratto,created_at) VALUES(?,?,?,?,?,?,?)",(az,cat,f.name,path,desc,text[:50000],datetime.now().isoformat())); st.success("Documento salvato.")
        else: st.warning("Carica un documento.")
    st.dataframe(q("SELECT azienda,categoria,filename,descrizione,created_at FROM documenti ORDER BY id DESC"),use_container_width=True)

def calendar():
    hero("Calendar","Eventi e agenda.")
    t1,t2=st.tabs(["Nuovo Evento","Elenco"])
    with t1:
        tipo=st.selectbox("Tipo",["VIDEO CALL - PRATICA","VIDEO CALL - AGGIORNAMENTO","APPUNTAMENTO"]); data=st.date_input("Data",date.today()); ora=st.time_input("Ora",datetime.now().time().replace(second=0,microsecond=0)); ot=st.selectbox("Organizzatore categoria",["Collaboratore","Gestore"]); org=st.selectbox("Organizzatore",people(ot) or [""]); dt=st.selectbox("Destinatario categoria",["Collaboratore","Gestore"]); dest=st.selectbox("Destinatario",people(dt) or [""]); luogo=st.text_input("Luogo"); az=st.selectbox("Azienda",[""]+azs()); banca=st.text_input("Banca"); imp=st.text_input("Importo"); strum=st.selectbox("Strumento",["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"]); richiesta=st.text_area("Richiesta")
        if st.button("Salva Evento"): x("INSERT INTO eventi(tipo,data,ora,organizzatore_tipo,organizzatore,destinatario_tipo,destinatario,luogo,azienda,banca,importo,strumento,richiesta,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(tipo,str(data),str(ora),ot,org,dt,dest,luogo,az,banca,money(imp),strum,richiesta,datetime.now().isoformat())); st.success("Evento salvato.")
    with t2: st.dataframe(q("SELECT * FROM eventi ORDER BY data DESC, ora DESC"),use_container_width=True)

def report():
    hero("Report","Report PDF completi.")
    az=st.selectbox("Azienda",["Tutte"]+azs())
    if st.button("Genera Report Completo",use_container_width=True):
        wh="" if az=="Tutte" else " WHERE azienda=?"; pp=() if az=="Tutte" else (az,)
        p=make_pdf("Report Completo FinancePlus",[("Aziende",q("SELECT ragione_sociale,piva,cf,rea,pec,sede,amministratore,ateco,fonte FROM aziende"+("" if az=="Tutte" else " WHERE ragione_sociale=?"),pp)),("Note",q("SELECT data,mittente,destinatario,azienda,banca,importo,strumento,stato FROM note"+wh,pp)),("Pratiche",q("SELECT azienda,strumento,banca,importo,durata,stato,priorita FROM pratiche"+wh,pp)),("Documenti",q("SELECT azienda,categoria,filename,descrizione FROM documenti"+wh,pp)),("Eventi",q("SELECT tipo,data,ora,organizzatore,destinatario,azienda,banca,importo,strumento FROM eventi"+wh,pp))],"report_completo_financeplus.pdf")
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
    hero("Admin","Utenti, backup e log.")
    t1,t2,t3=st.tabs(["Utenti","Backup","Log"])
    with t1:
        st.dataframe(q("SELECT id,username,ruolo,nome,attivo FROM utenti"),use_container_width=True)
        u=st.text_input("Username"); p=st.text_input("Password",type="password"); ruolo=st.selectbox("Ruolo",["Admin","Gestore","Collaboratore"]); nome=st.text_input("Nome")
        if st.button("Crea utente"): x("INSERT INTO utenti(username,password,ruolo,nome) VALUES(?,?,?,?)",(u,p,ruolo,nome)); st.success("Utente creato.")
    with t2:
        if DB.exists(): st.download_button("Scarica backup database",DB.read_bytes(),file_name="financeplus_360_v4_backup.db")
    with t3: st.dataframe(q("SELECT * FROM logs ORDER BY id DESC LIMIT 200"),use_container_width=True)

if "auth" not in st.session_state: st.session_state.auth=False
if not st.session_state.auth: login(); st.stop()
with st.sidebar:
    st.markdown(logo(150),unsafe_allow_html=True); st.markdown("### FinancePlus 360 Enterprise"); st.caption(APP_VERSION)
    menu=st.radio("Menu",["Dashboard","Mail","Smart Import","NOTA","Anagrafica","Finance","Docs","Report","Calendar","AI","Google Drive","Manuale","Admin"],label_visibility="collapsed", key="main_menu")
    st.divider()
    if st.button("Logout"): st.session_state.auth=False; st.rerun()
{"Dashboard":dashboard,"Mail":page_mail,"Smart Import":smart_import,"NOTA":nota,"Anagrafica":anagrafica,"Finance":finance,"Docs":docs,"Report":report,"Calendar":calendar,"AI":ai,"Google Drive":drive,"Manuale":manual,"Admin":admin}[menu]()
