import streamlit as st
from fpdf import FPDF
import tempfile
import os

# 1. Oldal konfigurációja
st.set_page_config(page_title="GYSEV Kocsivizsgáló App", page_icon="🚂", layout="centered")

st.title("🚂 GYSEV Kocsivizsgáló Webalkalmazás")
st.write("Műszaki vonatvizsgálati adatok rögzítése és automatikus PDF riport generálása")

st.markdown("---")

# 2. Adatbeviteli mezők (a Kivy projekt mezői alapján optimalizálva)
col1, col2, col3 = st.columns(3)

with col1:
    szolg_hely = st.text_input("Szolgálati hely", placeholder="pl. Sopron")

with col2:
    vonatszam = st.text_input("Vonatszám", placeholder="pl. 43122")

with col3:
    vaganyszam = st.text_input("Vágányszám", placeholder="pl. V.")

st.markdown("### 📋 Észlelt hibák / Megjegyzések")
megjegyzesek = st.text_area("Írd le a vizsgált vonat hibáit vagy a vizsgálat észrevételeit...", height=120)

st.markdown("### 📸 Fénykép csatolása")
uploaded_file = st.file_uploader("Válassz ki egy fotót a vizsgálatról", type=["jpg", "jpeg", "png"])

# Élő kép-előnézet a webes felületen, ha van feltöltött fájl
if uploaded_file is not None:
    st.image(uploaded_file, caption="A csatolt fénykép előnézete", use_container_width=True)

st.markdown("---")

# 3. PDF Generálása és letöltése szigorúan gombnyomásra
if st.button("📄 PDF Jelentés Elkészítése", type="primary"):
    if not szolg_hely or not vonatszam:
        st.error("Hiba: A Szolgálati hely és a Vonatszám mező kitöltése kötelező!")
    else:
        with st.spinner("PDF dokumentum összeállítása..."):
            try:
                # FPDF objektum létrehozása
                pdf = FPDF()
                pdf.add_page()
                
                # Címsor (Standard Arial betűtípus az alapértelmezett fpdf csomaghoz)
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "VONATVIZSGALATI JEGYZOKONYV", ln=True, align="C")
                pdf.ln(10)
                
                # Alapadatok beírása
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Szolgalati hely: {szolg_hely}", ln=True)
                pdf.cell(0, 10, f"Vonatszam: {vonatszam}", ln=True)
                pdf.cell(0, 10, f"Vaganyszam: {vaganyszam}", ln=True)
                pdf.ln(5)
                
                # Megjegyzések beírása
                pdf.cell(0, 10, "Hibak / Megjegyzesek:", ln=True)
                pdf.set_font("Arial", "I", 11)
                pdf.multi_cell(0, 10, megjegyzesek if megjegyzesek else "Nincs eszlelt hiba.")
                pdf.ln(10)
                
                # --- A FOTÓ BIZTONSÁGOS, DINAMIKUS BEILLESZTÉSE ---
                # Ez a rész korábban az app indulásakor azonnal lefutott és hibát dobott.
                # Most már csak akkor aktiválódik, ha VALÓBAN van feltöltött kép!
                if uploaded_file is not None:
                    # Létrehozunk egy ideiglenes fájlt a szerver háttértárán, mert az FPDF-nek fizikai fájlútvonal kell
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name
                    
                    # Kép beillesztése a PDF-be biztonságos környezetben
                    pdf.image(tmp_path, w=110)
                    
                    # Azonnali biztonsági takarítás: miután a PDF-be került a kép, a felesleges ideiglenes fájlt töröljük
                    os.unlink(tmp_path)
                
                # PDF mentése letölthető bájtokká
                pdf_output = pdf.output(dest="S").encode("latin-1", errors="ignore")
                
                st.success("🎉 A PDF jelentés sikeresen elkészült!")
                
                # Streamlit letöltő gomb biztosítása a felhasználónak
                st.download_button(
                    label="📥 PDF Fájl Letöltése",
                    data=pdf_output,
                    file_name=f"Kocsivizsgalo_Jelentes_{vonatszam}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Hiba történt a PDF generálása közben: {e}")
