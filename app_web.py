import streamlit as st
from fpdf import FPDF
import tempfile
import os

# 1. Oldal konfigurációja
st.set_page_config(page_title="GYSEV Kocsivizsgáló App", page_icon="🚂", layout="centered")

st.title("🚂 GYSEV Kocsivizsgáló Webalkalmazás")
st.write("Műszaki vonatvizsgálati adatok rögzítése és automatikus PDF riport generálása")

st.markdown("---")

# 2. Adatbeviteli mezők
col1, col2, col3 = st.columns(3)

with col1:
    szolg_hely = st.text_input("Szolgálati hely", placeholder="pl. Sopron")

with col2:
    vonatszam = st.text_input("Vonatszám", placeholder="pl. 43122")

with col3:
    vaganyszam = st.text_input("Vágányszám", placeholder="pl. V.")

st.markdown("### 📋 Észlelt hibák / Megjegyzések")
megjegyzesek = st.text_area("Írd le a vizsgált vonat hibáit vagy a vizsgálat észrevételeit...", height=120)

st.markdown("### 📸 Fényképek csatolása")
# Átállítva többszörös kijelölésre: accept_multiple_files=True
uploaded_files = st.file_uploader(
    "Válassz ki fotókat a vizsgálatról (akár többet is egyszerre)", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

# Élő kép-előnézet rácsos elrendezésben, hogy ne nyújtsa meg nagyon az oldalt
if uploaded_files:
    st.write(f"📸 Csatolt képek száma: **{len(uploaded_files)}** db")
    grid_cols = st.columns(3)  # 3 kép fér el egymás mellett a képernyőn
    for idx, file in enumerate(uploaded_files):
        with grid_cols[idx % 3]:
            st.image(file, caption=file.name, use_container_width=True)

st.markdown("---")

# 3. PDF Generálása és letöltése gombnyomásra
if st.button("📄 PDF Jelentés Elkészítése", type="primary"):
    if not szolg_hely or not vonatszam:
        st.error("Hiba: A Szolgálati hely és a Vonatszám mező kitöltése kötelező!")
    else:
        with st.spinner("PDF dokumentum összeállítása a képekkel..."):
            try:
                # FPDF objektum létrehozása
                pdf = FPDF()
                pdf.add_page()
                
                # Címsor (Standard Arial)
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
                
                # --- TÖBB FOTÓ BEILLESZTÉSE CIKLUSSAL ---
                if uploaded_files:
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(0, 10, f"Csatolt fenykepek ({len(uploaded_files)} db):", ln=True)
                    pdf.ln(5)
                    
                    for file in uploaded_files:
                        # Kiterjesztés automatikus meghatározása (.jpg, .png, stb.)
                        _, ext = os.path.splitext(file.name)
                        
                        # Ideiglenes fájl létrehozása az adott képnek
                        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                            tmp_file.write(file.getvalue())
                            tmp_path = tmp_file.name
                        
                        # Kép beillesztése (Szélesség: 100mm). 
                        # Ha nem fér el az aktuális lapon, az FPDF automatikusan új oldalt kezd neki!
                        pdf.image(tmp_path, w=100)
                        pdf.ln(10)  # Kis szünet a következő kép előtt
                        
                        # Ideiglenes fájl azonnali törlése
                        os.unlink(tmp_path)
                
                # PDF mentése letölthető bájtokká
                pdf_output = pdf.output(dest="S").encode("latin-1", errors="ignore")
                
                st.success("🎉 A PDF jelentés az összes képpel együtt sikeresen elkészült!")
                
                # Streamlit letöltő gomb
                st.download_button(
                    label="📥 PDF Fájl Letöltése",
                    data=pdf_output,
                    file_name=f"Kocsivizsgalo_Jelentes_{vonatszam}.pdf",
                    mime="application/pdf"
                )
                
            except Exception as e:
                st.error(f"Hiba történt a PDF generálása közben: {e}")
