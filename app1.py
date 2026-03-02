import streamlit as st
from openai import OpenAI
import PyPDF2 
import re
from docx import Document
from docx.shared import Pt, Inches
from io import BytesIO

# --- 1. CONFIGURATIE ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def extract_text_from_pdf(file_path):
    try:
        reader = PyPDF2.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"Fout bij lezen van {file_path}: {e}"

# --- Functie om de database map in te lezen ---
def load_cv_database():
    db = {}
    folder_path = "cv_database" # Deze map staat op GitHub
    
    # Controleer of de map bestaat
    if not os.path.exists(folder_path):
        st.error(f"Map '{folder_path}' niet gevonden in de repository.")
        return db

    # Lees alle bestanden in de map
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            text = extract_text_from_pdf(file_path)
            # Gebruik bestandsnaam zonder .pdf als ID
            db[filename.replace(".pdf", "")] = text
    
    return db

# Functie om de tekst goed in de template te krijgen (Behouden zoals gevraagd)
def create_formatted_docx(text, is_cv=True):
    doc = Document()
    lines = text.split('\n')
    
    for line in lines:
        clean_line = line.replace('*', '').replace('#', '').strip()
        if not clean_line: 
            continue
            
        if is_cv and clean_line.startswith('-'):
            p = doc.add_paragraph(style='List Bullet')
            run_text = clean_line.lstrip('-').strip()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_together = True 
        else:
            p = doc.add_paragraph()
            run_text = clean_line
            p.paragraph_format.space_after = Pt(6)

        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.line_spacing = 1.0

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

# State voor versiebeheer
if 'cv_versions' not in st.session_state:
    st.session_state.cv_versions = []
# State voor motivatie en analyse per versie
if 'mot_versions' not in st.session_state:
    st.session_state.mot_versions = []
if 'ana_versions' not in st.session_state:
    st.session_state.ana_versions = []

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

