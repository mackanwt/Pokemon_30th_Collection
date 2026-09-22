import streamlit as st
import pandas as pd
import json
import requests

st.set_page_config(page_title="Pokémon 30th Anniversary Collection", layout="wide")

# Funktion för att hämta aktuell växelkurs (EUR -> SEK)
@st.cache_data(ttl=3600)  # Cachar växelkursen i 1 timme
def get_eur_sek_rate():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/EUR")
        data = response.json()
        return float(data["rates"]["SEK"])
    except Exception:
        return 11.5  # Reservvärde om API:et inte skulle svara

exchange_rate = get_eur_sek_rate()

st.title("🎴 Pokémon 30th Anniversary Collection")
st.sidebar.markdown(f"**Aktuell Växelkurs:** 1 EUR = **{exchange_rate:.2f} SEK**")

# Ladda data
@st.cache_data
def load_data():
    with open("pokemon_30th_anniversary.json", "r", encoding="utf-8") as f:
        return json.load(f)

if "cards_data" not in st.session_state:
    st.session_state.cards_data = load_data()

df = pd.DataFrame(st.session_state.cards_data)

# Sortera och förbered vy
edited_df = st.data_editor(
    df,
    column_config={
        "Äger": st.column_config.CheckboxColumn("Äger", default=False),
        "Namn": st.column_config.TextColumn("Namn", disabled=True),
        "Setnr.": st.column_config.TextColumn("Setnr.", disabled=True),
        "Symbol": st.column_config.TextColumn("Symbol", disabled=True),
        "Sällsynthet": st.column_config.TextColumn("Sällsynthet", disabled=True),
        "Köpt för (EUR)": st.column_config.NumberColumn("Köpt för (EUR)", format="%.2f €"),
        "Köpt för (SEK)": st.column_config.NumberColumn("Köpt för (SEK)", format="%.2f kr"),
        "Värde (EUR)": st.column_config.NumberColumn("Värde (EUR)", format="%.2f €"),
        "Värde (SEK)": st.column_config.NumberColumn("Värde (SEK)", format="%.2f kr"),
        "Google Sök": st.column_config.LinkColumn("Cardmarket / Sök", display_text="Sök på Cardmarket"),
    },
    disabled=["_id", "Namn", "Setnr.", "Symbol", "Sällsynthet"],
    hide_index=True,
    use_container_width=True,
    key="editor"
)

# Synkronisera ändringar mellan EUR och SEK
if "editor" in st.session_state and st.session_state.editor.get("edited_rows"):
    edited_rows = st.session_state.editor["edited_rows"]
    updated = False

    for row_idx, changes in edited_rows.items():
        # Om Köpt för (EUR) ändras -> beräkna SEK
        if "Köpt för (EUR)" in changes and "Köpt för (SEK)" not in changes:
            eur_val = float(changes["Köpt för (EUR)"])
            df.at[row_idx, "Köpt för (EUR)"] = eur_val
            df.at[row_idx, "Köpt för (SEK)"] = round(eur_val * exchange_rate, 2)
            updated = True
        
        # Om Köpt för (SEK) ändras -> beräkna EUR
        elif "Köpt för (SEK)" in changes and "Köpt för (EUR)" not in changes:
            sek_val = float(changes["Köpt för (SEK)"])
            df.at[row_idx, "Köpt för (SEK)"] = sek_val
            df.at[row_idx, "Köpt för (EUR)"] = round(sek_val / exchange_rate, 2) if exchange_rate > 0 else 0.0
            updated = True

        # Om Värde (EUR) ändras -> beräkna SEK
        if "Värde (EUR)" in changes and "Värde (SEK)" not in changes:
            eur_val = float(changes["Värde (EUR)"])
            df.at[row_idx, "Värde (EUR)"] = eur_val
            df.at[row_idx, "Värde (SEK)"] = round(eur_val * exchange_rate, 2)
            updated = True

        # Om Värde (SEK) ändras -> beräkna EUR
        elif "Värde (SEK)" in changes and "Värde (EUR)" not in changes:
            sek_val = float(changes["Värde (SEK)"])
            df.at[row_idx, "Värde (SEK)"] = sek_val
            df.at[row_idx, "Värde (EUR)"] = round(sek_val / exchange_rate, 2) if exchange_rate > 0 else 0.0
            updated = True

    if updated:
        st.session_state.cards_data = df.to_dict(orient="records")
        with open("pokemon_30th_anniversary.json", "w", encoding="utf-8") as f:
            json.dump(st.session_state.cards_data, f, ensure_ascii=False, indent=2)
        st.rerun()

# Sammanfattning längst ner
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

total_owned = df["Äger"].sum()
total_bought_eur = df[df["Äger"]]["Köpt för (EUR)"].sum()
total_val_eur = df[df["Äger"]]["Värde (EUR)"].sum()
total_bought_sek = df[df["Äger"]]["Köpt för (SEK)"].sum()
total_val_sek = df[df["Äger"]]["Värde (SEK)"].sum()

col1.metric("Kort Ägda", f"{total_owned} / {len(df)}")
col2.metric("Totalt Köpt för", f"{total_bought_eur:.2f} €", f"{total_bought_sek:.2f} SEK")
col3.metric("Totalt Värde", f"{total_val_eur:.2f} €", f"{total_val_sek:.2f} SEK")
col4.metric("Vinst / Förlust", f"{(total_val_eur - total_bought_eur):.2f} €", f"{(total_val_sek - total_bought_sek):.2f} SEK")
