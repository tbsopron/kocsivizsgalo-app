import streamlit as st
from fpdf import FPDF
import tempfile
import os
from datetime import datetime
from PIL import Image  # Képhibák végleges kiküszöbölésére

# 1. Oldal konfigurációja
st.set_page_config(page_title="GYSEV Kocsivizsgáló App", page_icon="🚂", layout="centered")

st.title("🚂 GYSEV Kocsivizsgáló Webalkalmazás")
st.write("Műszaki vonatvizsgálati adatok rögzítése és automatikus PDF riport generálása")

st.markdown("---")

# Kezdeti állapotok beállítása a memóriában
if 'file_uploader_key' not in st.session_state:
    st.session_state.file_uploader_key = 0
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'vonatszam_mentett' not in st.session_state:
    st.session_state.vonatszam_mentett = ""

# --- BIZTONSÁGOS TÖRLÉSI FUNKCIÓ (CALLBACK) ---
def adatok_torlese_callback():
    st.session_state.felhasznalonev = ""
    st.session_state.szolg_hely = ""
    st.session_state.vonatszam = ""
    st.session_state.vaganyszam = ""
    st.session_state.megjegyzesek = ""
    st.session_state.file_uploader_key += 1
    st.session_state.pdf_data = None
    st.session_state.vonatszam_mentett = ""

# 2. Adatbeviteli mezők elrendezése
col1, col2 = st.columns(2)
with col1:
    felhasznalonev = st.text_input("Felhasználónév (Kocsivizsgáló)", key="felhasznalonev", placeholder="pl. Tóth Balázs")
with col2:
    szolg_hely = st.text_input("Szolgálati hely", key="szolg_hely", placeholder="pl. Sopron")

col3, col4 = st.columns(2)
with col3:
    vonatszam = st.text_input("Vonatszám", key="vonatszam", placeholder="pl. 43122")
with col4:
    vaganyszam = st.text_input("Vágányszám", key="vaganyszam", placeholder="pl. V.")

# Élő, automatikus időbélyegző a felületen és a jelentésben
aktualis_ido_str = datetime.now().strftime("%Y-%m-%d %H:%M")
st.text_input("Vizsgálat időpontja (Automatikus)", value=aktualis_ido_str, disabled=True)

st.markdown("### 📋 Észlelt hibák / Megjegyzések")
megjegyzesek = st.text_area("Írd le a vizsgált vonat hibáit vagy a vizsgálat észrevételeit...", key="megjegyzesek", height=120)

st.markdown("### 📸 Fényképek csatolása")
uploaded_files = st.file_uploader(
    "Válassz ki fotókat a vizsgálatról (akár többet is egyszerre)", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.file_uploader_key}"
)

if uploaded_files:
    st.write(f"📸 Csatolt képek száma: **{len(uploaded_files)}** db")
    grid_cols = st.columns(3)
    for idx, file in enumerate(uploaded_files):
        with grid_cols[idx % 3]:
            st.image(file, caption=file.name, use_container_width=True)

st.markdown("---")

# Gombok elhelyezése
btn_col1, btn_col2 = st.columns([2, 1])

with btn_col1:
    generate_pdf = st.button("📄 PDF Jelentés Elkészítése", type="primary")

with btn_col2:
    st.button("🗑️ Adatok törlése", type="secondary", on_click=adatok_torlese_callback)

# 3. PDF Generálása gombnyomásra
if generate_pdf:
    if not felhasznalonev or not szolg_hely or not vonatszam:
        st.error("Hiba: A Felhasználónév, Szolgálati hely és a Vonatszám mezők kitöltése kötelező!")
    else:
        with st.spinner("PDF dokumentum összeállítása a képekkel..."):
            try:
                pdf = FPDF()
                pdf.add_page()
                
                # Címsor
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "VONATVIZSGALATI JEGYZOKONYV", ln=True, align="C")
                pdf.ln(10)
                
                # Alapadatok + Időbélyegző rögzítése a PDF-ben
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 10, f"Kocsivizsgalo: {felhasznalonev}", ln=True)
                pdf.cell(0, 10, f"Szolgalati hely: {szolg_hely}", ln=True)
                pdf.cell(0, 10, f"Vonatszam: {vonatszam}", ln=True)
                pdf.cell(0, 10, f"Vaganyszam: {vaganyszam}", ln=True)
                pdf.cell(0, 10, f"Vizsgalat idopontja: {aktualis_ido_str}", ln=True)
                pdf.ln(5)
                
                # Megjegyzések
                pdf.cell(0, 10, "Hibak / Megjegyzesek:", ln=True)
                pdf.set_font("Arial", "I", 11)
                pdf.multi_cell(0, 10, megjegyzesek if megjegyzesek else "Nincs eszlelt hiba.")
                pdf.ln(10)
                
                # Fotók feldolgozása és beillesztése
                if uploaded_files:
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(0, 10, f"Csatolt fenykepek ({len(uploaded_files)} db):", ln=True)
                    pdf.ln(5)
                    
                    for file in uploaded_files:
                        img = Image.open(file)
                        if img.mode in ("RGBA", "P"):
                            img = img.convert("RGB")  # Átlátszósági réteg törlése a PDF kompatibilitás miatt
                        
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                            img.save(tmp_file, format="JPEG", quality=85)
                            tmp_path = tmp_file.name
                        
                        pdf.image(tmp_path, w=100)
                        pdf.ln(10)
                        os.unlink(tmp_path)
                
                st.session_state.pdf_data = pdf.output(dest="S").encode("latin-1", errors="ignore")
                st.session_state.vonatszam_mentett = vonatszam
                st.success("🎉 A PDF jelentés sikeresen elkészült!")
                
            except Exception as e:
                st.error(f"Hiba történt a PDF generálása közben: {e}")

# 4. Letöltés gomb megjelenítése (ha a PDF már elkészült)
if st.session_state.pdf_data is not None:
    st.download_button(
        label="📥 PDF Fájl Letöltése",
        data=st.session_state.pdf_data,
        file_name=f"Kocsivizsgalo_Jelentes_{st.session_state.vonatszam_mentett}.pdf",
        mime="application/pdf"
    )
