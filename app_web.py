import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageOps
import io
import datetime

# 1. OLDAL BEÁLLÍTÁSAI
st.set_page_config(
    page_title="GYSEV Kocsivizsgáló Hiba-App", 
    page_icon="🚂", 
    layout="centered"
)

# Egy kis egyedi stílus a felületnek, hogy jól látható legyen a vágányok között is
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .stButton>button { width: 100%; background-color: #005A9C; color: white; height: 3em; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

st.title("🚂 GYSEV Műszaki Kocsivizsgálat")
st.write("Azonnali hibarögzítés és hivatalos PDF dokumentum generálás.")

# --- 2. ADATBEVITEL ---
st.subheader("Hiba Részletei")

# Kocsiszám: Automatikusan nagybetűssé teszi és kiszűri a felesleges szóközöket
kocsiszam_raw = st.text_input("Kocsiszám (12 jegyű):", max_chars=12, placeholder="pl. 315553730012")
kocsiszam = kocsiszam_raw.strip().upper()

# Hiba leírása text_area
hiba_leiras = st.text_area("Észlelt hiba pontos leírása:", placeholder="pl. Sátortető repedés, fékberendezés hiba, stb...")

# --- 3. INTELLIGENS FOTÓ GOMB (KAMERA + GALÉRIA) ---
st.subheader("Fénykép csatolása")
st.info("Mobilon a gomb megnyitja a Kamerát (azonnali fotó) vagy a Galériát (feltöltés).")

feltoltott_kep = st.file_uploader(
    "Kattints a fotózáshoz vagy a kép kiválasztásához", 
    type=["jpg", "jpeg", "png"]
)

# Kép előnézet és feldolgozás
feldolgozott_kep_buffer = None
if feltoltott_kep is not None:
    try:
        # Beolvassuk a képet
        img = Image.open(feltoltott_kep)
        
        # MOBILOS JAVÍTÁS: Az Android/iOS telefonok elmentik a kép irányát (EXIF), 
        # de a PDF-be téve a kép sokszor elfordulna. Ez a sor kényszeríti a helyes álló/fekvő helyzetet.
        img = ImageOps.exif_transpose(img)
        
        # Megjelenítjük a kocsivizsgálónak ellenőrzésre
        st.image(img, caption="Csatolt fénykép", use_container_width=True)
        
        # Előkészítjük a képet a PDF-hez (méretarányos kicsinyítés, hogy ne legyen 10 MB a PDF)
        max_width = 450
        w_percent = (max_width / float(img.size[0]))
        h_size = int((float(img.size[1]) * float(w_percent)))
        
        # Konvertáljuk RGB-be (PNG esetén a transzparencia összeomlást okozhat a ReportLab-ben)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=80)
        img_byte_arr.seek(0)
        
        # Ezt a tiszta adatot fogja megkapni a PDF generátor
        feldolgozott_kep_buffer = img_byte_arr
        img_height_pdf = h_size
        
    except Exception as e:
        st.error(f"Nem sikerült a képet feldolgozni: {e}")

# --- 4. PDF GENERÁLÁSI LOGIKA ---
st.subheader("Dokumentum mentése")

if st.button("PDF MŰSZAKI JELENTÉS ELKÉSZÍTÉSE"):
    if not kocsiszam:
        st.error("⚠️ Hiányzik a kocsiszám!")
    elif len(kocsiszam) < 12:
        st.warning("⚠️ Figyelem: A megadott kocsiszám rövidebb mint 12 jegyű!")
    elif not hiba_leiras:
        st.error("⚠️ Nem adtad meg a hiba leírását!")
    else:
        try:
            # Memóriában dolgozunk, nem hozunk létre szemetet a szerver meghajtóján
            pdf_buffer = io.BytesIO()
            
            # Margók beállítása (A4-es méretre szabva)
            doc = SimpleDocTemplate(
                pdf_buffer, 
                pagesize=letter,
                rightMargin=45, leftMargin=45, topMargin=45, bottomMargin=45
            )
            
            styles = getSampleStyleSheet()
            
            # Egyedi, tiszta stílusok magyar ékezet-barát betűtípusokkal (Helvetica)
            cim_style = ParagraphStyle(
                'GysevCim',
                parent=styles['Heading1'],
                fontName='Helvetica-Bold',
                fontSize=22,
                leading=26,
                textColor=colors.HexColor('#005A9C'),
                spaceAfter=15
            )
            
            cimke_style = ParagraphStyle(
                'GysevCimke',
                parent=styles['Normal'],
                fontName='Helvetica-Bold',
                fontSize=12,
                leading=16,
                textColor=colors.HexColor('#333333')
            )
            
            adat_style = ParagraphStyle(
                'GysevAdat',
                parent=styles['Normal'],
                fontName='Helvetica',
                fontSize=12,
                leading=16,
                textColor=colors.HexColor('#000000'),
                spaceAfter=10
            )

            story = []
            
            # Dokumentum Fejléc
            story.append(Paragraph("MŰSZAKI KOCSIVIZSGÁLATI HIBAJELENTÉS", cim_style))
            
            # Dátum automatikus rögzítése
            aktualis_ido = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            story.append(Paragraph(f"<b>Rögzítés ideje:</b> {aktualis_ido}", adat_style))
            story.append(Spacer(1, 15))
            
            # Adatok beírása
            story.append(Paragraph("Kocsiszám:", cimke_style))
            story.append(Paragraph(kocsiszam, adat_style))
            
            story.append(Paragraph("Észlelt hiba leírása:", cimke_style))
            # Biztonságos sortörés kezelés a PDF szövegben
            biztonsagos_leiras = hiba_leiras.replace('\n', '<br/>')
            story.append(Paragraph(biztonsagos_leiras, adat_style))
            story.append(Spacer(1, 15))
            
            # Fotó beágyazása, ha létezik
            if feldolgozott_kep_buffer is not None:
                foto_elemek = []
                foto_elemek.append(Paragraph("Mellékelt helyszíni fotó:", cimke_style))
                foto_elemek.append(Spacer(1, 5))
                
                # ReportLab kép objektum generálása a beállított méretekkel
                rl_img = RLImage(feldolgozott_kep_buffer, width=450, height=img_height_pdf)
                foto_elemek.append(rl_img)
                
                # A KeepTogether biztosítja, hogy a kép és a felirata ne szakadjon ketté két külön oldalra
                story.append(KeepTogether(foto_elemek))
            
            # Dokumentum összeállítása
            doc.build(story)
            pdf_buffer.seek(0)
            
            st.success("✅ A PDF jelentés hiba nélkül összeállt!")
            
            # Letöltő gomb
            st.download_button(
                label="📥 PDF LETÖLTÉSE",
                data=pdf_buffer,
                file_name=f"GYSEV_hiba_{kocsiszam}_{datetime.date.today()}.pdf",
                mime="application/pdf"
            )
            
        except Exception as pdf_error:
            st.error(f"Hiba történt a PDF generálása közben: {pdf_error}")
