
import sqlite3, base64, re
from pathlib import Path
from datetime import datetime, date
import pandas as pd
import streamlit as st
import plotly.express as px
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm

DATA=Path("data"); UPLOADS=DATA/"uploads"; EXPORTS=Path("exports"); STATIC=Path("static"); MANUALI=Path("manuali")
for p in [DATA,UPLOADS,EXPORTS,STATIC,MANUALI]: p.mkdir(exist_ok=True,parents=True)
DB=DATA/"financeplus_360_v2.db"

st.set_page_config(page_title="FinancePlus 360 Enterprise", page_icon="static/favicon.png", layout="wide")

def inject():
    st.markdown("""
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="FinancePlus">
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
</style>""", unsafe_allow_html=True)
inject()

def con(): return sqlite3.connect(DB)
def init():
    c=con(); cur=c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS utenti(id INTEGER PRIMARY KEY, username TEXT UNIQUE,password TEXT,ruolo TEXT,nome TEXT,attivo INTEGER DEFAULT 1)")
    cur.execute("CREATE TABLE IF NOT EXISTS anagrafiche(id INTEGER PRIMARY KEY,tipo TEXT,nome TEXT,cognome TEXT,mail TEXT,cell TEXT,note TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS aziende(id INTEGER PRIMARY KEY,ragione_sociale TEXT,piva TEXT,cf TEXT,amministratore TEXT,sede TEXT,pec TEXT,collaboratore TEXT,settore TEXT,note TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS note(id INTEGER PRIMARY KEY,data TEXT,ora TEXT,mittente_tipo TEXT,mittente TEXT,destinatario_tipo TEXT,destinatario TEXT,azienda TEXT,banca TEXT,importo REAL,strumento TEXT,richiesta TEXT,stato TEXT,allegato TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS pratiche(id INTEGER PRIMARY KEY,azienda TEXT,strumento TEXT,banca TEXT,importo REAL,durata TEXT,stato TEXT,priorita TEXT,descrizione TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS documenti(id INTEGER PRIMARY KEY,azienda TEXT,categoria TEXT,filename TEXT,path TEXT,descrizione TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS eventi(id INTEGER PRIMARY KEY,tipo TEXT,data TEXT,ora TEXT,organizzatore_tipo TEXT,organizzatore TEXT,destinatario_tipo TEXT,destinatario TEXT,luogo TEXT,azienda TEXT,banca TEXT,importo REAL,strumento TEXT,richiesta TEXT,created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS logs(id INTEGER PRIMARY KEY,modulo TEXT,azione TEXT,dettaglio TEXT,created_at TEXT)")
    cur.execute("INSERT OR IGNORE INTO utenti(username,password,ruolo,nome) VALUES('admin','admin123','Admin','Amministratore')")
    c.commit(); c.close()
def q(sql,p=()):
    c=con(); d=pd.read_sql_query(sql,c,params=p); c.close(); return d
def x(sql,p=()):
    c=con(); cur=c.cursor(); cur.execute(sql,p); c.commit(); c.close()
def log(m,a,d=""): x("INSERT INTO logs(modulo,azione,dettaglio,created_at) VALUES(?,?,?,?)",(m,a,d,datetime.now().isoformat()))
init()

def b64(p):
    p=Path(p)
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""
def logo(w=170):
    p=STATIC/"financeplus_logo.jpeg"
    return f"<img src='data:image/jpeg;base64,{b64(p)}' width='{w}'>" if p.exists() else "<b>FinancePlus.Tech</b>"
def money(v):
    try: return float(str(v).replace(".","").replace(",","."))
    except: return 0.0
def people(t=None):
    if t: d=q("SELECT nome||' '||cognome n FROM anagrafiche WHERE tipo=? ORDER BY cognome,nome",(t,))
    else: d=q("SELECT nome||' '||cognome n FROM anagrafiche ORDER BY cognome,nome")
    return d.n.tolist() if len(d) else []
def azs():
    d=q("SELECT ragione_sociale FROM aziende ORDER BY ragione_sociale")
    return d.ragione_sociale.tolist() if len(d) else []
