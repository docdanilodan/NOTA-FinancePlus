
from pathlib import Path
from datetime import datetime
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm

EXPORTS = Path("exports")
EXPORTS.mkdir(exist_ok=True)

def create_pdf(title, sections, filename):
    out = EXPORTS / filename
    styles = getSampleStyleSheet()
    story = []
    logo = Path("static/financeplus_logo.jpeg")
    if logo.exists():
        story.append(Image(str(logo), width=4*cm, height=4*cm))
    story.append(Paragraph(title, styles["Title"]))
    story.append(Paragraph(f"FinancePlus.Tech - Generato il {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    for heading, content in sections:
        story.append(Paragraph(heading, styles["Heading2"]))
        if isinstance(content, pd.DataFrame):
            if len(content):
                d = content.fillna("").astype(str)
                table_data = [d.columns.tolist()] + d.values.tolist()
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0B2E5B")),
                    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                    ("GRID", (0,0), (-1,-1), 0.25, colors.grey),
                    ("FONTSIZE", (0,0), (-1,-1), 7),
                    ("VALIGN", (0,0), (-1,-1), "TOP"),
                ]))
                story.append(table)
            else:
                story.append(Paragraph("Nessun dato disponibile.", styles["Normal"]))
        else:
            story.append(Paragraph(str(content).replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 12))
    SimpleDocTemplate(str(out)).build(story)
    return out
