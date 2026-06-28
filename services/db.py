
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

DB = Path("database/financeplus_360_enterprise.db")
DB.parent.mkdir(parents=True, exist_ok=True)

def connect():
    return sqlite3.connect(DB)

def init_db():
    con = connect()
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS utenti(
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, ruolo TEXT, nome TEXT, attivo INTEGER DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS anagrafiche(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, nome TEXT, cognome TEXT, mail TEXT, cell TEXT, note TEXT, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS aziende(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ragione_sociale TEXT, piva TEXT, cf TEXT, amministratore TEXT, sede TEXT, pec TEXT, collaboratore TEXT, settore TEXT, note TEXT, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS note(
        id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT, ora TEXT, mittente_tipo TEXT, mittente TEXT, destinatario_tipo TEXT, destinatario TEXT, azienda TEXT, banca TEXT, importo REAL, strumento TEXT, richiesta TEXT, stato TEXT, allegato TEXT, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS pratiche(
        id INTEGER PRIMARY KEY AUTOINCREMENT, azienda TEXT, strumento TEXT, banca TEXT, importo REAL, durata TEXT, stato TEXT, priorita TEXT, descrizione TEXT, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS documenti(
        id INTEGER PRIMARY KEY AUTOINCREMENT, azienda TEXT, categoria TEXT, filename TEXT, path TEXT, descrizione TEXT, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS eventi(
        id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT, data TEXT, ora TEXT, organizzatore_tipo TEXT, organizzatore TEXT, destinatario_tipo TEXT, destinatario TEXT, luogo TEXT, azienda TEXT, banca TEXT, importo REAL, strumento TEXT, richiesta TEXT, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT, modulo TEXT, azione TEXT, dettaglio TEXT, created_at TEXT)""")
    cur.execute("INSERT OR IGNORE INTO utenti(username,password,ruolo,nome) VALUES('admin','admin123','Admin','Amministratore')")
    con.commit()
    con.close()

def query(sql, params=()):
    con = connect()
    df = pd.read_sql_query(sql, con, params=params)
    con.close()
    return df

def execute(sql, params=()):
    con = connect()
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    con.close()

def log(modulo, azione, dettaglio=""):
    execute("INSERT INTO logs(modulo,azione,dettaglio,created_at) VALUES(?,?,?,?)",
            (modulo, azione, dettaglio, datetime.now().isoformat()))
