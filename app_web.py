import streamlit as st
from fpdf import FPDF
import tempfile
import os
from datetime import datetime
from PIL import Image
import urllib.parse
import re

# 1. Oldal konfigurációja
st.set_page_config(page_title="GYSEV Kocsivizsgáló App", page_icon="🚂", layout="centered")

# --- GYSEV ARCULAT CSS ÉS JAVÍTÁSOK ---
st.markdown("""
    <style>
        div.stButton > button[kind="primary"] {
            background-color: #007A33 !important;
            color: #FFFFFF !important;
            border-radius: 8px;
            border: 2px solid #FFD100 !important;
            font-weight: bold;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #005F26 !important;
            color: #FFD100 !important;
        }
        div.stButton > button[kind="secondary"] {
            background-color: #6C757D !important;
            color: white !important;
            border-radius: 8px;
            border: none;
        }
        div.stButton > button[kind="secondary"]:hover {
            background-color: #5A6268 !important;
        }
        /* Rádió gombok (műveletválasztó) finomhangolása */
        div[data-testid="stRadio"] > label {
            color: #007A33 !important;
            font-weight: bold !important;
            font-size: 16px;
        }
        .mail-button {
            display: inline-block;
            padding: 0.5rem 1rem;
            background-color: #FFD100 !important;
            color: #007A33 !important;
            font-weight: bold;
            text-decoration: none;
            border-radius: 8px;
            border: 2px solid #007A33;
            text-align: center;
            margin-top: 10px;
        }
        .mail-button:hover {
            background-color: #E6BC00 !important;
            color: #005F26 !important;
        }
        h1 { color: #007A33 !important; }
        h3 {
            color: #007A33 !important;
            border-bottom: 2px solid #FFD100;
            padding-bottom: 5px;
        }
        .kocsi-box {
            padding: 15px;
            border: 1px solid #007A33;
            border-radius: 8px;
            margin-bottom: 15px;
            background-color: #F8F9FA;
        }
    </style>
    
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const inputs = document.querySelectorAll('input[type="file"]');
            inputs.forEach(input => {
                input.setAttribute("accept", "image/*");
            });
        });
    </script>
""", unsafe_allow_html=True)

st.title("🚂 GYSEV Kocsivizsgáló Webalkalmazás")
st.write("**Műszaki vonatvizsgálati és fékpróba adatok rögzítése és PDF generálás**")

st.markdown("---")

# --- MUNKAMENET ÁLLAPOTOK (SESSION STATE) ---
if 'file_uploader_keys' not in st.session_state:
    st.session_state.file_uploader_keys = {}
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'vonatszam_mentett' not in st.session_state:
    st.session_state.vonatszam_mentett = ""
if 'show_email_dialog' not in st.session_state:
    st.session_state.show_email_dialog = False

if 'hibas_kocsik' not in st.session_state:
    st.session_state.hibas_kocsik = [{"kocsiszam": "", "leiras": "", "kepek": []}]

# --- KOCSISZÁM FORMÁZÓ FUNKCIÓ ---
def formal_kocsiszam(nyers_szam):
    szamok = re.sub(r'\D', '', nyers_szam)
    if len(szamok) == 12:
        return f"{szamok[0:2]} {szamok[2:4]} {szamok[4:8]} {szamok[8:11]}-{szamok[11]}"
    return nyers_szam

# --- TELJES TÖRLÉSI FUNKCIÓ ---
def adatok_torlese_callback():
    st.session_state.felhasznalonev = ""
    st.session_state.szolg_hely = ""
    st.session_state.vonatszam = ""
    st.session_state.vaganyszam = ""
    
    for kulcs in st.session_state.file_uploader_keys.keys():
        st.session_state.file_uploader_keys[kulcs] += 1
        
    st.session_state.hibas_kocsik = [{"kocsiszam": "", "leiras": "", "kepek": []}]
    st.session_state.pdf_data = None
    st.session_state.vonatszam_mentett = ""
    st.session_state.show_email_dialog = False

# --- ⚙️ MŰVELET KIVÁLASZTÁSA ---
st.markdown("### 🛠️ Végzett munkafolyamat kiválasztása")
muvelet = st.radio(
    "Válassz műveletet:",
    ["Vonatvizsgálat 🔍", "Fékpróba 🛑"],
    horizontal=True
)

st.markdown("---")

# 2. Alapadatok elrendezése
st.markdown("### 🏢 Vizsgálati Alapadatok")
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

aktualis_ido_str = datetime.now().strftime("%Y-%m-%d %H:%M")
st.text_input("Vizsgálat időpontja (Automatikus)", value=aktualis_ido_str, disabled=True)

# --- 📜 DINAMIKUS ERDMÉNY / SABLONVÁLASZTÓ ---
st.markdown("### 📢 Vizsgálat eredménye / Állapota")
if "Fékpróba" in muvelet:
    sablonszoveg_opciok = ["Fék rendben", "Az alábbi kocsik nem fékeznek:"]
else:
    sablonszoveg_opciok = ["Vonat rendben", "Vonatban a következő hibákat találtam:"]

