import streamlit as st
from bs4 import BeautifulSoup
from fpdf import FPDF
import html
import io

class QCMProcessor:
    def __init__(self, raw_content):
        # ÉTAPE CRUCIALE : On nettoie le format "Code Source" du navigateur
        # On extrait tout ce qui est dans les balises <td class="line-content">
        soup_raw = BeautifulSoup(raw_content, 'html.parser')
        lines = soup_raw.find_all("td", class_="line-content")
        
        if lines:
            # On reconstruit le vrai HTML à partir des lignes de code
            full_html = "".join([line.get_text() for line in lines])
            # On décode les entités (ex: &lt; devient <)
            self.clean_html = html.unescape(full_html)
        else:
            # Si c'est un fichier HTML standard
            self.clean_html = raw_content
            
        self.soup = BeautifulSoup(self.clean_html, 'html.parser')
        
    def parse_data(self):
        qcm_list = []
        cards = self.soup.find_all("div", class_="card card-content")
        
        for card in cards:
            title_div = card.find("div", class_="card-title")
            if not title_div: continue
            
            # Nettoyage du titre
            qcm_title = title_div.get_text(" ", strip=True).split("info_outline")[0].strip()
            
            items = []
            item_titles = card.find_all("span", class_="card-title")
            
            for it_title in item_titles:
                label = it_title.get_text(strip=True)
                row = it_title.find_next_sibling("div", class_="row")
                if row:
                    paragraphs = row.find_all("p", class_="justify")
                    if len(paragraphs) >= 2:
                        sujet_txt = paragraphs[0].get_text(" ", strip=True).replace("Sujet :", "").strip()
                        correction_txt = paragraphs[1].get_text(" ", strip=True).replace("Correction :", "").strip()
                        
                        items.append({
                            "label": label,
                            "sujet": sujet_txt,
                            "correction": correction_txt
                        })
            
            if items:
                qcm_list.append({"title": qcm_title, "items": items})
        return qcm_list

def clean_txt(text):
    """Évite les crashs de police PDF sur les caractères spéciaux."""
    if not text: return ""
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u00a0': " ", '\u2026': "...", '\u00e9': "e", '\u00e0': "a",
        '\u00e8': "e", '\u00ea': "e", '\u00f4': "o", '\u00ee': "i"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf(all_qcm):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- SUJETS ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 20, "SUJETS", ln=True, align='C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.multi_cell(0, 10, clean_txt(qcm['title']), border=1, fill=True)
        pdf.ln(2)

        for item in qcm['items']:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"{item['label']} :", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, clean_txt(item['sujet']))
            pdf.ln(2)
        pdf.ln(5)

    # --- CORRIGÉS ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 20, "CORRIGES", ln=True, align='C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(230, 240, 255)
        pdf.multi_cell(0, 10, clean_txt(qcm['title']), border=1, fill=True)
        pdf.ln(2)

        for item in qcm['items']:
            pdf.set_font("Helvetica", "B", 10)
            pdf.write(6, f"{item['label']} - ")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, clean_txt(item['sujet']))
            
            color = (200, 0, 0) if "Faux" in item['correction'] else (0, 120, 0)
            pdf.set_text_color(*color)
            pdf.set_font("Helvetica", "B", 10)
            pdf.write(6, "Correction : ")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, clean_txt(item['correction']))
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)
    return pdf.output()

# --- APP ---
st.title("Convertisseur tHarmo")
files = st.file_uploader("Upload tes fichiers", type="html", accept_multiple_files=True)

if files:
    all_data = []
    for f in files:
        raw = f.read().decode("utf-8", errors="ignore")
        processor = QCMProcessor(raw)
        all_data.extend(processor.parse_data())
    
    if st.button(f"Générer PDF ({len(all_data)} QCMs trouvés)"):
        if not all_data:
            st.error("Aucun QCM trouvé. Ton fichier est peut-être vide ou mal copié.")
        else:
            pdf = generate_pdf(all_data)
            st.download_button("Télécharger PDF", data=bytes(pdf), file_name="export.pdf")