def safe(s): return re.sub(r"[^A-Za-z0-9_ -]","_",s or "Senza_Azienda").strip().replace(" ","_")
def save_file(f,sub):
    if not f: return ""
    folder=UPLOADS/sub; folder.mkdir(parents=True,exist_ok=True)
    p=folder/f.name; p.write_bytes(f.getvalue()); return str(p)
def pdf(title, sections, filename):
    out=EXPORTS/filename; styles=getSampleStyleSheet(); story=[]
    if (STATIC/"financeplus_logo.jpeg").exists(): story.append(Image(str(STATIC/"financeplus_logo.jpeg"),width=4*cm,height=4*cm))
    story += [Paragraph(title,styles["Title"]), Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"),styles["Normal"]), Spacer(1,12)]
    for h,d in sections:
        story.append(Paragraph(h,styles["Heading2"]))
        if isinstance(d,pd.DataFrame):
            if len(d):
                t=[d.columns.tolist()]+d.fillna("").astype(str).values.tolist()
                table=Table(t,repeatRows=1)
                table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0B2E5B")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),.25,colors.grey),("FONTSIZE",(0,0),(-1,-1),7)]))
                story.append(table)
            else: story.append(Paragraph("Nessun dato.",styles["Normal"]))
        else: story.append(Paragraph(str(d),styles["Normal"]))
        story.append(Spacer(1,12))
    SimpleDocTemplate(str(out)).build(story); return out
def hero(t,s): st.markdown(f"<div class='fp-hero'><h1>{t}</h1><p>{s}</p></div>",unsafe_allow_html=True); st.write("")

def login():
    c1,c2,c3=st.columns([1,1.2,1])
    with c2:
        st.markdown("<div class='fp-card' style='text-align:center'>",unsafe_allow_html=True)
        st.markdown(logo(220),unsafe_allow_html=True)
        st.markdown("## FinancePlus 360 Enterprise")
        u=st.text_input("Utente"); p=st.text_input("Password",type="password")
        if st.button("Entra",use_container_width=True):
            d=q("SELECT * FROM utenti WHERE username=? AND password=? AND attivo=1",(u,p))
            if len(d): st.session_state.auth=True; st.session_state.user=d.iloc[0].to_dict(); log("LOGIN","accesso",u); st.rerun()
            else: st.error("Credenziali non valide")
        st.info("Accesso iniziale: admin / admin123")
        st.markdown("</div>",unsafe_allow_html=True)

def dashboard():
    hero("Dashboard Direzionale","Controllo unico di attività, pratiche, documenti, note e calendario.")
    items=[("Note","note"),("Aziende","aziende"),("Pratiche","pratiche"),("Documenti","documenti"),("Eventi","eventi")]
    cols=st.columns(5)
    for col,(lab,tab) in zip(cols,items):
        n=len(q(f"SELECT * FROM {tab}"))
        col.markdown(f"<div class='fp-metric'><p>{lab}</p><h2>{n}</h2></div>",unsafe_allow_html=True)
    a,b=st.columns(2)
    with a:
        st.subheader("Note per stato")
        d=q("SELECT stato,COUNT(*) c FROM note GROUP BY stato")
        st.plotly_chart(px.pie(d,names="stato",values="c") if len(d) else px.pie(names=["Vuoto"],values=[1]),use_container_width=True)
    with b:
        st.subheader("Pratiche per stato")
        d=q("SELECT stato,COUNT(*) c FROM pratiche GROUP BY stato")
        st.plotly_chart(px.bar(d,x="stato",y="c") if len(d) else px.bar(x=["Vuoto"],y=[0]),use_container_width=True)

def page_nota():
    hero("NOTA","Gestione note operative, stati, allegati e PDF.")
    t1,t2,t3=st.tabs(["Nuova Nota","Elenco / Ricerca","PDF"])
    with t1:
        c1,c2=st.columns(2); data=c1.date_input("Data",date.today()); ora=c2.time_input("Ora",datetime.now().time().replace(second=0,microsecond=0))
        mt=st.selectbox("Mittente categoria",["Collaboratore","Gestore"]); mitt=st.selectbox("Mittente",people(mt) or [""])
        dt=st.selectbox("Destinatario categoria",["Collaboratore","Gestore"]); dest=st.selectbox("Destinatario",people(dt) or [""])
        az=st.selectbox("Azienda",[""]+azs()); banca=st.text_input("Banca"); imp=st.text_input("Importo")
        strum=st.selectbox("Strumento",["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"]); rich=st.text_area("Richiesta",height=160)
        stato=st.selectbox("Stato",["EVASA","INEVASA","IN ATTESA"]); f=st.file_uploader("Allegato")
        if st.button("Salva Nota",use_container_width=True):
            path=save_file(f,"note") if f else ""
            x("INSERT INTO note(data,ora,mittente_tipo,mittente,destinatario_tipo,destinatario,azienda,banca,importo,strumento,richiesta,stato,allegato,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(str(data),str(ora),mt,mitt,dt,dest,az,banca,money(imp),strum,rich,stato,path,datetime.now().isoformat()))
            log("NOTA","creata",az); st.success("Nota salvata.")
    with t2:
        d=q("SELECT * FROM note ORDER BY id DESC"); r=st.text_input("Ricerca")
        if r and len(d): d=d[d.astype(str).apply(lambda row: row.str.contains(r,case=False,na=False).any(),axis=1)]
        st.dataframe(d,use_container_width=True)
    with t3:
        if st.button("Genera PDF Note"):
            p=pdf("Report Note FinancePlus",[("Note",q("SELECT data,ora,mittente,destinatario,azienda,banca,importo,strumento,stato,richiesta FROM note"))],"report_note.pdf")
            st.download_button("Scarica PDF",p.read_bytes(),file_name=p.name)

def page_anagrafica():
    hero("Anagrafica","Collaboratori, gestori, aziende e schede cliente.")
    t1,t2,t3,t4=st.tabs(["Collaboratore","Gestore","Azienda","Elenchi"])
    for tab,tipo in [(t1,"Collaboratore"),(t2,"Gestore")]:
        with tab:
            nome=st.text_input("Nome",key=tipo+"n"); cog=st.text_input("Cognome",key=tipo+"c"); mail=st.text_input("Mail",key=tipo+"m"); cell=st.text_input("Cell",key=tipo+"cell"); note=st.text_area("Note",key=tipo+"note")
            if st.button("Salva "+tipo,key=tipo+"btn"):
                x("INSERT INTO anagrafiche(tipo,nome,cognome,mail,cell,note,created_at) VALUES(?,?,?,?,?,?,?)",(tipo,nome,cog,mail,cell,note,datetime.now().isoformat()))
                st.success(tipo+" salvato.")
    with t3:
        f=st.file_uploader("Inserisci Visura/Report PDF",type=["pdf"])
        rag=st.text_input("Ragione sociale"); piva=st.text_input("P.IVA"); cf=st.text_input("CF"); amm=st.text_input("Amministratore")
        sede=st.text_input("Sede"); pec=st.text_input("PEC"); settore=st.text_input("Settore"); coll=st.selectbox("Collaboratore",people("Collaboratore") or [""]); note=st.text_area("Note azienda")
        if f: save_file(f,"visure"); st.info("OCR automatico previsto in v2.1. Ora compila i campi manualmente.")
        if st.button("Salva Azienda"):
            x("INSERT INTO aziende(ragione_sociale,piva,cf,amministratore,sede,pec,collaboratore,settore,note,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(rag,piva,cf,amm,sede,pec,coll,settore,note,datetime.now().isoformat()))
            st.success("Azienda salvata.")
    with t4:
        st.dataframe(q("SELECT * FROM anagrafiche"),use_container_width=True); st.dataframe(q("SELECT * FROM aziende"),use_container_width=True)

def page_finance():
    hero("Finance","Gestione pratiche finanziarie e stato avanzamento.")
    t1,t2,t3=st.tabs(["Nuova Pratica","Elenco","PDF"])
    with t1:
        az=st.selectbox("Azienda",[""]+azs()); strum=st.selectbox("Strumento",["MUTUO","CHIROGRAFARIO","FACTORING","INVOICE TRADING","CROWD","PRESTITO"])
        banca=st.text_input("Banca"); imp=st.text_input("Importo"); durata=st.text_input("Durata")
        stato=st.selectbox("Stato",["NUOVA","ISTRUTTORIA","DOCUMENTI RICHIESTI","DELIBERATA","RESPINTA","EROGATA"]); priorita=st.selectbox("Priorità",["ALTA","MEDIA","BASSA"]); desc=st.text_area("Descrizione")
        if st.button("Salva Pratica"):
            x("INSERT INTO pratiche(azienda,strumento,banca,importo,durata,stato,priorita,descrizione,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(az,strum,banca,money(imp),durata,stato,priorita,desc,datetime.now().isoformat()))
            st.success("Pratica salvata.")
    with t2: st.dataframe(q("SELECT * FROM pratiche ORDER BY id DESC"),use_container_width=True)
    with t3:
        if st.button("PDF Pratiche"):
            p=pdf("Report Pratiche",[("Pratiche",q("SELECT azienda,strumento,banca,importo,durata,stato,priorita,descrizione FROM pratiche"))],"report_pratiche.pdf")
            st.download_button("Scarica PDF",p.read_bytes(),file_name=p.name)

def page_docs():
    hero("Docs","Archivio documentale cloud-ready.")
    az=st.selectbox("Azienda",[""]+azs()); cat=st.selectbox("Categoria",["VISURA","BILANCIO","CENTRALE RISCHI","ESTRATTO CONTO","CONTRATTO","REPORT","IDENTITA","ALTRO"])
    f=st.file_uploader("Carica documento"); desc=st.text_area("Descrizione")
    if st.button("Salva Documento"):
        if f:
            path=save_file(f,safe(az)); x("INSERT INTO documenti(azienda,categoria,filename,path,descrizione,created_at) VALUES(?,?,?,?,?,?)",(az,cat,f.name,path,desc,datetime.now().isoformat())); st.success("Documento salvato.")
        else: st.warning("Carica un documento.")
    st.dataframe(q("SELECT azienda,categoria,filename,descrizione,created_at FROM documenti"),use_container_width=True)

def page_calendar():
    hero("Calendar","Call, video call, appuntamenti e agenda.")
    t1,t2=st.tabs(["Nuovo Evento","Elenco"])
    with t1:
        tipo=st.selectbox("Tipo",["VIDEO CALL - PRATICA","VIDEO CALL - AGGIORNAMENTO","APPUNTAMENTO"])
        data=st.date_input("Data",date.today()); ora=st.time_input("Ora",datetime.now().time().replace(second=0,microsecond=0))
        ot=st.selectbox("Organizzatore categoria",["Collaboratore","Gestore"]); org=st.selectbox("Organizzatore",people(ot) or [""])
        dt=st.selectbox("Destinatario categoria",["Collaboratore","Gestore"]); dest=st.selectbox("Destinatario",people(dt) or [""])
        luogo=st.text_input("Luogo"); az=st.selectbox("Azienda",[""]+azs()); banca=st.text_input("Banca"); imp=st.text_input("Importo")
        strum=st.selectbox("Strumento",["CHIRO","FACTORING","INVOICE","MUTUO","PRESTITO","CROWD"]); rich=st.text_area("Richiesta")
        if st.button("Salva Evento"):
            x("INSERT INTO eventi(tipo,data,ora,organizzatore_tipo,organizzatore,destinatario_tipo,destinatario,luogo,azienda,banca,importo,strumento,richiesta,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(tipo,str(data),str(ora),ot,org,dt,dest,luogo,az,banca,money(imp),strum,rich,datetime.now().isoformat()))
            st.success("Evento salvato.")
    with t2: st.dataframe(q("SELECT * FROM eventi ORDER BY data DESC, ora DESC"),use_container_width=True)

def page_report():
    hero("Report","PDF professionali con logo FinancePlus.")
    az=st.selectbox("Azienda",["Tutte"]+azs())
    if st.button("Genera Report Completo"):
        wh="" if az=="Tutte" else " WHERE azienda=?"; pp=() if az=="Tutte" else (az,)
        p=pdf("Report Completo FinancePlus",[("Note",q("SELECT data,mittente,destinatario,azienda,banca,importo,strumento,stato FROM note"+wh,pp)),("Pratiche",q("SELECT azienda,strumento,banca,importo,durata,stato,priorita FROM pratiche"+wh,pp)),("Documenti",q("SELECT azienda,categoria,filename,descrizione FROM documenti"+wh,pp)),("Eventi",q("SELECT tipo,data,ora,organizzatore,destinatario,azienda,banca,importo,strumento FROM eventi"+wh,pp))],"report_completo_financeplus.pdf")
        st.download_button("Scarica PDF",p.read_bytes(),file_name=p.name)

def page_ai():
    hero("AI","Modulo assistente intelligente predisposto.")
    st.info("La v2.0 include il contenitore AI. La v2.1 collegherà OCR e analisi automatica di Visure, Bilanci e Centrale Rischi.")
    txt=st.text_area("Incolla testo pratica/documento")
    if st.button("Crea bozza nota"): st.success("Sintesi operativa: "+(txt[:900] if txt else "inserire testo."))

def page_drive():
    hero("Google Drive","Struttura cloud e backup.")
    st.code("https://drive.google.com/drive/folders/1PMMcslCfxkTrxEenal0fKuc39njN_yfv")
    st.code("FinancePlus_360\\n├── Clienti\\n├── Aziende\\n├── Pratiche\\n├── Visure\\n├── Bilanci\\n├── Centrale_Rischi\\n├── Report\\n├── Note\\n├── Backup\\n└── Manuali")
    st.warning("Sincronizzazione reale in v2.1 con credenziali Google.")

def page_manuale():
    hero("Manuale Integrato","Guide PDF e assistenza interna.")
    for p in MANUALI.glob("*.pdf"):
        st.download_button("Scarica "+p.name,p.read_bytes(),file_name=p.name)

def page_admin():
    hero("Admin","Utenti, backup e manutenzione.")
    t1,t2=st.tabs(["Utenti","Backup"])
    with t1:
        st.dataframe(q("SELECT id,username,ruolo,nome,attivo FROM utenti"),use_container_width=True)
        u=st.text_input("Username"); p=st.text_input("Password",type="password"); ruolo=st.selectbox("Ruolo",["Admin","Gestore","Collaboratore"]); nome=st.text_input("Nome")
        if st.button("Crea utente"): x("INSERT INTO utenti(username,password,ruolo,nome) VALUES(?,?,?,?)",(u,p,ruolo,nome)); st.success("Utente creato.")
    with t2:
        if DB.exists(): st.download_button("Scarica backup database",DB.read_bytes(),file_name="financeplus_360_v2_backup.db")

if "auth" not in st.session_state: st.session_state.auth=False
if not st.session_state.auth: login(); st.stop()
with st.sidebar:
    st.markdown(logo(150),unsafe_allow_html=True)
    st.markdown("### FinancePlus 360 Enterprise")
    st.caption("v2.0")
    menu=st.radio("Menu",["Dashboard","NOTA","Anagrafica","Finance","Docs","Report","Calendar","AI","Google Drive","Manuale","Admin"],label_visibility="collapsed")
    st.divider()
    if st.button("Logout"): st.session_state.auth=False; st.rerun()
{"Dashboard":dashboard,"NOTA":page_nota,"Anagrafica":page_anagrafica,"Finance":page_finance,"Docs":page_docs,"Report":page_report,"Calendar":page_calendar,"AI":page_ai,"Google Drive":page_drive,"Manuale":page_manuale,"Admin":page_admin}[menu]()
