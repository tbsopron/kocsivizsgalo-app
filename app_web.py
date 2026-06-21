import streamlit as st
from fpdf import FPDF
import tempfile
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from PIL import Image, ImageOps
import urllib.parse
import re

# 1. Oldal konfigurációja
st.set_page_config(page_title="GYSEV Kocsivizsgáló App", page_icon="🚂", layout="centered")

# --- GOLYÓÁLLÓ ÉKEZETMENTESÍTŐ FUNKCIÓ ---
def biztonsagos_szoveg(szoveg):
    if not szoveg:
        return ""
    trans_table = str.maketrans({
        'á': 'a', 'Á': 'A', 'é': 'e', 'É': 'E', 'í': 'i', 'Í': 'I',
        'ó': 'o', 'Ó': 'O', 'ö': 'o', 'Ö': 'O', 'ő': 'o', 'Ő': 'O',
        'ú': 'u', 'Ú': 'U', 'ü': 'u', 'Ü': 'U', 'ű': 'u', 'Ű': 'U'
    })
    return str(szoveg).translate(trans_table)

# --- PONTOS BUDAPESTI IDŐ FÜGGVÉNY ---
def aktualis_budapesti_ido():
    return datetime.now(ZoneInfo("Europe/Budapest")).strftime("%Y-%m-%d %H:%M")

