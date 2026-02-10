import streamlit as st
from openai import OpenAI
import PyPDF2 
import re
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO

# De API key veilig ophalen
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Functie om de tekst goed in de template te krijgen
def create_formatted_docx(text, is_cv=True):
    doc = Document()
    lines = text.split('\n')
    
    for line in lines:
        clean_line = line.strip()
        if not clean_line: 
            doc.add_paragraph()
            continue
            
        p = doc.add_paragraph()
        
        # Check of de regel een bullet moet zijn (begint met -)
        if is_cv and clean_line.startswith('-'):
            # Dit creëert een 'hangend inspringprofiel' (Hanging Indent)
            # Dit is exact hoe Word een 'echte bullet' opbouwt.
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            # We gebruiken het streepje uit de tekst als bullet-symbool
            run_text = clean_line
        else:
            run_text = clean_line.replace('#', '').strip()

        run = p.add_run(run_text)
        run.font.name = 'Poppins Light'
        run.font.size = Pt(9)
        
        # Alleen in het CV passen we de dikgedrukte headers en ervaring toe
        if is_cv:
            upper_line = clean_line.upper().strip()
            headers = ["KERNCOMPETENTIES", "WERKERVARING", "OPLEIDING", "CURSUSSEN & TRAININGEN", "VAARDIGHEDEN & COMPETENTIES", "RELEVANTE ERVARING"]
            
            # Logica voor dikgedrukte regels: Koppen, InTheArena-regel en Werkervaring met jaartallen
            if any(header in upper_line for header in headers) or \
               ("|" in clean_line and "InTheArena" in clean_line) or \
               (re.search(r'\(\d{4}\s*-\s*.*\)', clean_line)) or \
               (re.search(r'\(\d{4}\)', clean_line)):
                run.bold = True
        else:
            # Voor Motivatie en Analyse
            if ":" in clean_line and len(clean_line) < 40:
                run.bold = True

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- LOGIN LOGICA ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("InTheArena Portaal")
    password = st.text_input("Voer het wachtwoord in om toegang te krijgen:", type="password")
    if st.button("Log in"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Onjuist wachtwoord.")
    st.stop()

# --- INITIALISEER GEHEUGEN ---
if 'cv_result' not in st.session_state:
    st.session_state.cv_result = None
if 'mot_result' not in st.session_state:
    st.session_state.mot_result = None
if 'ana_result' not in st.session_state:
    st.session_state.ana_result = None

st.title("InTheArena CV Builder")

uploaded_file = st.file_uploader("Upload het originele CV (PDF)", type="pdf")
job_description = st.text_area("Plak hier de opdracht van de klant:", height=200)

# --- GENEREREN ---
if st.button("Genereer CV in InTheArena Stijl"):
    if uploaded_file and job_description:
        with st.spinner('Bezig met herschrijven...'):
            reader = PyPDF2.PdfReader(uploaded_file)
            cv_text = "".join([page.extract_text() for page in reader.pages])
            
            system_message = (
                "Jij bent mijn AI-assistent voor het professionaliseren van CV’s voor brokerportalen. "
                "Jouw taak is om een nieuw, volledig herschreven CV te genereren in exact dezelfde structuur, "
                "layout, tone-of-voice en schrijfstijl als het originele InTheArena-format.\n\n"
                "BELANGRIJK: De lengte van het herschreven CV MOET tussen de 700 en 900 woorden liggen. "
                "Breid de beschrijvingen van de werkervaring uit op basis van het origineel om dit te bereiken.\n\n"
                "INSTRUCTIES VOOR INHOUD:\n"
                "- Herschrijf slim, nooit verzinnen: Gebruik ALLEEN werk uit het originele CV.\n"
                "- Verwerk de taal en functietermen uit de broker aanvraag.\n"
                "- Kwaliteiten InTheArena: Voeg relevante Arena-kwaliteiten toe indien gevraagd.\n\n"
                "GEWENSTE STRUCTUUR:\n"
                "Gebruik PRECIES de volgende structuur: Naam | Consultant | InTheArena, intro, Kerncompetenties, "
                "Relevante ervaring, Werkervaring, Opleiding, Cursussen & trainingen, Vaardigheden en competenties.\n"
                "GEBRUIK VOOR ELKE BULLET een streepje (-) gevolgd door een spatie."
            )
            
            # De API calls
            cv_response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[{"role": "system", "content": system_message},
                          {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                temperature=0.3
            )
            st.session_state.cv_result = cv_response.choices[0].message.content

            # Motivatie en Analyse calls (kort gehouden voor overzicht)
            mot_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Schrijf een korte motivatie (200-300 woorden) in InTheArena-stijl."},
                          {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                temperature=0.4
            )
            st.session_state.mot_result = mot_res.choices[0].message.content

            ana_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Analyseer ontbrekende vaardigheden kritisch."},
                          {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                temperature=0.2
            )
            st.session_state.ana_result = ana_res.choices[0].message.content

# --- DOWNLOAD SECTIE ---
if st.session_state.cv_result:
    st.success("Alle documenten zijn gereed!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("Download CV", data=create_formatted_docx(st.session_state.cv_result, True), file_name="Herschreven_CV.docx")
    with col2:
        st.download_button("Download Motivatie", data=create_formatted_docx(st.session_state.mot_result, False), file_name="Motivatie.docx")
    with col3:
        st.download_button("Download Analyse", data=create_formatted_docx(st.session_state.ana_result, False), file_name="Analyse.docx")
