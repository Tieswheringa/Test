import streamlit as st
from openai import OpenAI
import PyPDF2 
import re
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO

# --- 1. CONFIGURATIE ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Functie om de tekst goed in de template te krijgen
def create_formatted_docx(text, is_cv=True):
    doc = Document()
    lines = text.split('\n')
    
    for line in lines:
        # Verwijder asterisken (*) en andere markdown-resten
        clean_line = line.replace('*', '').replace('#', '').strip()
        
        if not clean_line: 
            doc.add_paragraph()
            continue
            
        p = doc.add_paragraph()
        
        # Echte bullets met streepjes (Hanging Indent)
        if is_cv and clean_line.startswith('-'):
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            run_text = clean_line
        else:
            run_text = clean_line

        run = p.add_run(run_text)
        run.font.name = 'Poppins Light'
        run.font.size = Pt(9)
        
        if is_cv:
            upper_line = clean_line.upper().strip()
            headers = ["KERNCOMPETENTIES", "WERKERVARING", "OPLEIDING", "CURSUSSEN & TRAININGEN", "VAARDIGHEDEN & COMPETENTIES", "RELEVANTE ERVARING"]
            if any(header in upper_line for header in headers) or \
               ("|" in clean_line and "InTheArena" in clean_line) or \
               (re.search(r'\(\d{4}\s*-\s*.*\)', clean_line)) or \
               (re.search(r'\(\d{4}\)', clean_line)):
                run.bold = True
        elif ":" in clean_line and len(clean_line) < 50:
            run.bold = True

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 2. LOGIN LOGICA ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("InTheArena Portaal")
    password = st.text_input("Voer het wachtwoord in:", type="password")
    if st.button("Log in"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Onjuist wachtwoord.")
    st.stop()

# --- 3. INITIALISEER SESSION STATE ---
if 'cv_result' not in st.session_state:
    st.session_state.cv_result = None
if 'mot_result' not in st.session_state:
    st.session_state.mot_result = None
if 'ana_result' not in st.session_state:
    st.session_state.ana_result = None

st.title("InTheArena CV Builder 🚀")

uploaded_file = st.file_uploader("Upload het originele CV (PDF)", type="pdf")
job_description = st.text_area("Plak hier de opdracht van de klant:", height=200)

# --- 4. EERSTE GENERATIE ---
if st.button("Genereer Documenten"):
    if uploaded_file and job_description:
        with st.spinner('Bezig met herschrijven...'):
            reader = PyPDF2.PdfReader(uploaded_file)
            cv_text = "".join([page.extract_text() for page in reader.pages])
            
            # System prompt voor CV
            cv_system = (
                "Jij bent de InTheArena CV Builder. Schrijf een CV voor brokerportalen tussen 700-900 woorden. "
                "GEBRUIK GEEN asterisken (*) voor dikgedrukte tekst. Gebruik streepjes (-) voor bullets. "
                "Houd de exacte InTheArena structuur aan."
            )
            
            # CV Call
            cv_res = client.chat.completions.create(
                model="gpt-4o", 
                messages=[{"role": "system", "content": cv_system},
                          {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                temperature=0.3
            )
            st.session_state.cv_result = cv_res.choices[0].message.content

            # Motivatie Call
            mot_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Schrijf een korte motivatie (200-300 woorden) in InTheArena-stijl. Geen asterisken (*)."},
                          {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                temperature=0.4
            )
            st.session_state.mot_result = mot_res.choices[0].message.content

            # Analyse Call
            ana_res = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "Analyseer ontbrekende vaardigheden kritisch. Geen asterisken (*)."},
                          {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                temperature=0.2
            )
            st.session_state.ana_result = ana_res.choices[0].message.content

# --- 5. FEEDBACK SECTIE ---
if st.session_state.cv_result:
    st.divider()
    st.subheader("💡 Verfijn het resultaat")
    feedback = st.text_area("Wat moet er veranderd worden aan het CV?", placeholder="Bijv: Benadruk meer de ervaring met agile werken.")
    
    if st.button("Update CV"):
        if feedback:
            with st.spinner('CV wordt aangepast...'):
                cv_update = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[
                        {"role": "system", "content": "Pas het CV aan op basis van de feedback. Gebruik GEEN asterisken (*)."},
                        {"role": "user", "content": f"Huidig CV: {st.session_state.cv_result}\n\nFeedback: {feedback}"}
                    ],
                    temperature=0.3
                )
                st.session_state.cv_result = cv_update.choices[0].message.content
                st.success("CV is bijgewerkt!")

    # --- 6. DOWNLOAD SECTIE ---
    st.divider()
    st.success("Alle documenten zijn gereed!")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button("Download CV", 
                           data=create_formatted_docx(st.session_state.cv_result, True), 
                           file_name="Herschreven_CV.docx")
    
    with col2:
        if st.session_state.mot_result:
            st.download_button("Download Motivatie", 
                               data=create_formatted_docx(st.session_state.mot_result, False), 
                               file_name="Motivatie.docx")
    
    with col3:
        if st.session_state.ana_result:
            st.download_button("Download Analyse", 
                               data=create_formatted_docx(st.session_state.ana_result, False), 
                               file_name="Match_Analyse.docx")

    st.info("### Preview Analyse")
    st.markdown(st.session_state.ana_result.replace('*', ''))
