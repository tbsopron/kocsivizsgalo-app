import streamlit as st
import os
from datetime import datetime
from urllib.parse import quote
from fpdf import FPDF
import tempfile

# --- OLDAL BEÁLLÍTÁSAI (Mobilbarát nézet és GYSEV színek) ---
st.set_page_config(page_title="Kocsivizsgáló App", page_icon="🚂", layout="centered")

# Egyedi vasutas arculat (sötétkék alap, zöld gombok)
st.markdown("""
    <style>
    .stApp { background-color: #1A2B35; color: white; }
    h1, h2, h3, p, label { color: white !important; }
    div.stButton > button {
        width: 100%;
        background-color: #647413 !important;
        color: white !important;
        font-weight: bold;
        border: none;
        padding: 10px;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #263843 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- MUNKAMENET ÁLLAPOTOK INICIALIZÁLÁSA ---
if 'step' not in st.session_state:
    st.session_state.step = 'login'
if 'felhasznalo_nev' not in st.session_state:
    st.session_state.felhasznalo_nev = ""
if 'szolg_hely' not in st.session_state:
    st.session_state.szolg_hely = ""
if 'vonatszam' not in st.session_state:
    st.session_state.vonatszam = ""
if 'vaganyszam' not in st.session_state:
    st.session_state.vaganyszam = ""
if 'hibak' not in st.session_state:
    st.session_state.hibak = []
if 'muvelet_tipus' not in st.session_state:
    st.session_state.muvelet_tipus = ""

# --- KARAKTERTISZTÍTÓ AZ FPDF MIATT ---
def tiszta_szoveg(text):
    atfedes = {
        'á': 'a', 'Á': 'A', 'é': 'e', 'É': 'E', 'í': 'i', 'Í': 'I',
        'ó': 'o', 'Ó': 'O', 'ö': 'o', 'Ö': 'O', 'ő': 'o', 'Ő': 'O',
        'ú': 'u', 'Ú': 'U', 'ü': 'u', 'Ü': 'U', 'ű': 'u', 'Ű': 'U'
    }
    for k, v in atfedes.items():
        text = text.replace(k, v)
    return text

def reset_adatok():
    st.session_state.hibak = []

# --- 1. KÉPERNYŐ: BEJELENTKEZÉS ---
if st.session_state.step == 'login':
    st.title("KOCSIVIZSGÁLÓ APP v2.0 (Web)")
    st.subheader("Bejelentkezés")
    
    nev = st.text_input("Felhasználó név", value=st.session_state.felhasznalo_nev)
    if st.button("BEJELENTKEZÉS"):
        if nev:
            st.session_state.felhasznalo_nev = nev
            st.session_state.step = 'selection'
            st.rerun()

# --- 2. KÉPERNYŐ: ADATOK ÉS MŰVELET VÁLASZTÁS ---
elif st.session_state.step == 'selection':
    st.title(f"Üdvözöllek, {st.session_state.felhasznalo_nev}!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.szolg_hely = st.text_input("Szolg. hely", value=st.session_state.szolg_hely)
    with col2:
        st.session_state.vonatszam = st.text_input("Vonatszám", value=st.session_state.vonatszam)
    with col3:
        st.session_state.vaganyszam = st.text_input("Vágányszám", value=st.session_state.vaganyszam)
        
    st.write("---")
    
    if st.button("VONATVIZSGÁLAT INDÍTÁSA"):
        st.session_state.muvelet_tipus = "Vonatvizsgálat"
        st.session_state.step = 'working'
        st.rerun()
        
    if st.button("FÉKPRÓBA INDÍTÁSA"):
        st.session_state.muvelet_tipus = "Fékpróba"
        st.session_state.step = 'working'
        st.rerun()
        
    if st.button("KIJELENTKEZÉS / NÉVVÁLTÁS", use_container_width=True):
        st.session_state.step = 'login'
        st.rerun()

# --- 3. KÉPERNYŐ: IDŐVONALAS RÖGZÍTÉS ÉS PDF GENERÁLÁS ---
elif st.session_state.step == 'working':
    st.title(f"{st.session_state.muvelet_tipus.upper()} RÖGZÍTÉSE")
    st.write(f"**Vonat:** {st.session_state.vonatszam} | **Vágány:** {st.session_state.vaganyszam} | **Hely:** {st.session_state.szolg_hely}")
    
    # Úrlapelem, ami beküldés után automatikusan kiürül
    with st.form(key="beviszi_form", clear_on_submit=True):
        leiras = st.text_area("Hiba leírása / Megjegyzés:")
        foto = st.file_uploader("Fotó készítése vagy csatolása (Kamera/Galéria):", type=["jpg", "png", "jpeg"])
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            submit_foto = st.form_submit_button("FOTÓ + SZÖVEG RÖGZÍTÉSE")
        with col_b2:
            submit_szoveg = st.form_submit_button("CSAK SZÖVEG RÖGZÍTÉSE")
            
        if submit_foto:
            if foto is not None:
                st.session_state.hibak.append({
                    "szoveg": leiras if leiras.strip() else "[Csatolt foto leiras nelkul]",
                    "kep_bytes": foto.read(),
                    "kep_name": foto.name
                })
                st.toast("Fotós bejegyzés hozzáadva!")
                st.rerun()
            else:
                st.warning("Nem választottál fotót! Használd a 'Csak szöveg' gombot.")
                
        if submit_szoveg:
            if leiras.strip():
                st.session_state.hibak.append({
                    "szoveg": leiras,
                    "kep_bytes": None,
                    "kep_name": ""
                })
                st.toast("Szöveges bejegyzés hozzáadva!")
                st.rerun()

    st.write("---")
    st.subheader("Dokumentum idővonal (Élő külalak ellenőrzés):")
    
    if not st.session_state.hibak:
        st.info("Még nincs rögzített bejegyzés ezen a lapon.")
    else:
        for i, elem in enumerate(st.session_state.hibak, 1):
            st.markdown(f"**{i}. Bejegyzés:** {elem['szoveg']}")
            if elem['kep_bytes']:
                st.image(elem['kep_bytes'], width=300)
            st.write("")

    st.write("---")
    
    # --- PDF GENERÁLÁS MEMÓRIÁBAN ---
    if st.session_state.hibak:
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"Jegyzokonyv: {tiszta_szoveg(st.session_state.muvelet_tipus)}", ln=True, align='C')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Idopont: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.ln(5)
        pdf.cell(200, 10, txt=f"Nev: {tiszta_szoveg(st.session_state.felhasznalo_nev)}", ln=True)
        pdf.cell(200, 10, txt=f"Szolgalati hely: {tiszta_szoveg(st.session_state.szolg_hely)}", ln=True)
        pdf.cell(200, 10, txt=f"Vonatszam: {tiszta_szoveg(st.session_state.vonatszam)} | Vagany: {tiszta_szoveg(st.session_state.vaganyszam)}", ln=True)
        pdf.ln(10)
        
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Esemenyek es Vizsgalati adatok (Idovonal):", ln=True)
        pdf.ln(5)
        
        for idx, elem in enumerate(st.session_state.hibak, 1):
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 8, txt=f"{idx}. Bejegyzes:", ln=True)
            pdf.set_font("Arial", size=12)
            pdf.multi_cell(0, 8, txt=tiszta_szoveg(elem['szoveg']))
            pdf.ln(2)
            
            if elem['kep_bytes']:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(elem['kep_bytes'])
                    tmp_path = tmp.name
                try:
                    pdf.image(tmp_path, w=110)
                    pdf.ln(8)
                finally:
                    os.unlink(tmp_path)
            else:
                pdf.ln(4)
                
        pdf_output = pdf.output(dest='S').encode('latin-1')
        
        # Letöltés gomb
        st.download_button(
            label="📥 PDF JELENTÉS LETÖLTÉSE",
            data=pdf_output,
            file_name=f"Riport_{st.session_state.vonatszam}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
        
        # E-mail indító gomb
        subject = quote(f"Vasúti Jegyzőkönyv - {st.session_state.vonatszam}")
        body = quote(f"Tisztelt Diszpécser!\n\nMellékelten küldöm a {st.session_state.muvelet_tipus} során rögzített adatokat.\nA letöltött PDF-et kérjük csatolni.")
        mailto_url = f"mailto:?subject={subject}&body={body}"
        
        st.markdown(f'<a href="{mailto_url}" target="_blank"><button style="width:100%; background-color:#1F5A85 !important; color:white; padding:10px; border:none; font-weight:bold; border-radius:4px; margin-top:10px;">📧 LEVELEZŐ MEGNYITÁSA (DISZPÉCSER)</button></a>', unsafe_allow_html=True)

    st.write("---")
    col_back1, col_back2 = st.columns(2)
    with col_back1:
        if st.button("MINDENT TÖRÖL"):
            reset_adatok()
            st.rerun()
    with col_back2:
        if st.button("VISSZA A FŐMENÜBE"):
            st.session_state.step = 'selection'
            st.rerun()