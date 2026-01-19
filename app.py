import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime

# --- ASETUKSET ---
API_KEY = "78c13424469d15c398ab8fa8c832df15"
# LIITÄ TÄHÄN GOOGLE SHEETS -LINKKISI:
SHEET_URL = "https://docs.google.com/spreadsheets/d/14Ri5Ox9gHumxU21yIGyKWXPoc5srXaK7joDcwnUuQ6k/edit?usp=sharing"

st.set_page_config(page_title="Pilvi-Kalapäiväkirja", page_icon="🎣")

# Yhdistetään Google Sheetsiin
conn = st.connection("gsheets", type=GSheetsConnection)

def muunna_suunta(asteet):
    suunnat = ["Pohjoinen", "Koillinen", "Itä", "Kaakko", "Etelä", "Lounas", "Länsi", "Luode"]
    return suunnat[int((asteet + 22.5) // 45) % 8]

def hae_saa(kaupunki):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={kaupunki}&appid={API_KEY}&units=metric&lang=fi"
    try:
        r = requests.get(url).json()
        return {
            "temp": r["main"]["temp"],
            "pres": r["main"]["pressure"],
            "desc": r["weather"][0]["description"],
            "w_spd": r["wind"]["speed"],
            "w_deg": r["wind"]["deg"]
        }
    except: return None

st.title("🎣 Pilvi-Kalapäiväkirja")
st.info("Tiedot tallentuvat yhteiseen Google Sheetsiin.")

with st.form("kalalomake", clear_on_submit=True):
    lajivaihtoehdot = ["Ahven", "Hauki", "Kuha", "Siika","Muu"]
    
    laji = st.selectbox("Valitse kalalaji", lajivaihtoehdot)
    paikka = st.text_input("Paikkakunta")
    paino = st.number_input("Paino (g)", min_value=0)
    nappi = st.form_submit_button("Tallenna saalis pilveen")

if nappi:
    if laji and paikka:
        s = hae_saa(paikka)
        if s:
            # Luodaan uusi rivi
            uusi_rivi = pd.DataFrame([{
                "Pvm": datetime.now().strftime("%d.%m.%Y"),
                "Kello": datetime.now().strftime("%H:%M"),
                "Laji": laji,
                "Paikka": paikka,
                "Paino": paino,
                "Lampotila": s["temp"],
                "Paine": s["pres"],
                "Saa": s["desc"],
                "Tuuli_ms": s["w_spd"],
                "Tuulisuunta": muunna_suunta(s["w_deg"])
            }])
            
            # Luetaan vanhat ja lisätään uusi
            vanha_data = conn.read(spreadsheet=SHEET_URL)
            paivitetty_data = pd.concat([vanha_data, uusi_rivi], ignore_index=True)
            
            # Päivitetään Sheets
            conn.update(spreadsheet=SHEET_URL, data=paivitetty_data)
            st.success(f"Saalis tallennettu pilveen! Sää: {s['temp']}°C")
            st.cache_data.clear() # Tyhjennetään välimuisti, jotta uusi rivi näkyy heti
        else:
            st.error("Säätietojen haku epäonnistui.")

# Näytetään data Sheetsistä
st.divider()
try:
    data = conn.read(spreadsheet=SHEET_URL)
    st.dataframe(data, use_container_width=True)
except:

    st.warning("Taulukko on vielä tyhjä tai linkki on väärä.")
