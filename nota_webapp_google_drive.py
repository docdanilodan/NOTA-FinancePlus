# -*- coding: utf-8 -*-
"""
NOTA - Web App gestionale con Google Drive
Autore: generato per Dott. Danilo D'Angelo

REQUISITI:
    pip install streamlit pandas reportlab PyPDF2 google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

AVVIO LOCALE:
    streamlit run nota_webapp_google_drive.py

USO CON GOOGLE DRIVE:
    1) Crea un progetto Google Cloud e abilita Google Drive API.
    2) Scarica credentials.json OAuth Desktop/Web e mettilo nella stessa cartella dell'app.
    3) Al primo avvio autorizza l'accesso a Google Drive.
    4) L'app crea/sincronizza in Drive una cartella "NOTA_WEBAPP_DATI" con database, upload e PDF.

NOTA:
    Per uso multiutente serio conviene pubblicare su Streamlit Community Cloud/Render e usare un database cloud.
    Questa versione e' pensata per utilizzo personale o piccolo team, con sincronizzazione file su Drive.
"""

import os
import io
import json
import sqlite3
import datetime as dt
from pathlib import Path

import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
except Exception:
    Credentials = None
    InstalledAppFlow = None
    Request = None
    build = None
    MediaFileUpload = None
    MediaIoBaseDownload = None

APP_TITLE = "NOTA - Gestionale Web"
DATA_DIR = Path("nota_webapp_dati")
UPLOAD_DIR = DATA_DIR / "uploads"
PDF_DIR = DATA_DIR / "pdf"
DB_PATH = DATA_DIR / "nota_webapp.sqlite"
DRIVE_FOLDER_NAME = "NOTA_WEBAPP_DATI"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

STRUMENTI = ["CHIRO", "FACTORING", "INVOICE", "MUTUO", "PRESTITO", "CROWD"]
STATI = ["EVASA", "INEVASA", "IN ATTESA"]
TIPI_VIDEO_CALL = ["PRATICA", "AGGIORNAMENTO"]

DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)


