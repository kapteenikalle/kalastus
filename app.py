import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime, combine

# --- ASETUKSET ---
API_KEY = "78c13424469d15c398ab8fa8c832df15"
# GOOGLE SHEETS -LINKKI:
SHEET_URL = "https://docs.google.com/spreadsheets/d/14Ri5Ox9gHumxU21yIGyKWXPoc5srXaK7joDcwnUuQ6k/edit?usp=sharing"

st.set_page_config(page_title="Kalapäiväkirja", page_icon="🎣")

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

st.title("Kalapäiväkirja")

with st.form("kalalomake", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        paikka = st.text_input("Paikkakunta")
        lajivaihtoehdot = ["Ahven", "Hauki", "Kuha", "Siika", "Ei saalista", "Muu"]
        laji = st.selectbox("Pääasiallinen laji", lajivaihtoehdot)
    
    with col2:
        # Aloitus- ja lopetusajat
        alku = st.time_input("Reissu alkoi", datetime.now().replace(hour=8, minute=0).time())
        loppu = st.time_input("Reissu loppui", datetime.now().time())
        kpl = st.number_input("Kalojen lukumäärä (kpl)", min_value=0, step=1, value=1)
        paino = st.number_input("Suurimman kalan paino (g)", min_value=0, step=10)
    
    huomio = st.text_area("Lisatiedot (Viehe, syvyys)")
    
    nappi = st.form_submit_button("Tallenna reissu")

if nappi:
    if laji and paikka:
        # Lasketaan kesto tunteina
        t1 = combine(pvm, alku)
        t2 = combine(pvm, loppu)
        kesto = (t2 - t1).total_seconds() / 3600
        
        if kesto < 0:
            st.error("Lopetusaika ei voi olla ennen aloitusaikaa!")
        else:
            with st.spinner('Haetaan säätietoja ja tallennetaan...'):
                s = hae_saa(paikka)
                if s:
                    # Luodaan uusi rivi
                    uusi_rivi = pd.DataFrame([{
                        "Pvm": datetime.now().strftime("%d.%m.%Y"),
                        "Kello": datetime.now().strftime("%H:%M"),
                        "Laji": laji,
                        "Paikka": paikka,
                        "Lukumäärä": kpl,
                        "Suurin_kala_g": paino,
                        "Lampotila": s["temp"],
                        "Ilmanpaine": s["pres"],
                        "Saa": s["desc"],
                        "Tuuli_ms": s["w_spd"],
                        "Tuulisuunta": muunna_suunta(s["w_deg"]),
                        "Lisätiedot": huomio
                    }])
        
            
                    # Luetaan vanhat ja lisätään uusi
                    vanha_data = conn.read(spreadsheet=SHEET_URL)
                    paivitetty_data = pd.concat([vanha_data, uusi_rivi], ignore_index=True)
            
                    # Päivitetään Sheets
                    conn.update(spreadsheet=SHEET_URL, data=paivitetty_data)
                    st.success(f"Reissu tallennettu. Sää: {s['temp']}°C")
                    st.cache_data.clear() # Tyhjennetään välimuisti, jotta uusi rivi näkyy heti
                else:
                    st.error("Säätietojen haku epäonnistui.")
    else:
        st.warning("Syötä paikkakunta ennen tallennusta!")

# Näytetään data Sheetsistä
st.divider()
try:
    data = conn.read(spreadsheet=SHEET_URL)
    st.dataframe(data, use_container_width=True)
except:

    st.warning("Taulukko on vielä tyhjä tai linkki on väärä.")