# --- 4. PAGINA: CV BUILDER ---
elif st.session_state.page == "cv_builder":
    if st.sidebar.button("⬅ Terug naar Menu"):
        st.session_state.page = "home"
        st.rerun()

    st.title("InTheArena CV Builder")

    uploaded_file = st.file_uploader("Upload het originele CV (PDF)", type="pdf")
    job_description = st.text_area("Plak hier de opdracht van de klant:", height=200)

    if st.button("Genereer Documenten"):
        if uploaded_file and job_description:
            with st.spinner('Bezig met herschrijven...'):
                reader = PyPDF2.PdfReader(uploaded_file)
                cv_text = "".join([page.extract_text() for page in reader.pages])
                
                cv_system = (

    "Jij bent mijn AI-assistent for het professionaliseren van CV’s voor brokerportalen. "
    "Jouw taak is om een nieuw, volledig herschreven CV te genereren in exact dezelfde structuur, "
    "layout, tone-of-voice en schrijfstijl als het originele InTheArena-format.\n\n"
    
    "BELANGRIJK: De lengte van het herschreven CV MOET tussen de 700 en 900 woorden liggen. "
    "Breid de beschrijvingen van de werkervaring uit op basis van het origineel om dit te bereiken. "
    "Wees specifiek in resultaten en verantwoordelijkheden.\n\n"
    
    "CRUCIAAL: MAPPING VAN ERVARING AAN EISEN\n"
    "1. Analyseer de 'Harde Eisen' in de opdrachtomschrijving.\n"
    "2. Zoek in het originele CV naar ervaring die past bij deze eisen. Herschrijf deze ervaring zodanig dat de match overduidelijk is.\n"
    "3. Gebruik synoniemen en functietitels uit de opdrachtomschrijving in het CV (bijv. als de opdracht vraagt om een 'projectmanager', benadruk dan ervaring als 'projectleider' en gebruik de term projectmanager in de beschrijving).\n"
    "4. NEGEER DE OPROEP OM DE EISEN LETTERLIJK TE HERHALEN. Vertaal de eis naar een concrete prestatie uit het verleden van de kandidaat.\n\n"
    
    "INSTRUCTIES VOOR INHOUD:\n"
    "- Herschrijf slim, nooit verzinnen: Gebruik ALLEEN werk dat daadwerkelijk in het originele CV staat.\n"
    "- Kwaliteiten InTheArena: workshops faciliteren, analyse en structuur aanbrengen, "
    "communiceren en overtuigen, gedrag en teams begeleiden, implementatie realiseren, resultaten meten en borgen.\n"
    "- Schrijf 100% op basis van de uitvraag.\n\n"
    
    "GEWENSTE STRUCTUUR:\n"
    "Naam | Consultant | InTheArena en daaronder twee alinea's over de kracht en aanpak\n"
    "Kerncompetenties (met bullets)\n"
    "Relevante ervaring t.o.v. functie [Naam Functie] (met bullets, hier ervaring MAPPEN aan eisen)\n"
    "Werkervaring (Functie | Bedrijf (Jaartal), met daaronder bullets)\n"
    "Opleiding\n"
    "Cursussen & trainingen\n"
    "Vaardigheden en competenties\n"
    "GEBRUIK VOOR ELKE BULLET een streepje (-) gevolgd door een tab.\n"
    "GEBRUIK GEEN ASTERISKEN *"

                )
                
                cv_res = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[{"role": "system", "content": cv_system},
                              {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                    temperature=0.3
                )
                st.session_state.cv_versions.append(cv_res.choices[0].message.content)

                mot_res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Schrijf een korte motivatie (200-300 woorden) in InTheArena-stijl. Geen asterisken (*)."},
                              {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                    temperature=0.4
                )
                st.session_state.mot_versions.append(mot_res.choices[0].message.content)

                ana_res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": "Analyseer ontbrekende vaardigheden kritisch. Geen asterisken (*)."},
                              {"role": "user", "content": f"Opdracht: {job_description}\n\nCV: {cv_text}"}],
                    temperature=0.2
                )
                st.session_state.ana_versions.append(ana_res.choices[0].message.content)
                st.rerun()

    # Feedback & Versiebeheer sectie
    if st.session_state.cv_versions:
        st.divider()
        st.subheader("📚 Versiebeheer & Verfijnen")
        
        version_options = [f"Versie {i+1}" for i in range(len(st.session_state.cv_versions))]
        selected_version_index = st.selectbox("Selecteer een CV versie om te bekijken of te updaten:", 
                                            options=range(len(version_options)), 
                                            format_func=lambda x: version_options[x],
                                            index=len(version_options)-1)
        
        selected_cv = st.session_state.cv_versions[selected_version_index]
        selected_mot = st.session_state.mot_versions[selected_version_index] if selected_version_index < len(st.session_state.mot_versions) else None
        selected_ana = st.session_state.ana_versions[selected_version_index] if selected_version_index < len(st.session_state.ana_versions) else None

        feedback = st.text_area("Wat moet er veranderd worden aan de geselecteerde versie?", placeholder="Bijv: Meer focus op projectmanagement.")
        
        if st.button("Update CV"):
            if feedback:
                with st.spinner('CV, motivatiebrief en analyse worden bijgewerkt...'):
                    # Update CV
                    cv_update = client.chat.completions.create(
                        model="gpt-4o", 
                        messages=[
                            {"role": "system", "content": (
                                "Jij bent een redacteur. Je krijgt een volledig CV en feedback. "
                                "Jouw taak is om het VOLLEDIGE CV opnieuw uit te spugen (700-900 woorden), "
                                "waarbij je EXACT de structuur en de rest van de tekst behoudt, "
                                "en ENKEL de specifieke wijzigingen uit de feedback doorvoert. "
                                "Verwijder geen secties! Gebruik GEEN asterisken (*)."
                            )},
                            {"role": "user", "content": f"Huidig CV:\n{selected_cv}\n\nFeedback van de gebruiker: {feedback}"}
                        ],
                        temperature=0.3
                    )
                    new_cv = cv_update.choices[0].message.content
                    st.session_state.cv_versions.append(new_cv)

                    # Automatisch nieuwe motivatiebrief genereren op basis van het bijgewerkte CV
                    mot_update = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Schrijf een korte motivatie (200-300 woorden) in InTheArena-stijl op basis van het bijgewerkte CV. Geen asterisken (*)."},
                            {"role": "user", "content": f"Bijgewerkt CV:\n{new_cv}"}
                        ],
                        temperature=0.4
                    )
                    st.session_state.mot_versions.append(mot_update.choices[0].message.content)

                    # Automatisch nieuwe analyse genereren op basis van het bijgewerkte CV
                    ana_update = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "Analyseer ontbrekende vaardigheden kritisch op basis van het bijgewerkte CV. Geen asterisken (*)."},
                            {"role": "user", "content": f"Bijgewerkt CV:\n{new_cv}"}
                        ],
                        temperature=0.2
                    )
                    st.session_state.ana_versions.append(ana_update.choices[0].message.content)

                    st.success("Nieuwe versie aangemaakt — inclusief bijgewerkte motivatiebrief en analyse!")
                    st.rerun()

        # Download sectie gebaseerd op de geselecteerde versie
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(f"Download CV ({version_options[selected_version_index]})", 
                              data=create_formatted_docx(selected_cv, True), 
                              file_name=f"Herschreven_CV_V{selected_version_index+1}.docx")
        with col2:
            if selected_mot:
                st.download_button(f"Download Motivatie ({version_options[selected_version_index]})", 
                                   data=create_formatted_docx(selected_mot, False), 
                                   file_name=f"Motivatie_V{selected_version_index+1}.docx")
        with col3:
            if selected_ana:
                st.download_button(f"Download Analyse ({version_options[selected_version_index]})", 
                                   data=create_formatted_docx(selected_ana, False), 
                                   file_name=f"Analyse_V{selected_version_index+1}.docx")
        
        st.info("### Preview Analyse")
        if selected_ana:
            st.markdown(selected_ana.replace('*', ''))

