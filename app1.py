import streamlit as st
from openai import OpenAI
import PyPDF2 
#Placeholder omdat ik nog geen API key heb
client = OpenAI(api_key="JOUW_API_KEY_HIER")

st.title("InTheArena CV Builder")
st.subheader("Herschrijf CV's op basis van klantopdrachten")

uploaded_file = st.file_uploader("Upload het originele CV (PDF)", type="pdf")
job_description = st.text_area("Plak hier de opdracht van de klant:", height=200)

if st.button("Genereer Herschreven CV"):
    if uploaded_file and job_description:
        with st.spinner('Bezig met herschrijven...'):
            #Dit haalt de tekst uit het PDF
            reader = PyPDF2.PdfReader(uploaded_file)
            cv_text = ""
            for page in reader.pages:
                cv_text += page.extract_text()

            # SYSTEM PROMPT, BELANGRIJK hierzo kunnen we het model vergelijkbaar maken aan de bestaande tool
            system_message = (
                "Je bent de InTheArena CV Builder. Je bent een expert in werving en selectie. "
                "Je krijgt een CV en een opdrachtomschrijving. "
                "Jouw taken: "
                "1. Herschrijf het CV zodat de meest relevante ervaring voor de opdracht bovenaan staat. "
                "2. Schrijf een sterke, persoonlijke motivatie vanuit de kandidaat. "
                "3. Maak een eerlijke analyse van de tekortkomingen van de kandidaat voor deze specifieke opdracht."
            )

            # 4. Placeholder voor de API call
            response = client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Opdracht: {job_description}\n\nCV Tekst: {cv_text}"}
                ],
                temperature=0.3 #dit bepaalt hoe zakelijk het model is
            )

            resultaat = response.choices[0].message.content

            # 5. Resultaat tonen
            st.success("Klaar!")
            st.markdown("---")
            st.markdown(resultaat)
    else:
        st.error("Sorry, er is iets foutgegaan, upload a.u.b. een CV en voer een opdracht in.")