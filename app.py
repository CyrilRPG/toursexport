import urllib.request
import os

# Configuration de la police Unicode (DejaVuSans est standard et libre)
FONT_URL = "https://github.com/reingart/pyfpdf/raw/master/fpdf/font/DejaVuSans.ttf"
FONT_PATH = "DejaVuSans.ttf"

def download_font():
    if not os.path.exists(FONT_PATH):
        urllib.request.urlretrieve(FONT_URL, FONT_PATH)

class PDF(FPDF):
    def header(self):
        # Utiliser la police Unicode définie plus bas
        self.set_font('DejaVu', 'B', 8)
        self.cell(0, 10, 'Convertisseur QCM - tHarmo', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('DejaVu', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, title, 0, 1, 'L', fill=True)
        self.ln(4)

def generate_pdf(all_qcm):
    download_font() # S'assure que la police est disponible
    
    pdf = PDF()
    # AJOUT DE LA POLICE UNICODE
    pdf.add_font('DejaVu', '', FONT_PATH, uni=True)
    pdf.add_font('DejaVu', 'B', FONT_PATH, uni=True) # Note: idéalement il faudrait le fichier Bold séparé
    
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- PARTIE 1 : SUJET ---
    pdf.add_page()
    pdf.set_font("DejaVu", 'B', 16)
    pdf.cell(0, 20, "CAHIER D'EXERCICES (SUJETS)", 0, 1, 'C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.chapter_title(qcm['title'])
        for item in qcm['items']:
            pdf.set_font("DejaVu", 'B', 10)
            pdf.cell(0, 6, f"{item['label']}:", 0, 1)
            pdf.set_font("DejaVu", '', 10)
            pdf.multi_cell(0, 6, item['sujet'])
            pdf.ln(2)
        pdf.ln(5)

    # --- PARTIE 2 : CORRIGE ---
    pdf.add_page()
    pdf.set_font("DejaVu", 'B', 16)
    pdf.cell(0, 20, "CORRIGÉ DÉTAILLÉ", 0, 1, 'C')
    pdf.ln(10)

    for qcm in all_qcm:
        pdf.chapter_title(qcm['title'])
        for item in qcm['items']:
            pdf.set_font("DejaVu", 'B', 10)
            pdf.write(6, f"{item['label']} - Sujet: ")
            pdf.set_font("DejaVu", '', 10)
            pdf.multi_cell(0, 6, item['sujet'])
            
            # Gestion de la couleur (rouge/vert)
            if "Faux" in item['correction']:
                pdf.set_text_color(200, 0, 0)
            else:
                pdf.set_text_color(0, 128, 0)
                
            pdf.set_font("DejaVu", 'B', 10)
            pdf.write(6, "Correction : ")
            pdf.set_font("DejaVu", '', 10) # Pas d'italique natif simple ici sans fichier .ttf spécifique
            pdf.multi_cell(0, 6, item['correction'])
            pdf.set_text_color(0, 0, 0)
            pdf.ln(4)
        pdf.ln(5)

    return pdf.output()
