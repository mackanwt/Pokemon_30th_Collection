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

# Ladda data
@st.cache_data
def load_data():
    with open("pokemon_30th_anniversary.json", "r", encoding="utf-8") as f:
        return json.load(f)

if "cards_data" not in st.session_state:
    st.session_state.cards_data = load_data()

df = pd.DataFrame(st.session_state.cards_data)

# Ta bort _id från kolumnerna som skickas till data_editor för att helt dölja den
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

# Sammanfattning längst ned
st.markdown("---")
c1, c2, c3, c4 = st.columns(4)

total_owned = df["Äger"].sum()
total_bought_eur = df[df["Äger"]]["Köpt för (EUR)"].sum()
total_val_eur = df[df["Äger"]]["Värde (EUR)"].sum()
total_bought_sek = df[df["Äger"]]["Köpt för (SEK)"].sum()
total_val_sek = df[df["Äger"]]["Värde (SEK)"].sum()

c1.metric("Kort Ägda", f"{total_owned} / {len(df)}")
c2.metric("Totalt Köpt för", f"{total_bought_eur:.2f} €", f"{total_bought_sek:.2f} SEK")
c3.metric("Totalt Värde", f"{total_val_eur:.2f} €", f"{total_val_sek:.2f} SEK")
c4.metric("Vinst / Förlust", f"{(total_val_eur - total_bought_eur):.2f} €", f"{(total_val_sek - total_bought_sek):.2f} SEK")
