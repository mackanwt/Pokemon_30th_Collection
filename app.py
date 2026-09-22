import streamlit as st
import pandas as pd
import json
import os
import requests

# Konfigurera Streamlit-sidan
st.set_page_config(
    page_title="Pokémon 30th Anniversary Collection",
    page_icon="⚡",
    layout="wide"
)

# Filnamn för JSON-databasen
JSON_FILE = "pokemon_30th_anniversary.json"

# Funktion för att hämta dagsaktuell EUR/SEK växelkurs
@st.cache_data(ttl=3600)  # Cachar kursen i 1 timme
def get_eur_to_sek_rate():
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data.get("result") == "success":
            return float(data["rates"]["SEK"])
    except Exception:
        pass
    return 11.30  # Standard reservkurs om nätverksanropet misslyckas

# Hämta dagens växelkurs
eur_to_sek = get_eur_to_sek_rate()

@st.cache_data
def load_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            df = pd.DataFrame(data)
            return df
    else:
        st.error(f"Kunde inte hitta filen '{JSON_FILE}'. Se till att den ligger i samma mapp.")
        return pd.DataFrame()

# Läs in data
df = load_data()

if not df.empty:
    # Säkerställ förväntade kolumner
    expected_cols = {
        "Äger": False,
        "Namn": "",
        "Setnr.": "",
        "Sällsynthet": "Common",
        "Köpt för (EUR)": 0.0,
        "Värde (EUR)": 0.0,
        "Google Sök": "",
        "_id": "",
        "Bild": ""
    }
    for col, default_val in expected_cols.items():
        if col not in df.columns:
            df[col] = default_val

    # Beräkna SEK-kolumner baserat på växelkursen
    df["Köpt för (SEK)"] = df["Köpt för (EUR)"] * eur_to_sek
    df["Värde (SEK)"] = df["Värde (EUR)"] * eur_to_sek

    st.title("⚡ Pokémon 30th Anniversary Collection")
    st.caption(f"Dagsaktuell växelkurs: 1 EUR = {eur_to_sek:.2f} SEK")

    # Räkna ut statistik (endast för ägda kort)
    total_cards = len(df)
    owned_cards = int(df["Äger"].sum())
    pct_owned = (owned_cards / total_cards * 100) if total_cards > 0 else 0.0

    owned_df = df[df["Äger"] == True]
    
    total_value_eur = owned_df["Värde (EUR)"].sum()
    total_cost_eur = owned_df["Köpt för (EUR)"].sum()
    profit_loss_eur = total_value_eur - total_cost_eur

    total_value_sek = total_value_eur * eur_to_sek
    total_cost_sek = total_cost_eur * eur_to_sek
    profit_loss_sek = profit_loss_eur * eur_to_sek

    # Topp-mätare
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Samlade Kort", f"{owned_cards} / {total_cards}", delta=f"{pct_owned:.1f}%")
    c2.metric("Totalt Värde", f"€{total_value_eur:.2f}", f"{total_value_sek:.0f} kr")
    c3.metric("Totalt Köppris", f"€{total_cost_eur:.2f}", f"{total_cost_sek:.0f} kr")
    c4.metric("Vinst/Förlust", f"€{profit_loss_eur:.2f}", f"{profit_loss_sek:.0f} kr")

    st.divider()

    # Filter & Sortering
    col_filter, col_sort = st.columns([2, 2])
    with col_filter:
        rarities = ["Alla"] + list(df["Sällsynthet"].unique())
        selected_rarity = st.selectbox("Filtrera på Sällsynthet:", rarities)
    
    with col_sort:
        sort_option = st.selectbox(
            "Sortering:", 
            ["Standard (Set-ordning)", "Namn (A-Ö)", "Äger först", "Högst värde (EUR)", "Högst värde (SEK)"]
        )

    # Filtrera data
    filtered_df = df.copy()
    if selected_rarity != "Alla":
        filtered_df = filtered_df[filtered_df["Sällsynthet"] == selected_rarity]

    # Sortera data
    if sort_option == "Namn (A-Ö)":
        filtered_df = filtered_df.sort_values(by="Namn")
    elif sort_option == "Äger först":
        filtered_df = filtered_df.sort_values(by="Äger", ascending=False)
    elif sort_option in ["Högst värde (EUR)", "Högst värde (SEK)"]:
        filtered_df = filtered_df.sort_values(by="Värde (EUR)", ascending=False)

    # Tabell
    st.subheader("Kortlista")
    
    display_cols = [
        "Äger", "Namn", "Setnr.", "Sällsynthet", 
        "Köpt för (EUR)", "Köpt för (SEK)", 
        "Värde (EUR)", "Värde (SEK)", 
        "Google Sök"
    ]

    edited_df = st.data_editor(
        filtered_df[display_cols],
        column_config={
            "Äger": st.column_config.CheckboxColumn("Äger", help="Bocka i om du äger kortet"),
            "Google Sök": st.column_config.LinkColumn("Google Sök", display_text="Cardmarket"),
            "Köpt för (EUR)": st.column_config.NumberColumn("Köpt för (€)", format="€%.2f"),
            "Köpt för (SEK)": st.column_config.NumberColumn("Köpt för (kr)", format="%.2f kr"),
            "Värde (EUR)": st.column_config.NumberColumn("Värde (€)", format="€%.2f"),
            "Värde (SEK)": st.column_config.NumberColumn("Värde (kr)", format="%.2f kr"),
        },
        disabled=["Namn", "Setnr.", "Sällsynthet", "Köpt för (SEK)", "Värde (SEK)", "Google Sök"],
        hide_index=True,
        use_container_width=True
    )

    # Bildvisare för valt kort
    st.divider()
    st.subheader("🖼️ Bildvisning")
    
    selected_card_id = st.selectbox(
        "Välj ett kort att visa bild för:", 
        df["_id"].tolist(), 
        format_func=lambda x: f"{x} - {df[df['_id']==x]['Namn'].values[0]}"
    )
    
    card_info = df[df["_id"] == selected_card_id].iloc[0]
    
    local_img_path = f"images/{selected_card_id}.png"
    if os.path.exists(local_img_path):
        st.image(local_img_path, caption=f"{card_info['Namn']} ({card_info['Setnr.']}) - {card_info['Sällsynthet']}", width=280)
    elif card_info["Bild"]:
        st.image(card_info["Bild"], caption=f"{card_info['Namn']} ({card_info['Setnr.']}) - {card_info['Sällsynthet']}", width=280)
    else:
        st.info("Ingen bild hittades i mappen 'images/'.")
