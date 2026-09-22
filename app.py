import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Pokémon 30th Celebration Collector", layout="wide")

JSON_FILE = "pokemon_30th_anniversary.json"

@st.cache_data
def load_data():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

raw_data = load_data()
df = pd.DataFrame(raw_data)

st.title("⚡ Pokémon 30th Celebration Collection")

if not df.empty:
    # Översikt och statistik
    owned_count = int(df["Äger"].sum())
    total_cards = len(df)
    progress = owned_count / total_cards if total_cards > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Samlade Kort", f"{owned_count} / {total_cards}")
    col2.metric("Framsteg", f"{progress:.1%}")
    col3.metric("Totalt Köpt För", f"{df[df['Äger']]['Köpt för (EUR)'].sum():.2f} €")
    col4.metric("Totalt Värde", f"{df[df['Äger']]['Värde (EUR)'].sum():.2f} €")

    st.progress(progress)
    st.divider()

    # Filtrering
    st.subheader("🔍 Filter & Sortering")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        rarity_filter = st.multiselect(
            "Filtrera på Sällsynthet:",
            options=df["Sällsynthet"].unique().tolist(),
            default=df["Sällsynthet"].unique().tolist()
        )
        
    with filter_col2:
        ownership_filter = st.radio("Visa:", ["Alla", "Bara Ägda", "Bara Saknade"], horizontal=True)

    # Applicera filter
    filtered_df = df[df["Sällsynthet"].isin(rarity_filter)].copy()
    
    if ownership_filter == "Bara Ägda":
        filtered_df = filtered_df[filtered_df["Äger"] == True]
    elif ownership_filter == "Bara Saknade":
        filtered_df = filtered_df[filtered_df["Äger"] == False]

    st.subheader("📋 Kortlista")
    
    edited_df = st.data_editor(
        filtered_df,
        column_config={
            "_id": None,
            "Äger": st.column_config.CheckboxColumn("Äger", default=False),
            "Setnr.": st.column_config.TextColumn("Setnr", disabled=True),
            "Namn": st.column_config.TextColumn("Namn"),
            "Symbol": st.column_config.TextColumn("Rarity Symbol", disabled=True),
            "Sällsynthet": st.column_config.TextColumn("Kategori", disabled=True),
            "Köpt för (EUR)": st.column_config.NumberColumn("Köpt (EUR)", format="%.2f €"),
            "Värde (EUR)": st.column_config.NumberColumn("Värde (EUR)", format="%.2f €"),
            "Google Sök": st.column_config.LinkColumn("Cardmarket / Sök", display_text="Sök Kort")
        },
        disabled=["_id", "Setnr.", "Symbol", "Sällsynthet"],
        hide_index=True,
        use_container_width=True,
        num_rows="fixed"
    )

    if st.button("💾 Spara Ändringar", type="primary"):
        for _, row in edited_df.iterrows():
            card_id = row["_id"]
            idx = next((i for i, item in enumerate(raw_data) if item["_id"] == card_id), None)
            if idx is not None:
                raw_data[idx]["Äger"] = bool(row["Äger"])
                raw_data[idx]["Namn"] = row["Namn"]
                raw_data[idx]["Köpt för (EUR)"] = float(row["Köpt för (EUR)"])
                raw_data[idx]["Värde (EUR)"] = float(row["Värde (EUR)"])

        save_data(raw_data)
        st.success("Dina ändringar har sparats!")
        st.cache_data.clear()
        st.rerun()
else:
    st.error("Kör 'python generate_30th_json.py' i terminalen för att skapa JSON-filen först.")
