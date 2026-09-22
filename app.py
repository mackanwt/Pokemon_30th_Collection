import streamlit as st
import pandas as pd
import json
import requests
import base64
from typing import Any, Tuple

st.set_page_config(page_title="Pokémon 30th Anniversary Collection", layout="wide")

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]
DATA_FILE_PATH = "pokemon_30th_anniversary.json"

# --- GITHUB-FUNKTIONER ---
def github_load_file(file_path: str, default_data: Any) -> Any:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
    except Exception:
        return default_data
        
    if response.status_code == 200:
        try:
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            if not content.strip():
                return default_data
            return json.loads(content)
        except Exception as e:
            st.error(f"⚠️ JSON-fel i filen **{file_path}**: {e}")
            return default_data
    return default_data

def github_save_file(file_path: str, content: Any, commit_message: str) -> Tuple[bool, str]:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    sha = None
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            sha = response.json()['sha']
    except Exception:
        pass
        
    encoded_content = base64.b64encode(json.dumps(content, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
    data = {"message": commit_message, "content": encoded_content}
    if sha:
        data["sha"] = sha
        
    try:
        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Sparat"
        return False, response.text
    except Exception as e:
        return False, str(e)

# --- VÄXELKURS ---
@st.cache_data(ttl=3600)
def get_eur_sek_rate():
    try:
        response = requests.get("https://open.er-api.com/v6/latest/EUR")
        data = response.json()
        return float(data["rates"]["SEK"])
    except Exception:
        return 11.28

exchange_rate = get_eur_sek_rate()

# --- LADDA DATA ---
if "cards_data" not in st.session_state:
    st.session_state.cards_data = github_load_file(DATA_FILE_PATH, [])

# Layout med rubrik och växelkurs
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

df = pd.DataFrame(st.session_state.cards_data)

if not df.empty:
    for col in ["Äger", "Köpt för (EUR)", "Värde (EUR)"]:
        if col not in df.columns:
            df[col] = False if col == "Äger" else 0.0

    # Ta bort "Skick" och "Egen Cardmarket Länk" om de finns i datan
    cols_to_drop = [c for c in ["Skick", "Egen Cardmarket Länk", "Egen Länk"] if c in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    df["Köpt för (SEK)"] = (pd.to_numeric(df["Köpt för (EUR)"], errors='coerce').fillna(0.0) * exchange_rate).round(2)
    df["Värde (SEK)"] = (pd.to_numeric(df["Värde (EUR)"], errors='coerce').fillna(0.0) * exchange_rate).round(2)

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
            "Köpt för (SEK)": st.column_config.NumberColumn("Köpt för (SEK)", format="%.2f kr", disabled=True),
            "Värde (EUR)": st.column_config.NumberColumn("Värde (EUR)", format="%.2f €"),
            "Värde (SEK)": st.column_config.NumberColumn("Värde (SEK)", format="%.2f kr", disabled=True),
            "Google Sök": st.column_config.LinkColumn("Cardmarket / Sök", display_text="🔍 Sök på Cardmarket"),
        },
        disabled=["Namn", "Setnr.", "Symbol", "Sällsynthet", "Köpt för (SEK)", "Värde (SEK)", "Google Sök"],
        hide_index=True,
        use_container_width=True,
        key="editor"
    )

    if st.button("💾 Spara ändringar till GitHub", type="primary"):
        updated_data = []
        for i, row in edited_df.iterrows():
            row_dict = row.to_dict()
            # Koppla tillbaka originalets _id
            if i < len(st.session_state.cards_data):
                row_dict["_id"] = st.session_state.cards_data[i].get("_id", f"card_{i}")
            else:
                row_dict["_id"] = f"card_custom_{i}"
            
            # Rensar bort eventuella kvarvarande fält för Skick och Egen Länk
            row_dict.pop("Skick", None)
            row_dict.pop("Egen Cardmarket Länk", None)
            row_dict.pop("Egen Länk", None)

            # Räkna om SEK
            k_eur = float(row_dict.get("Köpt för (EUR)", 0.0) or 0.0)
            v_eur = float(row_dict.get("Värde (EUR)", 0.0) or 0.0)
            row_dict["Köpt för (SEK)"] = round(k_eur * exchange_rate, 2)
            row_dict["Värde (SEK)"] = round(v_eur * exchange_rate, 2)
            
            updated_data.append(row_dict)

        # Spara via GitHub API
        success, msg = github_save_file(DATA_FILE_PATH, updated_data, "Uppdaterade 30th Anniversary samling")

        if success:
            st.session_state["cards_data"] = updated_data
            st.success("Ändringarna sparades direkt till GitHub!")
            st.rerun()
        else:
            st.error(f"Kunde inte spara till GitHub: {msg}")

    # Sammanfattning längst ned
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)

    total_owned = edited_df["Äger"].sum()
    total_bought_eur = edited_df[edited_df["Äger"]]["Köpt för (EUR)"].sum()
    total_val_eur = edited_df[edited_df["Äger"]]["Värde (EUR)"].sum()
    total_bought_sek = edited_df[edited_df["Äger"]]["Köpt för (SEK)"].sum()
    total_val_sek = edited_df[edited_df["Äger"]]["Värde (SEK)"].sum()

    c1.metric("Kort Ägda", f"{total_owned} / {len(edited_df)}")
    c2.metric("Totalt Köpt", f"{total_bought_eur:.2f} €", f"{total_bought_sek:.2f} SEK")
    c3.metric("Totalt Värde", f"{total_val_eur:.2f} €", f"{total_val_sek:.2f} SEK")
    c4.metric("Vinst / Förlust", f"{(total_val_eur - total_bought_eur):.2f} €", f"{(total_val_sek - total_bought_sek):.2f} SEK")
else:
    st.info("Ingen data hittades.")
