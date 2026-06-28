# FinancePlus 360 TOP v5.2 MAIL PARSER FIX

File principale Streamlit: `nota_webapp_google_drive.py`

Accesso iniziale:
- admin
- admin123

## Correzione v5.2
- Fix errore: `module 'email' has no attribute 'policy'`
- Parser email sostituito con:
  - `from email import policy`
  - `from email.parser import BytesParser`
- Scarico IMAP più stabile su Streamlit Cloud

## Parametri Aruba consigliati
- Server IMAP: imaps.aruba.it
- Porta: 993
- SSL: sì
- Cartella IMAP: INBOX

## Modulo Mail
- Scarica Mail
- R/Mail
- R/Collaboratori
- R/Aziende
