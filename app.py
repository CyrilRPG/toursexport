import streamlit as st
from bs4 import BeautifulSoup
from fpdf import FPDF
import html
import io

class QCMProcessor:
    def __init__(self, raw_content):
        # On décode les entités HTML (ex: &lt; devient <) au cas où le fichier est mal formaté
        decoded_content = html.unescape(raw_content)
        self.soup = BeautifulSoup(decoded_content, 'html.parser')
        
    def parse_data(self):
        qcm_list = []
        # Extraction des cartes de QCM
        cards = self.soup.find_all("div", class_="card card-content")
        
        for card in cards:
            title_div = card.find("div", class_="card-title")
            if not title_div: continue
            
            # Nettoyage du titre (on enlève les icônes de l'interface)
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

def clean_for_pdf(text):
    """Remplace les caractères problématiques pour la police Helvetica standard."""
    if not text: return ""
    replacements = {
        '\u2019': "'", '\u2018': "'", '\u201c': '"', '\u201d': '"',
        '\u00a0': " ", '\u2026': "...", '\u00e2': "a", '\u00e9': "e",
        '\u00e0': "a", '\u00e8': "e", '\u00f9': "u", '\u00ea': "e",
        '\u00ee': "i", '\u00f4': "o", '\u00eb': "e", '\u00ef': "i"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Conversion finale en Latin-1 (format PDF standard)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf(all_qcm):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PARTIE 1 : SUJET ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 20, "CAHIER D'EXERCICES (SUJETS)", ln=True, align='C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(245, 245, 245)
        pdf.multi_cell(0, 10, clean_for_pdf(qcm['title']), border=1, fill=True)
        pdf.ln(2)

        for item in qcm['items']:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"{item['label']} :", ln=True)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, clean_for_pdf(item['sujet']))
            pdf.ln(2)
        pdf.ln(5)

    # --- PARTIE 2 : CORRIGE ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 20, "CORRIGE DETAILLE", ln=True, align='C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(235, 245, 255)
        pdf.multi_cell(0, 10, clean_for_pdf(qcm['title']), border=1, fill=True)
        pdf.ln(2)

        for item in qcm['items']:
            pdf.set_font("Helvetica", "B", 10)
            pdf.write(6, f"{item['label']} - Sujet : ")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, clean_for_pdf(item['sujet']))
            
            # Couleur
            if "Faux" in item['correction']:
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(0, 120, 0)
            
            pdf.set_font("Helvetica", "B", 10)
            pdf.write(6, "Correction : ")
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, clean_for_pdf(item['correction']))
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)
        pdf.ln(5)

    return pdf.output()

# --- INTERFACE ---
st.set_page_config(page_title="tHarmo PDF", layout="centered")
st.title("📄 Convertisseur tHarmo")

files = st.file_uploader("Upload tes fichiers HTML", type="html", accept_multiple_files=True)

if files:
    all_data = []
    for f in files:
        raw_content = f.read().decode("utf-8", errors="ignore")
        processor = QCMProcessor(raw_content)
        all_data.extend(processor.parse_data())
    
    if st.button(f"Générer le PDF ({len(all_data)} QCMs trouvés)"):
        if not all_data:
            st.warning("Aucun QCM détecté. Vérifie le format de ton fichier.")
        else:
            pdf_bytes = generate_pdf(all_data)
            st.download_button(
                label="⬇️ Télécharger le PDF",
                data=bytes(pdf_bytes),
                file_name="QCM_Sujet_Corrige.pdf",
                mime="application/pdf"
            )
