import streamlit as st
from streamlit_gsheets import GSheetsConnection
import requests
import pandas as pd
from datetime import datetime, time

# --- ASETUKSET ---
API_KEY = "78c13424469d15c398ab8fa8c832df15"

try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
except:
    SHEET_URL = "https://docs.google.com/spreadsheets/d/14Ri5Ox9gHumxU21yIGyKWXPoc5srXaK7joDcwnUuQ6k/edit?usp=sharing"

st.set_page_config(page_title="Kalapäiväkirja")
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

st.title("🎣 Kalapäiväkirja")

with st.form("kalalomake", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        paikka = st.text_input("Paikkakunta")
        lajivaihtoehdot = ["Ahven", "Hauki", "Kuha", "Siika", "Ei saalista (MP)", "Muu"]
        laji = st.selectbox("Pääasiallinen laji", lajivaihtoehdot)
        pvm = st.date_input("Päivämäärä", datetime.now())
    
    with col2:
        alku = st.time_input("Reissu alkoi")
        loppu = st.time_input("Reissu loppui")
        syonti = st.time_input("Paras syöntiaika")
        
        st.divider()
        kpl = st.number_input("Kalojen lukumäärä (kpl)", min_value=0, step=1, value=1)
        paino = st.number_input("Suurimman paino (g)", min_value=0, step=10)
    
    huomio = st.text_area("Lisatiedot (vieheet, keli, havainnot)")
    nappi = st.form_submit_button("Tallenna")

if nappi:
    if paikka:
        t1 = datetime.combine(pvm, alku)
        t2 = datetime.combine(pvm, loppu)
        kesto = (t2 - t1).total_seconds() / 3600
        
        if kesto < 0:
            st.error("Lopetusaika on ennen aloitusaikaa!")
        else:
            with st.spinner('Tallennetaan...'):
                s = hae_saa(paikka)
                if s:
                    # TÄRKEÄÄ: Sanakirjan avaimet on oltava TÄSMÄLLEEN samat kuin Sheetsissä
                    uusi_rivi = pd.DataFrame([{
                        "Pvm": pvm.strftime("%d.%m.%Y"),
                        "Aloitusaika": alku.strftime("%H:%M"),
                        "Lopetusaika": loppu.strftime("%H:%M"),
                        "Kesto_h": round(kesto, 1),
                        "Syontiaika": syonti.strftime("%H:%M"),
                        "Laji": laji,
                        "Paikka": paikka,
                        "Lukumäärä": kpl,
                        "Suurin_kala_g": paino,
                        "Lampotila": s["temp"],
                        "Ilmanpaine": s["pres"],
                        "Saa": s["desc"],
                        "Tuuli_ms": s["w_spd"],
                        "Tuulisuunta": muunna_suunta(s["w_deg"]),
                        "Lisatiedot": huomio
                    }])
                    
                    # Luetaan ja päivitetään
                    vanha_data = conn.read(spreadsheet=SHEET_URL, ttl=0)
                    paivitetty_data = pd.concat([vanha_data, uusi_rivi], ignore_index=True)
                    
                    # Pidetään vain halutut sarakkeet oikeassa järjestyksessä
                    sarake_jarjestys = ["Pvm", "Aloitusaika", "Lopetusaika", "Kesto_h", "Syontiaika", "Laji", "Paikka", "Lukumäärä", "Suurin_kala_g", "Lampotila", "Ilmanpaine", "Saa", "Tuuli_ms", "Tuulisuunta", "Lisatiedot"]
                    paivitetty_data = paivitetty_data[sarake_jarjestys]
                    
                    conn.update(spreadsheet=SHEET_URL, data=paivitetty_data)
                    st.success(f"Tallennettu!")
                    st.cache_data.clear()
    else:
        st.warning("Lisää paikkakunta!")

st.divider()
try:
    data = conn.read(spreadsheet=SHEET_URL)
    st.subheader("Viimeisimmät merkinnät")
    st.dataframe(data.tail(10), use_container_width=True)
except:
    st.info("Taulukko on vielä tyhjä.")