kivalasztott_statusz = st.selectbox("Válaszd ki a megfelelő megállapítást:", sablonszoveg_opciok)

# --- 📋 DINAMIKUS KOCSI-HIBA SZEKCIÓ ---
st.markdown("### 📋 Észlelt kocsik / hibák részletezése")
st.caption("Ha a 'rendben' opciót választottad fent, ezt a szekciót üresen is hagyhatod.")

for idx, kocsi in enumerate(st.session_state.hibas_kocsik):
    st.markdown(f'<div class="kocsi-box">', unsafe_allow_html=True)
    st.write(f"**{idx + 1}. Érintett kocsi adatai**")
    
    k1, k2 = st.columns([1, 2])
    with k1:
        nyers_kocsiszam = st.text_input(f"Kocsiszám (12 jegyű)", value=kocsi["kocsiszam"], key=f"kocsi_szam_{idx}", placeholder="pl. 315566123451")
        formazott = formal_kocsiszam(nyers_kocsiszam)
        if len(re.sub(r'\D', '', nyers_kocsiszam)) == 12:
            st.success(f"Formátum OK: `{formazott}`")
            st.session_state.hibas_kocsik[idx]["kocsiszam"] = formazott
        elif nyers_kocsiszam != "":
            st.warning("⚠️ Kérjük, pontosan 12 számjegyet adj meg!")
            st.session_state.hibas_kocsik[idx]["kocsiszam"] = nyers_kocsiszam

    with k2:
        st.session_state.hibas_kocsik[idx]["leiras"] = st.text_area(
            f"Hiba / Észrevétel leírása ({idx + 1}. kocsi)", 
            value=kocsi["leiras"], 
            key=f"kocsi_leiras_{idx}", 
            height=68,
            placeholder="pl. Nem működik a kormányszelep / Laposodás..."
        )
    
    if idx not in st.session_state.file_uploader_keys:
        st.session_state.file_uploader_keys[idx] = 0
        
    uploaded_files = st.file_uploader(
        f"Fotók csatolása a(z) {idx + 1}. kocsihoz", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True,
        key=f"kocsi_foto_{idx}_{st.session_state.file_uploader_keys[idx]}"
    )
    st.session_state.hibas_kocsik[idx]["kepek"] = uploaded_files if uploaded_files else []
    
    if uploaded_files:
        grid_cols = st.columns(4)
        for f_idx, file in enumerate(uploaded_files):
            with grid_cols[f_idx % 4]:
                st.image(file, caption=file.name, use_container_width=True)
                
    st.markdown('</div>', unsafe_allow_html=True)

c_btn1, c_btn2, _ = st.columns([1, 1, 2])
with c_btn1:
    if st.button("➕ Új kocsi hozzáadása", use_container_width=True):
        st.session_state.hibas_kocsik.append({"kocsiszam": "", "leiras": "", "kepek": []})
        st.rerun()
with c_btn2:
    if len(st.session_state.hibas_kocsik) > 1:
        if st.button("➖ Utolsó kocsi törlése", use_container_width=True):
            st.session_state.hibas_kocsik.pop()
            st.rerun()

st.markdown("---")

btn_col1, btn_col2 = st.columns([2, 1])
with btn_col1:
    generate_pdf = st.button("📄 PDF Jelentés Elkészítése", type="primary")
with btn_col2:
    st.button("🗑️ Adatok törlése", type="secondary", on_click=adatok_torlese_callback)