def db_connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    con = db_connect()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS collaboratori (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, cognome TEXT, mail TEXT, cell TEXT,
        creato_il TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS gestori (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT, cognome TEXT, mail TEXT, cell TEXT,
        creato_il TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS aziende (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ragione_sociale TEXT, piva TEXT, amministratore TEXT,
        collaboratore_id INTEGER,
        documento_pdf TEXT,
        creato_il TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS note (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, ora TEXT,
        mittente_tipo TEXT, mittente_id INTEGER,
        destinatario_tipo TEXT, destinatario_id INTEGER,
        azienda TEXT, banca TEXT, importo TEXT, strumento TEXT,
        richiesta TEXT, stato TEXT,
        creato_il TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS videocall (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT, data TEXT, ora TEXT,
        organizzatore_tipo TEXT, organizzatore_id INTEGER,
        destinatario_tipo TEXT, destinatario_id INTEGER,
        azienda_id INTEGER, banca TEXT, importo TEXT, strumento TEXT,
        richiesta TEXT, oggetto TEXT,
        creato_il TEXT
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appuntamenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT, ora TEXT,
        organizzatore_tipo TEXT, organizzatore_id INTEGER,
        destinatario_tipo TEXT, destinatario_id INTEGER,
        luogo TEXT, azienda_id INTEGER, banca TEXT, importo TEXT, strumento TEXT,
        richiesta TEXT,
        creato_il TEXT
    )""")
    con.commit()
    con.close()


def query_df(sql, params=()):
    con = db_connect()
    df = pd.read_sql_query(sql, con, params=params)
    con.close()
    return df


def execute(sql, params=()):
    con = db_connect()
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    con.close()


def now_date():
    return dt.datetime.now().strftime("%d/%m/%Y")


def now_time():
    return dt.datetime.now().strftime("%H:%M")


def today_iso():
    return dt.date.today().isoformat()


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def full_name(row):
    return f"{row['nome']} {row['cognome']}".strip()


def people_options(tipo):
    table = "collaboratori" if tipo == "Collaboratore" else "gestori"
    df = query_df(f"SELECT id, nome, cognome, mail, cell FROM {table} ORDER BY cognome, nome")
    mapping = {}
    for _, r in df.iterrows():
        label = f"{r['nome']} {r['cognome']} - {r['mail']}".strip()
        mapping[label] = int(r["id"])
    return mapping


def aziende_options():
    df = query_df("SELECT id, ragione_sociale, piva FROM aziende ORDER BY ragione_sociale")
    mapping = {}
    for _, r in df.iterrows():
        label = f"{r['ragione_sociale']} - P.IVA {r['piva']}".strip()
        mapping[label] = int(r["id"])
    return mapping


def save_uploaded_pdf(uploaded_file):
    if not uploaded_file:
        return ""
    safe = uploaded_file.name.replace("/", "_").replace("\\", "_")
    path = UPLOAD_DIR / f"{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe}"
    path.write_bytes(uploaded_file.getvalue())
    return str(path)


def extract_company_data_from_pdf(path):
    result = {"ragione_sociale": "", "piva": "", "amministratore": ""}
    if not path or not PdfReader:
        return result
    try:
        reader = PdfReader(path)
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:5])
        lines = [x.strip() for x in text.splitlines() if x.strip()]
        upper = text.upper()
        # Estrazione semplice, migliorabile su layout specifici di visure/report.
        for line in lines[:40]:
            if len(line) > 4 and not result["ragione_sociale"]:
                if any(k in line.upper() for k in ["S.R.L", "SRL", "S.P.A", "SPA", "SAS", "SNC", "DITTA"]):
                    result["ragione_sociale"] = line[:120]
                    break
        import re
        m = re.search(r"(?:P\.?\s*IVA|PARTITA\s+IVA)\D*(\d{11})", upper)
        if m:
            result["piva"] = m.group(1)
        for i, line in enumerate(lines):
            if any(k in line.upper() for k in ["AMMINISTRATORE", "LEGALE RAPPRESENTANTE"]):
                result["amministratore"] = (line + " " + (lines[i+1] if i+1 < len(lines) else ""))[:120]
                break
    except Exception:
        pass
    return result


def make_pdf(title, df, filename):
    path = PDF_DIR / filename
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), rightMargin=18, leftMargin=18, topMargin=18, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 10)]
    if df.empty:
        story.append(Paragraph("Nessun dato disponibile.", styles["Normal"]))
    else:
        data = [list(df.columns)] + df.astype(str).values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ffd966")),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(table)
    doc.build(story)
    return path


def drive_service():
    if not Credentials:
        st.warning("Librerie Google non installate. Installa i requisiti per attivare Google Drive.")
        return None
    token_path = DATA_DIR / "token.json"
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            cred_path = Path("credentials.json")
            if not cred_path.exists():
                st.error("Manca credentials.json nella cartella dell'app.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("drive", "v3", credentials=creds)


def get_or_create_drive_folder(service):
    q = f"mimeType='application/vnd.google-apps.folder' and name='{DRIVE_FOLDER_NAME}' and trashed=false"
    res = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    meta = {"name": DRIVE_FOLDER_NAME, "mimeType": "application/vnd.google-apps.folder"}
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def upload_to_drive(service, local_path, folder_id):
    local_path = Path(local_path)
    q = f"name='{local_path.name}' and '{folder_id}' in parents and trashed=false"
    found = service.files().list(q=q, spaces="drive", fields="files(id, name)").execute().get("files", [])
    media = MediaFileUpload(str(local_path), resumable=True)
    meta = {"name": local_path.name, "parents": [folder_id]}
    if found:
        service.files().update(fileId=found[0]["id"], media_body=media).execute()
    else:
        service.files().create(body=meta, media_body=media, fields="id").execute()


def sync_all_to_drive():
    service = drive_service()
    if not service:
        return
    folder_id = get_or_create_drive_folder(service)
    for path in [DB_PATH] + list(UPLOAD_DIR.glob("*")) + list(PDF_DIR.glob("*.pdf")):
        if path.exists() and path.is_file():
            upload_to_drive(service, path, folder_id)
    st.success("Sincronizzazione completata su Google Drive.")


def sidebar():
    st.sidebar.title("Dashboard")
    menu = st.sidebar.radio("Menu", ["Dashboard", "NOTA", "ANAGRAFICA", "CALL/VCALL", "REPORT", "CALENDARIO", "GOOGLE DRIVE"])
    st.sidebar.caption("NOTA Web App - PC, tablet e cellulare")
    return menu


def show_dashboard():
    st.title(APP_TITLE)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Note", len(query_df("SELECT id FROM note")))
    c2.metric("Aziende", len(query_df("SELECT id FROM aziende")))
    c3.metric("Video Call", len(query_df("SELECT id FROM videocall")))
    c4.metric("Appuntamenti", len(query_df("SELECT id FROM appuntamenti")))
    st.info("Usa il menu laterale per inserire note, anagrafiche, call, appuntamenti, report e calendario.")


def page_nota():
    st.header("1. NOTA")
    tab1, tab2 = st.tabs(["Nuova nota", "Elenco note e PDF"])
    with tab1:
        st.subheader("Nuova nota")
        with st.form("nota_form"):
            col1, col2 = st.columns(2)
            data = col1.text_input("Data", now_date())
            ora = col2.text_input("Ora", now_time())
            mtipo = st.selectbox("Mittente tipo", ["Collaboratore", "Gestore"])
            mopts = people_options(mtipo)
            mittente = st.selectbox("Mittente", list(mopts.keys()) or ["Nessun nominativo presente"])
            dtipo = st.selectbox("Destinatario tipo", ["Collaboratore", "Gestore"])
            dopts = people_options(dtipo)
            destinatario = st.selectbox("Destinatario", list(dopts.keys()) or ["Nessun nominativo presente"])
            col3, col4 = st.columns(2)
            azienda = col3.text_input("Azienda")
            banca = col4.text_input("Banca")
            col5, col6 = st.columns(2)
            importo = col5.text_input("Importo")
            strumento = col6.selectbox("Strumento", STRUMENTI)
            richiesta = st.text_area("Richiesta", height=160)
            stato = st.selectbox("Stato", STATI)
            ok = st.form_submit_button("Salva nota")
            if ok:
                execute("""INSERT INTO note VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (data, ora, mtipo, mopts.get(mittente, 0), dtipo, dopts.get(destinatario, 0), azienda, banca, importo, strumento, richiesta, stato, now_iso()))
                st.success("Nota salvata.")
    with tab2:
        df = query_df("SELECT id, data, ora, mittente_tipo, destinatario_tipo, azienda, banca, importo, strumento, richiesta, stato FROM note ORDER BY id DESC")
        st.dataframe(df, use_container_width=True)
        if st.button("Genera PDF note"):
            path = make_pdf("Elenco Note", df, "elenco_note.pdf")
            st.success(f"PDF creato: {path}")
            with open(path, "rb") as f:
                st.download_button("Scarica PDF note", f, file_name="elenco_note.pdf")


def page_anagrafica():
    st.header("2. ANAGRAFICA")
    tab1, tab2, tab3, tab4 = st.tabs(["Inserisci Collaboratore", "Inserisci Gestore", "Inserisci Azienda", "Elenchi e PDF"])
    with tab1:
        with st.form("collab_form"):
            nome = st.text_input("Nome")
            cognome = st.text_input("Cognome")
            mail = st.text_input("Mail")
            cell = st.text_input("Cell")
            if st.form_submit_button("Salva collaboratore"):
                execute("INSERT INTO collaboratori VALUES (NULL,?,?,?,?,?)", (nome, cognome, mail, cell, now_iso()))
                st.success("Collaboratore salvato.")
    with tab2:
        with st.form("gest_form"):
            nome = st.text_input("Nome", key="gnome")
            cognome = st.text_input("Cognome", key="gcognome")
            mail = st.text_input("Mail", key="gmail")
            cell = st.text_input("Cell", key="gcell")
            if st.form_submit_button("Salva gestore"):
                execute("INSERT INTO gestori VALUES (NULL,?,?,?,?,?)", (nome, cognome, mail, cell, now_iso()))
                st.success("Gestore salvato.")
    with tab3:
        st.caption("Carica visura/report PDF: l'app prova a compilare in automatico Ragione sociale, P.IVA e Amministratore.")
        uploaded = st.file_uploader("Inserisci Visura/Report PDF", type=["pdf"])
        extracted = {"ragione_sociale": "", "piva": "", "amministratore": ""}
        saved_path = ""
        if uploaded:
            saved_path = save_uploaded_pdf(uploaded)
            extracted = extract_company_data_from_pdf(saved_path)
            st.success("PDF caricato. Verifica i dati estratti prima di salvare.")
        with st.form("azienda_form"):
            rag = st.text_input("Ragione sociale", value=extracted.get("ragione_sociale", ""))
            piva = st.text_input("P.IVA", value=extracted.get("piva", ""))
            amm = st.text_input("Nome Cognome Amministratore", value=extracted.get("amministratore", ""))
            copts = people_options("Collaboratore")
            collab = st.selectbox("Collaboratore", list(copts.keys()) or ["Nessun collaboratore presente"])
            doc_path = st.text_input("Documento PDF caricato", value=saved_path)
            if st.form_submit_button("Salva azienda"):
                execute("INSERT INTO aziende VALUES (NULL,?,?,?,?,?,?)", (rag, piva, amm, copts.get(collab, 0), doc_path, now_iso()))
                st.success("Azienda salvata.")
    with tab4:
        st.subheader("Collaboratori")
        coll = query_df("SELECT id, nome, cognome, mail, cell FROM collaboratori ORDER BY cognome")
        st.dataframe(coll, use_container_width=True)
        st.subheader("Gestori")
        gest = query_df("SELECT id, nome, cognome, mail, cell FROM gestori ORDER BY cognome")
        st.dataframe(gest, use_container_width=True)
        st.subheader("Aziende")
        az = query_df("SELECT id, ragione_sociale, piva, amministratore, collaboratore_id FROM aziende ORDER BY ragione_sociale")
        st.dataframe(az, use_container_width=True)
        if st.button("Genera PDF anagrafica"):
            combo = pd.concat([
                coll.assign(tipo="Collaboratore"),
                gest.assign(tipo="Gestore"),
                az.rename(columns={"ragione_sociale": "nome", "piva": "cognome"}).assign(tipo="Azienda")
            ], ignore_index=True, sort=False)
            path = make_pdf("Elenco Gestori Collaboratori Aziende", combo.fillna(""), "elenco_anagrafica.pdf")
            with open(path, "rb") as f:
                st.download_button("Scarica PDF anagrafica", f, file_name="elenco_anagrafica.pdf")


def page_call():
    st.header("3. CALL/VCALL")
    tab1, tab2, tab3 = st.tabs(["Nuova Video Call", "Nuovo Appuntamento", "Elenchi e PDF"])
    with tab1:
        tipo = st.selectbox("Tipo Video Call", TIPI_VIDEO_CALL)
        with st.form("vcall_form"):
            data = st.text_input("Data", now_date(), key="vcdata")
            ora = st.text_input("Ora", now_time(), key="vcora")
            otipo = st.selectbox("Organizzatore tipo", ["Collaboratore", "Gestore"], key="vot")
            oopts = people_options(otipo)
            org = st.selectbox("Organizzatore", list(oopts.keys()) or ["Nessun nominativo presente"], key="vo")
            if tipo == "PRATICA":
                dtipo = st.selectbox("Destinatario tipo", ["Collaboratore", "Gestore"], key="vdt")
                dopts = people_options(dtipo)
                dest = st.selectbox("Destinatario", list(dopts.keys()) or ["Nessun nominativo presente"], key="vd")
                aopts = aziende_options()
                azienda = st.selectbox("Azienda", list(aopts.keys()) or ["Nessuna azienda presente"])
                banca = st.text_input("Banca")
                importo = st.text_input("Importo")
                strumento = st.selectbox("Strumento", STRUMENTI)
                richiesta = st.text_area("Richiesta", height=160)
                oggetto = ""
            else:
                dtipo, dest, dopts, azienda, aopts, banca, importo, strumento, richiesta = "", "", {}, "", {}, "", "", "", ""
                oggetto = st.text_area("Oggetto", height=160)
            if st.form_submit_button("Salva Video Call"):
                execute("INSERT INTO videocall VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (tipo, data, ora, otipo, oopts.get(org, 0), dtipo, dopts.get(dest, 0), aopts.get(azienda, 0), banca, importo, strumento, richiesta, oggetto, now_iso()))
                st.success("Video Call salvata.")
    with tab2:
        with st.form("app_form"):
            data = st.text_input("Data", now_date(), key="apdata")
            ora = st.text_input("Ora", now_time(), key="apora")
            otipo = st.selectbox("Organizzatore tipo", ["Collaboratore", "Gestore"], key="apot")
            oopts = people_options(otipo)
            org = st.selectbox("Organizzatore", list(oopts.keys()) or ["Nessun nominativo presente"], key="apo")
            dtipo = st.selectbox("Destinatario tipo", ["Collaboratore", "Gestore"], key="apdt")
            dopts = people_options(dtipo)
            dest = st.selectbox("Destinatario", list(dopts.keys()) or ["Nessun nominativo presente"], key="apd")
            luogo = st.text_input("Luogo")
            aopts = aziende_options()
            azienda = st.selectbox("Azienda", list(aopts.keys()) or ["Nessuna azienda presente"], key="apaz")
            banca = st.text_input("Banca", key="apbanca")
            importo = st.text_input("Importo", key="apimporto")
            strumento = st.selectbox("Strumento", STRUMENTI, key="apstrumento")
            richiesta = st.text_area("Richiesta", height=160, key="aprichiesta")
            if st.form_submit_button("Salva appuntamento"):
                execute("INSERT INTO appuntamenti VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (data, ora, otipo, oopts.get(org, 0), dtipo, dopts.get(dest, 0), luogo, aopts.get(azienda, 0), banca, importo, strumento, richiesta, now_iso()))
                st.success("Appuntamento salvato.")
    with tab3:
        vc = query_df("SELECT id, tipo, data, ora, organizzatore_tipo, destinatario_tipo, azienda_id, banca, importo, strumento, richiesta, oggetto FROM videocall ORDER BY id DESC")
        ap = query_df("SELECT id, data, ora, organizzatore_tipo, destinatario_tipo, luogo, azienda_id, banca, importo, strumento, richiesta FROM appuntamenti ORDER BY id DESC")
        st.subheader("Video Call")
        st.dataframe(vc, use_container_width=True)
        st.subheader("Appuntamenti")
        st.dataframe(ap, use_container_width=True)
        if st.button("Genera PDF Call e Appuntamenti"):
            combo = pd.concat([vc.assign(tipo_record="Video Call"), ap.assign(tipo_record="Appuntamento")], ignore_index=True, sort=False).fillna("")
            path = make_pdf("Elenco Video Call e Appuntamenti", combo, "elenco_call_appuntamenti.pdf")
            with open(path, "rb") as f:
                st.download_button("Scarica PDF Call/Appuntamenti", f, file_name="elenco_call_appuntamenti.pdf")


def page_report():
    st.header("4. REPORT")
    aopts = aziende_options()
    scelta = st.selectbox("Azienda", ["Tutte le aziende"] + list(aopts.keys()))
    note = query_df("SELECT * FROM note ORDER BY stato, azienda")
    if scelta != "Tutte le aziende":
        rag = scelta.split(" - P.IVA ")[0]
        note = note[note["azienda"].fillna("").str.contains(rag, case=False, na=False)]
    st.subheader("Note distinte per stato")
    st.dataframe(note, use_container_width=True)
    if not note.empty:
        st.bar_chart(note["stato"].value_counts())
    if st.button("Genera PDF Report"):
        path = make_pdf("Report per azienda/collaboratore con note evase, inevase e in attesa", note.fillna(""), "report_note.pdf")
        with open(path, "rb") as f:
            st.download_button("Scarica PDF Report", f, file_name="report_note.pdf")


def page_calendario():
    st.header("5. CALENDARIO")
    vista = st.radio("Vista", ["Settimanale", "Mensile"], horizontal=True)
    base = st.date_input("Data di riferimento", dt.date.today())
    note = query_df("SELECT data, ora, 'Nota' AS tipo, azienda AS titolo, richiesta AS descrizione FROM note")
    vc = query_df("SELECT data, ora, 'Video Call' AS tipo, tipo AS titolo, COALESCE(richiesta, oggetto) AS descrizione FROM videocall")
    ap = query_df("SELECT data, ora, 'Appuntamento' AS tipo, luogo AS titolo, richiesta AS descrizione FROM appuntamenti")
    events = pd.concat([note, vc, ap], ignore_index=True, sort=False).fillna("")
    def parse_it(s):
        try:
            return dt.datetime.strptime(s, "%d/%m/%Y").date()
        except Exception:
            return None
    events["giorno"] = events["data"].apply(parse_it)
    if vista == "Settimanale":
        start = base - dt.timedelta(days=base.weekday())
        end = start + dt.timedelta(days=6)
    else:
        start = base.replace(day=1)
        next_month = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)
        end = next_month - dt.timedelta(days=1)
    filt = events[(events["giorno"] >= start) & (events["giorno"] <= end)].sort_values(["giorno", "ora"])
    st.write(f"Periodo: {start.strftime('%d/%m/%Y')} - {end.strftime('%d/%m/%Y')}")
    st.dataframe(filt[["data", "ora", "tipo", "titolo", "descrizione"]], use_container_width=True)


def page_drive():
    st.header("Google Drive")
    st.write("Questa sezione sincronizza database, PDF generati e documenti caricati nella cartella Google Drive:", DRIVE_FOLDER_NAME)
    st.warning("Prima di usare Drive devi avere il file credentials.json nella cartella dell'app.")
    if st.button("Sincronizza ora su Google Drive"):
        sync_all_to_drive()
    st.info("Per usarla da cellulare e PC: pubblica l'app su Streamlit Community Cloud/Render oppure eseguila su un PC sempre acceso e accedi dal browser.")


def main():
    inject_pwa_links()
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()
    menu = sidebar()
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "NOTA":
        page_nota()
    elif menu == "ANAGRAFICA":
        page_anagrafica()
    elif menu == "CALL/VCALL":
        page_call()
    elif menu == "REPORT":
        page_report()
    elif menu == "CALENDARIO":
        page_calendario()
    elif menu == "GOOGLE DRIVE":
        page_drive()


if __name__ == "__main__":
    main()
