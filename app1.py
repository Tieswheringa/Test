import streamlit as st
from openai import OpenAI
import PyPDF2 
import re
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO

# --- 1. CONFIGURATIE ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Functie om de tekst goed in de template te krijgen (Behouden zoals gevraagd)
def create_formatted_docx(text, is_cv=True):
    doc = Document()
    lines = text.split('\n')
    
    for line in lines:
        clean_line = line.replace('*', '').replace('#', '').strip()
        if not clean_line: 
            doc.add_paragraph()
            continue
            
        if is_cv and clean_line.startswith('-'):
            # We maken een officiële Word bullet-lijst aan
            p = doc.add_paragraph(style='List Bullet')
            # Verwijder het tekstuele streepje omdat Word zelf een bolletje toevoegt
            run_text = clean_line.lstrip('-').strip()
        else:
            p = doc.add_paragraph()
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

# --- 2. LOGIN & PAGINA BEHEER ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'page' not in st.session_state:
    st.session_state.page = "home"

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

# --- 3. HOMEPAGE ---
if st.session_state.page == "home":
    st.title("Welkom bij het InTheArena Portaal")
    st.write("Maak een keuze uit de onderstaande tools:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 CV & Motivatie Generator", use_container_width=True):
            st.session_state.page = "cv_builder"
            st.rerun()
            
    with col2:
        if st.button("🎯 Test geschiktheid opdracht", use_container_width=True):
            st.session_state.page = "geschiktheid_test"
            st.rerun()

# --- 4. PAGINA: CV BUILDER (HUIDIGE CODE) ---
elif st.session_state.page == "cv_builder":
    if st.sidebar.button("⬅ Terug naar Menu"):
        st.session_state.page = "home"
        st.rerun()

    if 'cv_result' not in st.session_state:
        st.session_state.cv_result = None
    if 'mot_result' not in st.session_state:
        st.session_state.mot_result = None
    if 'ana_result' not in st.session_state:
        st.session_state.ana_result = None

    st.title("InTheArena CV Builder")

    uploaded_file = st.file_uploader("Upload het originele CV (PDF)", type="pdf")
    job_description = st.text_area("Plak hier de opdracht van de klant:", height=200)

    if st.button("Genereer Documenten"):
        if uploaded_file and job_description:
            with st.spinner('Bezig met herschrijven...'):
                reader = PyPDF2.PdfReader(uploaded_file)
                cv_text = "".join([page.extract_text() for page in reader.pages])
                
                cv_system = (
                    "Jij bent mijn AI-assistent voor het professionaliseren van CV’s voor brokerportalen. "
                    "Jouw taak is om een nieuw, volledig herschreven CV te genereren in exact dezelfde structuur, "
                    "layout, tone-of-voice en schrijfstijl als het originele InTheArena-format.\n\n"
                    "BELANGRIJK: De lengte van het herschreven CV MOET tussen de 700 en 900 woorden liggen. "
                    "Breid de beschrijvingen van de werkervaring uit op basis van het origineel om dit te bereiken. "
                    "Wees specifiek in resultaten en verantwoordelijkheden.\n\n"
                    "INSTRUCTIES VOOR INHOUD:\n"
                    "- Herschrijf slim, nooit verzinnen: Gebruik ALLEEN werk dat daadwerkelijk in het originele CV staat.\n"
                    "- Kwaliteiten InTheArena: workshops faciliteren, analyse en structuur aanbrengen, "
                    "communiceren en overtuigen, gedrag en teams begeleiden, implementatie realiseren, resultaten meten en borgen.\n"
                    "- Schrijf 100% op basis van de uitvraag.\n\n"
                    "GEWENSTE STRUCTUUR:\n"
                    "Naam | Consultant | InTheArena en daaronder twee alinea's over de kracht en aanpak\n"
                    "Kerncompetenties (met bullets)\n"
                    "Relevante ervaring t.o.v. functie [Naam Functie] (met bullets)\n"
                    "Werkervaring (Functie | Bedrijf (Jaartal), met daaronder bullets)\n"
                    "Opleiding\n"
                    "Cursussen & trainingen\n"
                    "Vaardigheden en competenties\n"
                    "GEBRUIK VOOR ELKE BULLET een streepje (-) gevolgd door een tab.\n"
                    "GEBRUIK GEEN ASTERISKEN *"
                )
                
                # API Calls
                cv_res = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "system", "content": cv_system},
                              {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                    temperature=0.3
                )
                st.session_state.cv_result = cv_res.choices[0].message.content

                mot_res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Schrijf een korte motivatie (200-300 woorden) in InTheArena-stijl. Geen asterisken (*)."},
                              {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                    temperature=0.4
                )
                st.session_state.mot_result = mot_res.choices[0].message.content

                ana_res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Analyseer ontbrekende vaardigheden kritisch. Geen asterisken (*)."},
                              {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                    temperature=0.2
                )
                st.session_state.ana_result = ana_res.choices[0].message.content

    # Feedback sectie (behoudt logica)
    if st.session_state.cv_result:
        st.divider()
        st.subheader("💡 Verfijn het resultaat")
        feedback = st.text_area("Wat moet er veranderd worden?", placeholder="Bijv: Meer focus op projectmanagement.")
        if st.button("Update CV"):
            if feedback:
                with st.spinner('CV wordt volledig herschreven met jouw aanpassingen...'):
                    cv_update = client.chat.completions.create(
                        model="o1-mini", 
                        messages=[
                            {"role": "system", "content": (
                                "Jij bent een redacteur. Je krijgt een volledig CV en feedback. "
                                "Jouw taak is om het VOLLEDIGE CV opnieuw uit te spugen (700-900 woorden), "
                                "waarbij je EXACT de structuur en de rest van de tekst behoudt, "
                                "en ENKEL de specifieke wijzigingen uit de feedback doorvoert. "
                                "Verwijder geen secties! Gebruik GEEN asterisken (*)."
                            )},
                            {"role": "user", "content": f"Huidig CV:\n{st.session_state.cv_result}\n\nFeedback van de gebruiker: {feedback}"}
                        ],
                        temperature=0.3
                    )
                    st.session_state.cv_result = cv_update.choices[0].message.content
                    st.success("CV is volledig bijgewerkt!")

        # Download sectie
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("Download CV", data=create_formatted_docx(st.session_state.cv_result, True), file_name="Herschreven_CV.docx")
        with col2:
            if st.session_state.mot_result:
                st.download_button("Download Motivatie", data=create_formatted_docx(st.session_state.mot_result, False), file_name="Motivatie.docx")
        with col3:
            if st.session_state.ana_result:
                st.download_button("Download Analyse", data=create_formatted_docx(st.session_state.ana_result, False), file_name="Analyse.docx")
        
        st.info("### Preview Analyse")
        st.markdown(st.session_state.ana_result.replace('*', ''))

# --- 5. PAGINA: GESCHIKTHEID TEST (PLACEHOLDER) ---
elif st.session_state.page == "geschiktheid_test":
    if st.sidebar.button("⬅ Terug naar Menu"):
        st.session_state.page = "home"
        st.rerun()

    st.title("🎯 Test geschiktheid opdracht/opdrachtgever")
    st.info("Deze module is momenteel in ontwikkeling.")
    st.write("Hier komt straks de functionaliteit om te toetsen of een specifieke kandidaat of InTheArena als geheel past bij een nieuwe aanvraag.")