# 3. PDF Generálása kibővített tartalommal
if generate_pdf:
    if not felhasznalonev or not szolg_hely or not vonatszam:
        st.error("Hiba: A Felhasználónév, Szolgálati hely és a Vonatszám mezők kitöltése kötelező!")
    else:
        with st.spinner("PDF dokumentum összeállítása és képek feldolgozása..."):
            try:
                pdf = FPDF()
                pdf.add_page()
                
                # Dinamikus fejléc a választott művelet alapján
                tiszta_muvelet = muvelet.replace(" 🔍", "").replace(" 🛑", "").upper()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, f"{tiszta_muvelet} JEGYZOKONYV", ln=True, align="C")
                pdf.ln(10)
                
                # Alapadatok
                pdf.set_font("Arial", "", 12)
                pdf.cell(0, 8, f"Kocsivizsgalo: {felhasznalonev}", ln=True)
                pdf.cell(0, 8, f"Szolgalati hely: {szolg_hely}", ln=True)
                pdf.cell(0, 8, f"Vonatszam: {vonatszam}", ln=True)
                pdf.cell(0, 8, f"Vaganyszam: {vaganyszam}", ln=True)
                pdf.cell(0, 8, f"Muvelet tipusa: {tiszta_muvelet}", ln=True)
                pdf.cell(0, 8, f"Idopont: {aktualis_ido_str}", ln=True)
                pdf.ln(8)
                
                # Állapot / Eredmény rögzítése
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, f"VIZSGALAT ERDEMENTE: {kivalasztott_statusz.upper()}", ln=True)
                pdf.ln(5)
                
                # Csak akkor részletezzük a kocsikat, ha a felhasználó rögzített adatot vagy nem a "rendben" státuszt választotta
                van_adat = any(kocsi['kocsiszam'] or kocsi['leiras'] or kocsi['kepek'] for kocsi in st.session_state.hibas_kocsik)
                
                if van_adat:
                    pdf.set_font("Arial", "B", 14)
                    pdf.cell(0, 10, "ERINTETT KOCSIK ES ESZREVETELEK:", ln=True)
                    pdf.ln(2)
                    
                    for idx, kocsi in enumerate(st.session_state.hibas_kocsik):
                        # Ha teljesen üres a sor, átugorhatjuk a szép riport érdekében
                        if not kocsi['kocsiszam'] and not kocsi['leiras'] and not kocsi['kepek']:
                            continue
                            
                        pdf.set_font("Arial", "B", 12)
                        kocsi_fejlec = f"{idx + 1}. Kocsiszam: {kocsi['kocsiszam'] if kocsi['kocsiszam'] else 'Nincs megadva'}"
                        pdf.cell(0, 8, kocsi_fejlec, ln=True)
                        
                        pdf.set_font("Arial", "", 11)
                        pdf.cell(0, 6, "Reszletek / Leiras:", ln=True)
                        pdf.set_font("Arial", "I", 11)
                        pdf.multi_cell(0, 6, kocsi["leiras"] if kocsi["leiras"] else "Nincs kulon leiras megadva.")
                        pdf.ln(4)
                        
                        if kocsi["kepek"]:
                            pdf.set_font("Arial", "B", 10)
                            pdf.cell(0, 6, f"Csatolt fotok ({len(kocsi['kepek'])} db):", ln=True)
                            pdf.ln(2)
                            
                            for img_file in kocsi["kepek"]:
                                img = Image.open(img_file)
                                if img.mode in ("RGBA", "P"):
                                    img = img.convert("RGB")
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                                    img.save(tmp_file, format="JPEG", quality=85)
                                    tmp_path = tmp_file.name
                                
                                pdf.image(tmp_path, w=90)
                                pdf.ln(5)
                                os.unlink(tmp_path)
                        
                        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                        pdf.ln(5)
                else:
                    pdf.set_font("Arial", "I", 12)
                    pdf.cell(0, 10, "Kulon listazando hiba vagy rendellenesseg nem lett rogzitve.", ln=True)
                
                st.session_state.pdf_data = pdf.output(dest="S").encode("latin-1", errors="ignore")
                st.session_state.vonatszam_mentett = vonatszam
                st.session_state.show_email_dialog = True
                st.success("🎉 A strukturált PDF jelentés elkészült!")
                
            except Exception as e:
                st.error(f"Hiba történt a PDF generálása közben: {e}")

# --- 4. EMAIL DIALÓGUS ---
@st.dialog("📧 Küldés e-mailben")
def email_kuldes_dialog():
    st.write("Szeretnéd azonnal továbbítani a riportot e-mailben?")
    st.info("💡 **Fontos:** Először mentsd el a PDF-et a készülékre, majd a megnyíló e-mailben manuálisan csatold azt!")
    
    st.download_button(
        label="📥 1. Lépés: PDF Letöltése/Mentése",
        data=st.session_state.pdf_data,
        file_name=f"Kocsivizsgalo_Jelentes_{st.session_state.vonatszam_mentett}.pdf",
        mime="application/pdf",
        key="dialog_download"
    )
    
    tiszta_muvelet = muvelet.replace(" 🔍", "").replace(" 🛑", "")
    subject = f"GYSEV {tiszta_muvelet} Jelentés - Vonat: {st.session_state.vonatszam_mentett} ({kivalasztott_statusz})"
    body = f"Tisztelt Címzett!\n\nMellékelten küldöm a(z) {tiszta_muvelet} jegyzőkönyvet.\n\nVonatszám: {st.session_state.vonatszam_mentett}\nEredmény: {kivalasztott_statusz}\n\nÜdvözlettel,\n{st.session_state.felhasznalonev}"
    
    mailto_url = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.markdown(f'<a href="{mailto_url}" target="_blank" class="mail-button">🚀 2. Lépés: OK (E-mail megnyitása)</a>', unsafe_allow_html=True)
    with d_col2:
        if st.button("❌ Mégse (Bezárás)", use_container_width=True):
            st.session_state.show_email_dialog = False
            st.rerun()

if st.session_state.show_email_dialog and st.session_state.pdf_data is not None:
    email_kuldes_dialog()

# 5. Statikus Letöltés gomb a főoldalon
if st.session_state.pdf_data is not None and not st.session_state.show_email_dialog:
    st.markdown("### 📄 Elkészült jelentés")
    st.download_button(
        label="📥 PDF Fájl Letöltése újra",
        data=st.session_state.pdf_data,
        file_name=f"Kocsivizsgalo_Jelentes_{st.session_state.vonatszam_mentett}.pdf",
        mime="application/pdf"
    )
