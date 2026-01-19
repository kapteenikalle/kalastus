import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import os

# --- ASETUKSET ---
API_KEY = "78c13424469d15c398ab8fa8c832df15"
TIEDOSTO = "kalasaaliit.csv"

def muunna_suunta(asteet):
    suunnat = ["Pohjoinen", "Koillinen", "Itä", "Kaakko", "Etelä", "Lounas", "Länsi", "Luode"]
    indeksi = int((asteet + 22.5) // 45) % 8
    return suunnat[indeksi]

def hae_saa(kaupunki):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={kaupunki}&appid={API_KEY}&units=metric&lang=fi"
    try:
        vastaus = requests.get(url).json()
        if vasta_koodi := vastaus.get("main"):
            tuuli_asteet = vastaus["wind"].get("deg", 0)
            return {
                "Lämpötila": vasta_koodi["temp"],
                "Paine": vasta_koodi["pressure"],
                "Sää": vastaus["weather"][0]["description"],
                "Tuuli_ms": vastaus["wind"].get("speed", 0),
                "Tuuli_suunta": muunna_suunta(tuuli_asteet)
            }
    except:
        return None
    return None

# --- VERKKOSIVUN KÄYTTÖLIITTYMÄ ---
st.set_page_config(page_title="Kalapäiväkirja", page_icon="🎣")
st.title("🎣 Digitaalinen Kalapäiväkirja")

with st.form("kalalomake", clear_on_submit=True):
    laji = st.text_input("Kalan laji")
    paikka = st.text_input("Paikkakunta (esim. Tampere)")
    paino = st.number_input("Paino (g)", min_value=0, step=10)
    nappi = st.form_submit_button("Tallenna saalis")

if nappi:
    if not laji or not paikka:
        st.warning("Täytä vähintään laji ja paikka!")
    else:
        saatiedot = hae_saa(paikka)
        
        if saatiedot:
            nyt = datetime.now()
            uusi_rivi = {
                "Päivämäärä": nyt.strftime("%d.%m.%Y"),  # Esim. 19.01.2024
                "Kello": nyt.strftime("%H:%M"),         # Esim. 14:30
                "Laji": laji,
                "Paikka": paikka,
                "Paino_g": paino,
                "Lämpötila_C": saatiedot["Lämpötila"],
                "Ilmanpaine_hPa": saatiedot["Paine"],
                "Sääkuvaus": saatiedot["Sää"],
                "Tuuli_ms": saatiedot["Tuuli_ms"],
                "Tuulensuunta": saatiedot["Tuuli_suunta"]
            }
            
            df_uusi = pd.DataFrame([uusi_rivi])
            tiedosto_olemassa = os.path.exists(TIEDOSTO)
            
            # Tallennus puolipisteellä ja UTF-8-SIG (Excel-yhteensopiva)
            df_uusi.to_csv(TIEDOSTO, mode='a', index=False, sep=';', 
                           header=not tiedosto_olemassa, encoding='utf-8-sig')
            
            st.success(f"Tallennettu! Päivä: {uusi_rivi['Päivämäärä']}, Kello: {uusi_rivi['Kello']}")
        else:
            st.error("Säätietojen haku epäonnistui.")

# Näytetään viimeisimmät saaliit
if os.path.exists(TIEDOSTO):
    st.divider()
    st.subheader("Viimeisimmät merkinnät")
    data = pd.read_csv(TIEDOSTO, sep=';', encoding='utf-8-sig')
    st.dataframe(data.tail(10), use_container_width=True)