# --- 5. PAGINA: GESCHIKTHEID TEST (Gecorrigeerd) ---
elif st.session_state.page == "geschiktheid_test":
    if st.sidebar.button("⬅ Terug naar Menu"):
        st.session_state.page = "home"
        st.rerun()

    st.title("🎯 Test geschiktheid opdracht")
    st.write("De AI analyseert de geüploade CV's om de perfecte match te vinden.")

    job_description_test = st.text_area("Plak hier de opdrachtomschrijving:", height=300)

    # Identificatie van de geüploade bestanden (gebruik de exacte namen uit de metadata)
    # Zorg dat deze namen exact overeenkomen met de files die je hebt geüpload!
    file_mapping = {
        "Max van den Top": "CV_MaxvandenTop_VNG.pdf",
        "Micha Sjoerts": "CV_Micha_Sjoerts_KOOPPDF.pdf",
        "Wendy van den Brink": "Cvwendy.pdf"
    }

    if st.button("Start Diepgaande Analyse"):
        if job_description_test:
            with st.spinner('De AI leest de volledige CV\'s en beoordeelt de match...'):
                
                # 1. Content ophalen via file_content_fetcher
                # Deze tool haalt de tekst op van de geüploade bestanden
                try:
                    # Hier wordt de tool aangeroepen om de inhoud van de files te lezen
                    cv_texts = client.files.content.fetch(
                        query="Haal de volledige tekst op van de CV's",
                        source_references=list(file_mapping.values())
                    )
                    
                    # 2. Inhoud structureren voor de prompt
                    cv_data_for_prompt = f"CV Data:\n{cv_texts}"
                except Exception as e:
                    cv_data_for_prompt = f"Fout bij het ophalen van CV data: {e}"

                # Systeemprompt voor diepgaande analyse
                match_system = (
                    "Jij bent een Senior Recruiter voor InTheArena. Je hebt zojuist de volledige tekst van de CV's van onze consultants ontvangen.\n"
                    "Jouw taak is om de opdracht te vergelijken met de volledige werkervaring in de documenten.\n\n"
                    "RICHTLIJNEN:\n"
                    "1. Match op 'Harde Eisen': Zoek naar bewijs dat de kandidaat exact heeft gedaan wat gevraagd wordt (bijv. specifieke systemen, Rijksoverheid, ervaringstermijnen).\n"
                    "2. Beredeneer: Verbind specifieke projecten of resultaten uit het CV aan de opdracht.\n"
                    "3. InTheArena-factor: Let op ervaring met workshops, implementatie en structuur.\n\n"
                    "OUTPUT STRUCTUUR:\n"
                    "### 🏆 Top Match: [Naam]\n"
                    "**Match Score:** [0-100%]\n"
                    "**Beredenering:** [Specifieke bewijsvoering uit het CV]\n\n"
                    "### 🔍 Analyse overige kandidaten\n"
                    "[Korte toelichting per andere consultant]\n\n"
                    "### 🚩 Risico's\n"
                    "[Welke eisen ontbreken nog?]"
                )

                # 3. API call met de opgehaalde content
                match_res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": match_system},
                        {"role": "user", "content": f"Opdracht:\n{job_description_test}\n\n{cv_data_for_prompt}"}
                    ],
                    temperature=0.2
                )

                st.divider()
                st.subheader("Resultaat van de Geschiktheidstest")
                st.markdown(match_res.choices[0].message.content)
        else:
            st.warning("Plak eerst een opdrachtomschrijving.")
