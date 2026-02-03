import streamlit as st
from openai import OpenAI
import PyPDF2 
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from io import BytesIO

#de API key
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

#functie om de tekst goed in de template te krijgen
def create_formatted_docx(herschreven_tekst):
    doc = Document()
    lines = herschreven_tekst.split('\n')
    
    for line in lines:
        if not line.strip(): # Sla lege regels over 
            doc.add_paragraph()
            continue
            
        p = doc.add_paragraph()
        run = p.add_run(line.replace('#', '').strip())
        
        #gebruik juiste lettertype en font size
        run.font.name = 'Poppins Light'
        run.font.size = Pt(9)
        
        # We vergelijken alles in hoofdletters 
        upper_line = line.upper().strip()
        headers = [
            "KERNCOMPETENTIES", 
            "WERKERVARING", 
            "OPLEIDING", 
            "CURSUSSEN & TRAININGEN", 
            "VAARDIGHEDEN & COMPETENTIES",
            "RELEVANTE ERVARING"
        ]
        
        # Maak dikgedrukt als het een header of als | en InTheArena in de line staan
        if any(header in upper_line for header in headers) or ("|" in line and "InTheArena" in line):
            run.bold = True

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

#Grote naam bovenaan de website
st.title("InTheArena CV Builder")

uploaded_file = st.file_uploader("Upload het originele CV (PDF)", type="pdf")
job_description = st.text_area("Plak hier de opdracht van de klant:", height=200)

#knop
if st.button("Genereer CV in InTheArena Stijl"):
    if uploaded_file and job_description:
        with st.spinner('Bezig met herschrijven volgens template...'):
            reader = PyPDF2.PdfReader(uploaded_file)
            cv_text = "".join([page.extract_text() for page in reader.pages])
                #system prompts, wat je meegeeft aan chatgpt
            system_message = (
                "Je bent de InTheArena CV Builder. Herschrijf het CV in de ik-vorm. "
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
            #De API call
            response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Opdracht: {job_description}\n\nCV Tekst: {cv_text}"}
                ],
                temperature=0.3
            )

            resultaat = response.choices[0].message.content
            

            word_file = create_formatted_docx(resultaat)
            #knop om de word file te kunnen downloaden
            st.download_button(
                label="Download CV (Poppins 9)",
                data=word_file,
                file_name="Herschreven_CV_InTheArena.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
