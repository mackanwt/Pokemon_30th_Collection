import streamlit as st
import pandas as pd
import json
import requests

st.set_page_config(page_title="Pokémon 30th Anniversary Collection", layout="wide")

# Hämta växelkurs (EUR -> SEK)
@st.cache_data(ttl=3600)
def get_eur_sek_rate():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/EUR")
        data = response.json()
        return float(data["rates"]["SEK"])
    except Exception:
        return 11.28  # Reservvärde

exchange_rate = get_eur_sek_rate()

# Layout med rubrik till vänster och växelkurs snyggt uppe till höger
col_title, col_rate = st.columns([3, 1])

with col_title:
    st.title("🎴 Pokémon 30th Anniversary Collection")

with col_rate:
    st.markdown(
        f"<div style='text-align: right; padding-top: 25px; color: #666; font-size: 14px;'>"
        f"💱 <b>Aktuell växelkurs:</b> 1 EUR = <b>{exchange_rate:.2f} SEK</b>"
        f"</div>",
        unsafe_allow_html=True
    )

# Ladda data från JSON utan cachning så att senaste filen alltid läss in direkt
def load_data():
    try:
        with open("pokemon_30th_anniversary.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

if "cards_data" not in st.session_state:
    st.session_state.cards_data = load_data()

# Om filen på disk har uppdaterats externt (t.ex. vid manuell tillagd rad), läs in den på nytt om längden skiljer sig
disk_data = load_data()
if len(disk_data) != len(st.session_state.cards_data):
    st.session_state.cards_data = disk_data

df = pd.DataFrame(st.session_state.cards_data)

# Ta bort _id från kolumnerna som skickas till data_editor för att dölja den i tabellen
display_columns = [col for col in df.columns if col != "_id"]

edited_df = st.data_editor(
    df[display_columns],
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
    disabled=["Namn", "Setnr.", "Symbol", "Sällsynthet"],
    hide_index=True,
    use_container_width=True,
    key="editor"
)

# Knapp för att spara ändringar permanent direkt till JSON-filen
if st.button("💾 Spara ändringar", type="primary"):
    # Synka ändringarna från editor-statusen till dataframe
    if "editor" in st.session_state and st.session_state.editor.get("edited_rows"):
        edited_rows = st.session_state.editor["edited_rows"]
        for row_idx, changes in edited_rows.items():
            for col_name, new_val in changes.items():
                df.at[int(row_idx), col_name] = new_val
                
                # Automatisk omräkning av SEK/EUR vid behov
                if col_name == "Köpt för (EUR)":
                    df.at[int(row_idx), "Köpt för (SEK)"] = round(float(new_val) * exchange_rate, 2)
                elif col_name == "Köpt för (SEK)":
                    df.at[int(row_idx), "Köpt för (EUR)"] = round(float(new_val) / exchange_rate, 2) if exchange_rate > 0 else 0.0
                elif col_name == "Värde (EUR)":
                    df.at[int(row_idx), "Värde (SEK)"] = round(float(new_val) * exchange_rate, 2)
                elif col_name == "Värde (SEK)":
                    df.at[int(row_idx), "Värde (EUR)"] = round(float(new_val) / exchange_rate, 2) if exchange_rate > 0 else 0.0

    # Behåll ursprungliga _id-värden för varje rad
    updated_data = []
    for i, row in df.iterrows():
        row_dict = row.to_dict()
        if i < len(st.session_state.cards_data):
            row_dict["_id"] = st.session_state.cards_data[i].get("_id", f"card_{i}")
        else:
            row_dict["_id"] = f"card_custom_{i}"
        updated_data.append(row_dict)
        
    st.session_state.cards_data = updated_data

    # SKRIV DIREKT TILL JSON-FILEN PÅ DISKEN
    with open("pokemon_30th_anniversary.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.cards_data, f, ensure_ascii=False, indent=2)

    st.success("Ändringarna har sparats permanent direkt till JSON-filen!")
    st.rerun()

# Sammanfattning längst ned
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)

total_owned = edited_df["Äger"].sum()
total_bought_eur = edited_df[edited_df["Äger"]]["Köpt för (EUR)"].sum()
total_val_eur = edited_df[edited_df["Äger"]]["Värde (EUR)"].sum()
total_bought_sek = edited_df[edited_df["Äger"]]["Köpt för (SEK)"].sum()
total_val_sek = edited_df[edited_df["Äger"]]["Värde (SEK)"].sum()

c1.metric("Kort Ägda", f"{total_owned} / {len(edited_df)}")
c2.metric("Totalt Köpt för", f"{total_bought_eur:.2f} €", f"{total_bought_sek:.2f} SEK")
c3.metric("Totalt Värde", f"{total_val_eur:.2f} €", f"{total_val_sek:.2f} SEK")
c4.metric("Vinst / Förlust", f"{(total_val_eur - total_bought_eur):.2f} €", f"{(total_val_sek - total_bought_sek):.2f} SEK")
