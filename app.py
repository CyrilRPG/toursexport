import streamlit as st
from bs4 import BeautifulSoup
from fpdf import FPDF
import io

class QCMProcessor:
    def __init__(self, html_content):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        
    def parse_data(self):
        qcm_list = []
        # Chaque QCM est dans une div class="row" qui contient une card
        cards = self.soup.find_all("div", class_="card card-content")
        
        for card in cards:
            title_div = card.find("div", class_="card-title")
            if not title_div: continue
            
            # Nettoyage du titre (ex: QCM : A propos de...)
            qcm_title = title_div.get_text(strip=True).replace("info_outline", "").replace("grade", "").replace("trending_up", "").replace("report_problem", "")
            
            items = []
            # Les items sont séparés par des <span class="card-title">Item A</span>
            item_titles = card.find_all("span", class_="card-title")
            
            for it_title in item_titles:
                label = it_title.get_text(strip=True)
                # La structure suivante est une div class="row"
                row = it_title.find_next_sibling("div", class_="row")
                if row:
                    sujet_div = row.find("p", class_="justify")
                    # On cherche le bloc sujet et correction
                    paragraphs = row.find_all("p", class_="justify")
                    sujet_txt = ""
                    correction_txt = ""
                    
                    if len(paragraphs) >= 2:
                        # Extraction du texte du sujet
                        sujet_txt = paragraphs[0].get_text(strip=True).replace("Sujet :", "").strip()
                        # Extraction de la correction
                        correction_txt = paragraphs[1].get_text(strip=True).replace("Correction :", "").strip()
                    
                    items.append({
                        "label": label,
                        "sujet": sujet_txt,
                        "correction": correction_txt
                    })
            
            if qcm_title and items:
                qcm_list.append({"title": qcm_title, "items": items})
        
        return qcm_list

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 8)
        self.cell(0, 10, 'Convertisseur QCM - tHarmo', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', fill=True)
        self.ln(4)

def generate_pdf(all_qcm):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- PARTIE 1 : SUJET ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 20, "CAHIER D'EXERCICES (SUJETS)", 0, 1, 'C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.chapter_title(qcm['title'])
        for item in qcm['items']:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, f"{item['label']}:", 0, 1)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, item['sujet'])
            pdf.ln(2)
        pdf.ln(5)

    # --- PARTIE 2 : CORRIGE ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 20, "CORRIGÉ DÉTAILLÉ", 0, 1, 'C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.chapter_title(qcm['title'])
        for item in qcm['items']:
            pdf.set_font("Arial", 'B', 10)
            pdf.write(6, f"{item['label']} - Sujet: ")
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 6, item['sujet'])
            
            pdf.set_font("Arial", 'B', 10)
            pdf.set_text_color(200, 0, 0) if "Faux" in item['correction'] else pdf.set_text_color(0, 128, 0)
            pdf.write(6, "Correction : ")
            pdf.set_font("Arial", 'I', 10)
            pdf.multi_cell(0, 6, item['correction'])
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)
        pdf.ln(5)

    return pdf.output()

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="tHarmo HTML to PDF", layout="centered")

st.title("📄 Convertisseur tHarmo en Masse")
st.write("Glissez vos fichiers HTML pour obtenir un PDF Sujet + Corrigé.")

uploaded_files = st.file_uploader("Choisir les fichiers HTML", type="html", accept_multiple_files=True)

if uploaded_files:
    all_extracted_data = []
    
    for uploaded_file in uploaded_files:
        content = uploaded_file.read().decode("utf-8")
        processor = QCMProcessor(content)
        data = processor.parse_data()
        all_extracted_data.extend(data)
    
    if st.button(f"Générer le PDF ({len(all_extracted_data)} QCMs détectés)"):
        with st.spinner('Génération du PDF en cours...'):
            pdf_bytes = generate_pdf(all_extracted_data)
            st.success("Terminé !")
            st.download_button(
                label="⬇️ Télécharger le PDF",
                data=pdf_bytes,
                file_name="QCM_Sujet_Corrige.pdf",
                mime="application/pdf"
            )

st.divider()
st.info("Note : L'application traite les items (A, B, C, D, E) avec leurs justifications respectives.")
