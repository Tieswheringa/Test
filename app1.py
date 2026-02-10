import streamlit as st
from openai import OpenAI
import PyPDF2 
import re
from docx import Document
from docx.shared import Pt
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
            
        # Check of de regel een bullet moet zijn (begint met -)
        if is_cv and clean_line.startswith('-'):
            # Voeg een paragraaf toe met de officiële Word bullet-stijl
            p = doc.add_paragraph(style='List Bullet')
            # Verwijder het streepje uit de tekst voor de Word-bullet
            run_text = clean_line.lstrip('- ').strip()
        else:
            p = doc.add_paragraph()
            run_text = clean_line.replace('#', '').strip()

        run = p.add_run(run_text)
        run.font.name = 'Poppins Light'
        run.font.size = Pt(9)
        
        # Alleen in het CV passen we de dikgedrukte headers toe
        if is_cv:
            upper_line = clean_line.upper().strip()
            headers = ["KERNCOMPETENTIES", "WERKERVARING", "OPLEIDING", "CURSUSSEN & TRAININGEN", "VAARDIGHEDEN & COMPETENTIES", "RELEVANTE ERVARING"]
            
            # Logica voor dikgedrukte regels:
            # 1. Hoofdkoppen
            # 2. De Naam | Consultant regel
            # 3. Werkervaring regels (herkenning op basis van jaartallen tussen haakjes)
            if any(header in upper_line for header in headers) or \
               ("|" in clean_line and "InTheArena" in clean_line) or \
               (re.search(r'\(\d{4}\s*-\s*.*\)', clean_line)) or \
               (re.search(r'\(\d{4}\)', clean_line)):
                run.bold = True
        else:
            # Voor Motivatie en Analyse maken we koppen dikgedrukt als ze bovenaan staan
            if ":" in clean_line and len(clean_line) < 40:
                run.bold = True

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

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

# Initialiseer session_state om resultaten te bewaren na het klikken op download
if 'cv_result' not in st.session_state:
    st.session_state.cv_result = None
if 'mot_result' not in st.session_state:
    st.session_state.mot_result = None
if 'ana_result' not in st.session_state:
    st.session_state.ana_result = None

# Grote naam bovenaan de website
st.title("InTheArena CV Builder")

uploaded_file = st.file_uploader("Upload het originele CV (PDF)", type="pdf")
job_description = st.text_area("Plak hier de opdracht van de klant:", height=200)

# Knop
if st.button("Genereer CV in InTheArena Stijl"):
    if uploaded_file and job_description:
        with st.spinner('Bezig met herschrijven volgens template...'):
            reader = PyPDF2.PdfReader(uploaded_file)
            cv_text = "".join([page.extract_text() for page in reader.pages])
            
            # Bereken origineel woordaantal voor de instructie
            original_word_count = len(cv_text.split())
            
            # System prompt voor CV
            system_message = (
                "Jij bent mijn AI-assistent voor het professionaliseren van CV’s voor brokerportalen. "
                "Jouw taak is om een nieuw, volledig herschreven CV te genereren in exact dezelfde structuur, "
                "layout, tone-of-voice en schrijfstijl als het originele InTheArena-format.\n\n"
                f"BELANGRIJK: Het originele CV bevat ongeveer {original_word_count} woorden. "
                "Jouw herschreven versie MOET ongeveer evenveel woorden bevatten (marge van 100 woorden). "
                "Kort de werkervaring of introductie niet onnodig in; behoud de diepgang van het origineel.\n\n"
                "INSTRUCTIES VOOR INHOUD:\n"
                "- Herschrijf slim, nooit verzinnen: Gebruik ALLEEN werk dat daadwerkelijk in het originele CV staat.\n"
                "- Je mag herformuleren, bundelen of ordenen, of verantwoordelijkheden toevoegen mits herleidbaar.\n"
                "- Kwaliteiten InTheArena: Wij beschikken momenteel over: workshops faciliteren, analyse en structuur aanbrengen, "
                "communiceren en overtuigen, gedrag en teams begeleiden, implementatie realiseren, resultaten meten en borgen. "
                "Voeg deze toe als de uitvraag hierom vraagt.\n"
                "- Schrijf 100% op basis van de uitvraag: Verwerk de taal en functietermen uit de broker aanvraag.\n"
                "- Functietitels aanpassen mag alleen als dit logisch is (bijv. Projectmedewerker -> Projectleider).\n\n"
                "GEWENSTE STRUCTUUR:\n"
                "Gebruik PRECIES de volgende structuur en koppen:\n"
                "Naam | Consultant | InTheArena en daaronder twee alinea's over de kracht en aanpak\n"
                "Kerncompetenties (met bullets)\n"
                "Relevante ervaring t.o.v. functie [Naam Functie] (met bullets)\n"
                "Werkervaring (Functie | Bedrijf (Jaartal), met daaronder bullets)\n"
                "Opleiding\n"
                "Cursussen & trainingen\n"
                "Vaardigheden en competenties\n"
                "Houd het zakelijk maar energiek. Gebruik voor opsommingen altijd het streepje (-)."
            )
            
            # De API calls en opslaan in session_state
            cv_response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Opdracht: {job_description}\n\nCV Tekst: {cv_text}"}
                ],
                temperature=0.3
            )
            st.session_state.cv_result = cv_response.choices[0].message.content

            mot_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Schrijf een korte motivatie (200-300 woorden) in InTheArena-stijl. Concreet, helder, actiegericht, menselijk en zonder superlatieven."},
                    {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}
                ],
                temperature=0.4
            )
            st.session_state.mot_result = mot_response.choices[0].message.content

            ana_response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": (
                        "Je bent een kritische recruiter. Analyseer welke vaardigheden/competenties "
                        "ontbreken in het CV om een perfecte match te zijn voor de opdracht. "
                        "Verzin niets! Geef per ontbrekend punt een suggestie hoe de kandidaat "
                        "dit zou kunnen toevoegen of toelichten."
                    )},
                    {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}
                ],
                temperature=0.2
            )
            st.session_state.ana_result = ana_response.choices[0].message.content

# Toon resultaten en downloadknoppen als er data in de session_state zit
if st.session_state.cv_result:
    st.success("Alle documenten zijn gereed!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button("Download CV", 
                           data=create_formatted_docx(st.session_state.cv_result, True), 
                           file_name="Herschreven_CV.docx")
    
    with col2:
        st.download_button("Download Motivatie", 
                           data=create_formatted_docx(st.session_state.mot_result, False), 
                           file_name="Motivatie.docx")
    
    with col3:
        st.download_button("Download Analyse", 
                           data=create_formatted_docx(st.session_state.ana_result, False), 
                           file_name="Analyse_Tekortkomingen.docx")

    # Preview van de analyse onderaan
    st.info("### Analyse van ontbrekende zaken")
    st.markdown(st.session_state.ana_result)
elif not uploaded_file and not job_description:
    pass # Voorkom error melding bij eerste keer laden