# --- GYSEV ARCULAT CSS ---
st.markdown("""
    <style>
        div.stButton > button[kind="primary"] {
            background-color: #007A33 !important; color: #FFFFFF !important;
            border-radius: 8px; border: 2px solid #FFD100 !important; font-weight: bold;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #005F26 !important; color: #FFD100 !important;
        }
        div.stButton > button[kind="secondary"] {
            background-color: #6C757D !important; color: white !important;
            border-radius: 8px; border: none;
        }
        div.stButton > button[kind="secondary"]:hover { background-color: #5A6268 !important; }
        .mail-button {
            display: inline-block; padding: 0.5rem 1rem; background-color: #FFD100 !important;
            color: #007A33 !important; font-weight: bold; text-decoration: none;
            border-radius: 8px; border: 2px solid #007A33; text-align: center; margin-top: 10px; width: 100%;
        }
        .mail-button:hover { background-color: #E6BC00 !important; color: #005F26 !important; }
        h1, h3 { color: #007A33 !important; }
        h3 { border-bottom: 2px solid #FFD100; padding-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("🚂 GYSEV Kocsivizsgáló Webalkalmazás")
st.write("**Műszaki vonatvizsgálati, RID és fékpróba adatok rögzítése**")
st.markdown("---")

# --- MUNKAMENET ÁLLAPOTOK (SESSION STATE) ---
if 'file_uploader_keys' not in st.session_state: st.session_state.file_uploader_keys = {}
if 'pdf_data' not in st.session_state: st.session_state.pdf_data = None
if 'vonatszam_mentett' not in st.session_state: st.session_state.vonatszam_mentett = ""
if 'show_email_dialog' not in st.session_state: st.session_state.show_email_dialog = False
if 'hibas_kocsik' not in st.session_state: st.session_state.hibas_kocsik = []

def formal_kocsiszam(nyers_szam):
    szamok = re.sub(r'\D', '', nyers_szam)
    if len(szamok) == 12:
        return f"{szamok[0:2]} {szamok[2:4]} {szamok[4:8]} {szamok[8:11]}-{szamok[11]}"
    return nyers_szam

def adatok_torlese_callback():
    st.session_state.felhasznalonev = ""
    st.session_state.szolg_hely = ""
    st.session_state.vonatszam = ""
    st.session_state.vaganyszam = ""
    for kulcs in list(st.session_state.file_uploader_keys.keys()):
        st.session_state.file_uploader_keys[kulcs] += 1
    st.session_state.hibas_kocsik = []
    st.session_state.pdf_data = None
    st.session_state.vonatszam_mentett = ""
    st.session_state.show_email_dialog = False

# --- 📧 EMAIL DIALÓGUS ---
@st.dialog("📧 Küldés e-mailben")
def email_kuldes_dialog(muvelet_nev, statusz_lista):
    st.write("Szeretnéd azonnal továbbítani a riportot e-mailben?")
    st.info("💡 **Fontos:** Először mentsd el a PDF-et a készülékre, majd a megnyíló e-mailben manuálisan csatold azt!")
    
    st.download_button(
        label="📥 1. Lépés: PDF Letöltése/Mentése", data=st.session_state.pdf_data,
        file_name=f"Kocsivizsgalo_Jelentes_{st.session_state.vonatszam_mentett}.pdf", mime="application/pdf", key="dialog_download"
    )
    
    statusz_szoveg = " | ".join(statusz_lista)
    subject = f"GYSEV Jelentes - Vonat: {st.session_state.vonatszam_mentett} ({muvelet_nev})"
    body = f"Tisztelt Cimzett!\n\nMellekelten kuldom a jegyzokonyvet a kovetkezohoz: {muvelet_nev}.\n\nVonatszam: {st.session_state.vonatszam_mentett}\nEredmeny(ek):\n{statusz_szoveg}\n\nUdvözlettel,\n{st.session_state.felhasznalonev}"
    
    mailto_url = f"mailto:?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    d_col1, d_col2 = st.columns(2)
    with d_col1: st.markdown(f'<a href="{mailto_url}" target="_blank" class="mail-button">🚀 2. Lépés: E-mail megnyitása</a>', unsafe_allow_html=True)
    with d_col2:
        if st.button("❌ Bezárás (Mégse)", use_container_width=True):
            st.session_state.show_email_dialog = False
            st.rerun()

# --- ⚙️ MŰVELET KIVÁLASZTÁSA ---
st.markdown("### 🛠️ Végzett munkafolyamat kiválasztása")
muvelet_csoport = st.radio("Válassz a fő műveletcsoportok közül:", ["Vonatvizsgálati és RID feladatok", "Fékpróba 🛑"])

opciok = []
kivalasztott_statuszok = []
muvelet_nev_kombinalt = ""

if muvelet_csoport == "Vonatvizsgálati és RID feladatok":
    opciok = st.multiselect("Válaszd ki az elvégzett feladatokat (többet is lehet):", ["Vonatvizsgálat", "RID ellenőrzés"])
    
    if "RID ellenőrzés" in opciok:
        rid_eredmeny = st.selectbox("RID ellenőrzés állapota:", ["RID rendben", "RID hiba"])
        kivalasztott_statuszok.append(f"RID: {rid_eredmeny}")
        
    if "Vonatvizsgálat" in opciok:
        vv_eredmeny = st.selectbox("Vonatvizsgálat állapota:", ["Vonat rendben", "Vonatban hibákat találtam"])
        kivalasztott_statuszok.append(f"Vonatvizsgalat: {vv_eredmeny}")
        
    muvelet_nev_kombinalt = " + ".join(opciok) if opciok else "Nincs kivalasztva feladat"

else:
    st.info("⚠️ Fékpróba kiválasztva. Ez a művelet önálló, nem vonható össze mással.")
    fk_eredmeny = st.selectbox("Fékpróba állapota:", ["Fék rendben", "Fék hiba: Az alábbi kocsik nem fékeznek"])
    kivalasztott_statuszok.append(f"Fekproba: {fk_eredmeny}")
    muvelet_nev_kombinalt = "Fekproba"

st.markdown("---")

# --- 🏢 ALAPADATOK ---
st.markdown("### 🏢 Vizsgálati Alapadatok")
col1, col2 = st.columns(2)
with col1: st.text_input("Felhasználónév (Kocsivizsgáló)", key="felhasznalonev", placeholder="pl. Tóth Balázs")
with col2: st.text_input("Szolgálati hely", key="szolg_hely", placeholder="pl. Sopron")

col3, col4 = st.columns(2)
with col3: st.text_input("Vonatszám", key="vonatszam", placeholder="pl. 43122")
with col4: st.text_input("Vágányszám", key="vaganyszam", placeholder="pl. V.")

st.text_input("Vizsgálat időpontja", value=aktualis_budapesti_ido(), disabled=True)

# --- 📋 KOCSI-HIBA SZEKCIÓ ---
st.markdown("### 📋 Észlelt kocsik / hibák részletezése")
if not st.session_state.hibas_kocsik:
    st.info("💡 Minden rendben? Ha hibás kocsit/fotót akarsz hozzáadni, nyomd meg a lenti 'Új kocsi hozzáadása' gombot.")

for idx, kocsi in enumerate(st.session_state.hibas_kocsik):
    with st.container(border=True):
        st.write(f"**{idx + 1}. Érintett kocsi adatai**")
        k1, k2 = st.columns([1, 2])
        with k1:
            nyers_kocsiszam = st.text_input(f"Kocsiszám (12 jegyű)", value=kocsi["kocsiszam"], key=f"kocsi_szam_{idx}")
            formazott = formal_kocsiszam(nyers_kocsiszam)
            if len(re.sub(r'\D', '', nyers_kocsiszam)) == 12:
                st.success(f"OK: `{formazott}`")
                st.session_state.hibas_kocsik[idx]["kocsiszam"] = formazott
            elif nyers_kocsiszam != "":
                st.warning("⚠️ 12 számjegyet adj meg!")
                st.session_state.hibas_kocsik[idx]["kocsiszam"] = nyers_kocsiszam

        with k2:
            st.session_state.hibas_kocsik[idx]["leiras"] = st.text_area(f"Hiba / Észrevétel", value=kocsi["leiras"], key=f"kocsi_leiras_{idx}", height=68)
        
        if idx not in st.session_state.file_uploader_keys: st.session_state.file_uploader_keys[idx] = 0
        
        feltoltott_kepek = st.file_uploader(
            "Fotók készítése (Kamera) vagy kiválasztása", type=["jpg", "jpeg", "png"], 
            accept_multiple_files=True, key=f"kocsi_foto_{idx}_{st.session_state.file_uploader_keys[idx]}"
        )
        
        if feltoltott_kepek:
            mentett_kepek = []
            for egy_kep in feltoltott_kepek:
                try:
                    img = Image.open(egy_kep)
                    img = ImageOps.exif_transpose(img)
                    mentett_kepek.append(img)
                except Exception as e:
                    st.error(f"Kép hiba: {e}")
            st.session_state.hibas_kocsik[idx]["kepek"] = mentett_kepek
        else:
            st.session_state.hibas_kocsik[idx]["kepek"] = []
                
        if st.session_state.hibas_kocsik[idx]["kepek"]:
            grid_cols = st.columns(4)
            for f_idx, img_obj in enumerate(st.session_state.hibas_kocsik[idx]["kepek"]):
                with grid_cols[f_idx % 4]: st.image(img_obj, use_container_width=True)

c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 2])
with c_btn1:
    if st.button("➕ Új kocsi hozzáadása", use_container_width=True):
        st.session_state.hibas_kocsik.append({"kocsiszam": "", "leiras": "", "kepek": []})
        st.rerun()
with c_btn2:
    if len(st.session_state.hibas_kocsik) > 0:
        if st.button("➖ Utolsó kocsi törlése", use_container_width=True):
            st.session_state.hibas_kocsik.pop()
            st.rerun()

st.markdown("---")
btn_col1, btn_col2 = st.columns([2, 1])
with btn_col1: generate_pdf = st.button("📄 PDF Jelentés Elkészítése", type="primary")
with btn_col2: st.button("🗑️ Adatok törlése", type="secondary", on_click=adatok_torlese_callback)

# --- PDF GENERÁLÁS ---
if generate_pdf:
    felhasznalonev = st.session_state.felhasznalonev
    szolg_hely = st.session_state.szolg_hely
    vonatszam = st.session_state.vonatszam
    vaganyszam = st.session_state.vaganyszam

    if not felhasznalonev or not szolg_hely or not vonatszam or (muvelet_csoport == "Vonatvizsgálati és RID feladatok" and not opciok):
        st.error("Hiba: Felhasználónév, Szolgálati hely, Vonatszám és legalább egy feladat megadása kötelező!")
    else:
        with st.spinner("PDF dokumentum összeállítása..."):
            try:
                pontos_lezarasi_ido = aktualis_budapesti_ido()
                
                pdf = FPDF()
                pdf.add_page()
                font_name = 'Helvetica'
                
                cim_szoveg = "GYSEV JEGYZOKONYV"
                pdf.set_font(font_name, "B", 16)
                pdf.cell(0, 10, cim_szoveg, ln=True, align="C")
                pdf.ln(10)
                
                pdf.set_font(font_name, "", 12)
                pdf.cell(0, 8, f"{biztonsagos_szoveg('Kocsivizsgalo')}: {biztonsagos_szoveg(felhasznalonev)}", ln=True)
                pdf.cell(0, 8, f"{biztonsagos_szoveg('Szolgalati hely')}: {biztonsagos_szoveg(szolg_hely)}", ln=True)
                pdf.cell(0, 8, f"Vonatszam: {biztonsagos_szoveg(vonatszam)}", ln=True)
                pdf.cell(0, 8, f"Vaganyszam: {biztonsagos_szoveg(vaganyszam)}", ln=True)
                pdf.cell(0, 8, f"{biztonsagos_szoveg('Muvelet(ek)')}: {biztonsagos_szoveg(muvelet_nev_kombinalt)}", ln=True)
                pdf.cell(0, 8, f"Idopont (Lezaras): {pontos_lezarasi_ido}", ln=True)
                pdf.ln(8)
                
                pdf.set_font(font_name, "B", 12)
                pdf.cell(0, 8, biztonsagos_szoveg("VIZSGALAT EREDMENYE(I):"), ln=True)
                pdf.set_font(font_name, "", 12)
                for stat in kivalasztott_statuszok:
                    pdf.cell(0, 8, f"- {biztonsagos_szoveg(stat)}", ln=True)
                pdf.ln(5)
                
                if st.session_state.hibas_kocsik:
                    pdf.set_font(font_name, "B", 14)
                    pdf.cell(0, 10, f"{biztonsagos_szoveg('ERINTETT KOCSIK ES ESZREVETELEK')}:", ln=True)
                    pdf.ln(2)
                    
                    for idx, kocsi in enumerate(st.session_state.hibas_kocsik):
                        pdf.set_font(font_name, "B", 12)
                        kocsi_fejlec = f"{idx + 1}. Kocsiszam: {biztonsagos_szoveg(kocsi['kocsiszam']) if kocsi['kocsiszam'] else 'Nincs megadva'}"
                        pdf.cell(0, 8, kocsi_fejlec, ln=True)
                        
                        pdf.set_font(font_name, "", 11)
                        pdf.cell(0, 6, f"{biztonsagos_szoveg('Reszletek / Leiras')}:", ln=True)
                        pdf.set_font(font_name, "I", 11)
                        pdf.multi_cell(0, 6, biztonsagos_szoveg(kocsi["leiras"]) if kocsi["leiras"] else "Nincs kulon leiras megadva.")
                        pdf.ln(4)
                        
                        # --- HELYTAKARÉKOS RÁCSOS KÉPELRENDEZÉS A PDF-BEN ---
                        if kocsi["kepek"]:
                            pdf.set_font(font_name, "B", 10)
                            pdf.cell(0, 6, f"Csatolt fotok ({len(kocsi['kepek'])} db):", ln=True)
                            pdf.ln(2)
                            
                            kep_szelesseg = 90  # Max szélesség (2 kép egymás mellett)
                            kepek_szama = len(kocsi["kepek"])
                            max_magassag_sorban = 0
                            sor_y = pdf.get_y()
                            
                            for f_idx, img_obj in enumerate(kocsi["kepek"]):
                                current_img = img_obj
                                if current_img.mode in ("RGBA", "P"):
                                    current_img = current_img.convert("RGB")
                                
                                img_w, img_h = current_img.size
                                arany = img_h / img_w
                                szamitott_magassag = kep_szelesseg * arany
                                aktualis_szelesseg = kep_szelesseg
                                
                                # Álló képek magasság-korlátozása (Max 90 mm)
                                if szamitott_magassag > 90:
                                    szamitott_magassag = 90
                                    aktualis_szelesseg = szamitott_magassag / arany
                                    
                                if sor_y + szamitott_magassag > 270:
                                    pdf.add_page()
                                    sor_y = pdf.get_y()
                                    max_magassag_sorban = 0
                                
                                # X koordináta számítás (páros balra, páratlan jobbra)
                                x_poz = 10 if (f_idx % 2 == 0) else 110
                                
                                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                                    current_img.save(tmp_file, format="JPEG", quality=85)
                                    tmp_img_path = tmp_file.name
                                
                                pdf.image(tmp_img_path, x=x_poz, y=sor_y, w=aktualis_szelesseg)
                                os.unlink(tmp_img_path)
                                
                                if szamitott_magassag > max_magassag_sorban:
                                    max_magassag_sorban = szamitott_magassag
                                
                                # Sorvége vagy legutolsó kép esetén ugrás a következő sorra
                                if f_idx % 2 != 0 or f_idx == kepek_szama - 1:
                                    pdf.set_y(sor_y + max_magassag_sorban + 5)
                                    sor_y = pdf.get_y()
                                    max_magassag_sorban = 0
                            
                            pdf.ln(2)
                        
                        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                        pdf.ln(5)
                else:
                    pdf.set_font(font_name, "I", 12)
                    pdf.cell(0, 10, f"{biztonsagos_szoveg('Kulon listazando hiba vagy rendellenesseg nem lett rogzitve.')}", ln=True)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf_file:
                    pdf.output(tmp_pdf_file.name)
                    tmp_pdf_path = tmp_pdf_file.name
                
                with open(tmp_pdf_path, "rb") as f:
                    st.session_state.pdf_data = f.read()
                os.unlink(tmp_pdf_path)
                
                st.session_state.vonatszam_mentett = vonatszam
                st.session_state.show_email_dialog = True
                st.success("🎉 A jelentés sikeresen elkészült!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Hiba történt a PDF generálása közben: {e}")

if st.session_state.show_email_dialog and st.session_state.pdf_data is not None:
    email_kuldes_dialog(muvelet_nev_kombinalt, kivalasztott_statuszok)

if st.session_state.pdf_data is not None and not st.session_state.show_email_dialog:
    st.markdown("### 📄 Elkészült jelentés")
    st.download_button("📥 PDF Fájl Letöltése újra", data=st.session_state.pdf_data, file_name=f"Kocsivizsgalo_Jelentes_{st.session_state.vonatszam_mentett}.pdf", mime="application/pdf")
