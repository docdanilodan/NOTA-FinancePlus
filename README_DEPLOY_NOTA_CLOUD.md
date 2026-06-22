# NOTA FinancePlus Cloud v1

Versione web app pronta per PC, iPhone e iPad.

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run nota_webapp_google_drive.py
```

Credenziali demo: `admin / admin123`. Prima della pubblicazione usare `.streamlit/secrets.toml`.

## Pubblicazione consigliata

### Streamlit Cloud
1. Carica questa cartella su GitHub.
2. Crea una nuova app Streamlit.
3. Main file: `nota_webapp_google_drive.py`.
4. Incolla i secrets prendendo esempio da `.streamlit/secrets.toml.example`.
5. Collega il dominio `nota.financeplus.tech` dal DNS del provider.

### Render / Railway
Usa `Procfile` già incluso.

### Docker / VPS
```bash
docker build -t nota-financeplus .
docker run -p 8501:8501 nota-financeplus
```

## iPhone / iOS
1. Apri il link della app con Safari.
2. Tocca Condividi.
3. Tocca **Aggiungi a schermata Home**.
4. Nome consigliato: `NOTA`.

## Google Drive
Abilita Google Drive API e inserisci `credentials.json` nella cartella dell'app o sul server. La sezione Google Drive sincronizza database, upload e PDF nella cartella `NOTA_WEBAPP_DATI`.

## Contenuto
- Dashboard con logo FinancePlus.Tech
- Note con stati evasa/inevasa/in attesa
- Anagrafica collaboratori, gestori, aziende
- Upload visura/report PDF
- Video call e appuntamenti
- Report PDF con logo come sfondo/filigrana
- Calendario settimanale/mensile
- Login utenti e ruoli base
- Predisposizione icona iOS
