import streamlit as st
import pandas as pd
import json
import requests
import base64
from typing import Tuple, Any

# --- KONFIGURATION ---
st.set_page_config(page_title="Pokémon 30th Anniversary Collection", layout="wide")

GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "")
DATA_FILE_PATH = "pokemon_30th_anniversary.json"

# --- GITHUB HJÄLPFUNKTIONER ---
def github_load_file(file_path: str, default_data: Any) -> Any:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_data

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            content = base64.b64decode(response.json()['content']).decode('utf-8')
            return json.loads(content)
    except Exception as e:
        st.error(f"Kunde inte ladda data från GitHub: {e}")
    return default_data

def github_save_file(file_path: str, content: Any, commit_message: str) -> Tuple[bool, str]:
    if not GITHUB_TOKEN or not GITHUB_REPO:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
            return True, "Sparat lokalt"
        except Exception as e:
            return False, str(e)

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    
    sha = None
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            sha = response.json()['sha']
    except Exception:
        pass
        
    encoded_content = base64.b64encode(json.dumps(content, indent=4, ensure_ascii=False).encode('utf-8')).decode('utf-8')
    data = {"message": commit_message, "content": encoded_content}
    if sha:
        data["sha"] = sha
        
    try:
        response = requests.put(url, headers=headers, json=data, timeout=10)
        if response.status_code in [200, 201]:
            return True, "Sparat till GitHub"
        return False, response.text
    except Exception as e:
        return False, str(e)

# --- VÄXELKURS ---
@st.cache_data(ttl=3600)
def fetch_eur_to_sek_rate() -> float:
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return float(resp.json().get("rates", {}).get("SEK", 11.50))
    except Exception:
        pass
    return 11.50

eur_to_sek = fetch_eur_to_sek_rate()

# --- LADDA DATA ---
if "collection" not in st.session_state or st.session_state["collection"] is None:
    st.session_state["collection"] = github_load_file(DATA_FILE_PATH, [])

collection = st.session_state["collection"]

# --- HUVUDLAYOUT ---
st.title("⚡ Pokémon 30th Anniversary Collection")

if not collection:
    st.warning("Hittade ingen kortdata i JSON-filen.")
else:
    df = pd.DataFrame(collection)

    # Beräkningar
    df["Värde (EUR)"] = pd.to_numeric(df.get("Värde (EUR)", 0), errors='coerce').fillna(0.0)
    df["Köpt för (EUR)"] = pd.to_numeric(df.get("Köpt för (EUR)", 0), errors='coerce').fillna(0.0)
    df["Värde idag (SEK)"] = (df["Värde (EUR)"] * eur_to_sek).round(2)
    df["Köpt för (SEK)"] = (df["Köpt för (EUR)"] * eur_to_sek).round(2)

    owned_df = df[df["Äger"] == True]
    total_cards = len(df)
    owned_count = len(owned_df)
    progress_pct = (owned_count / total_cards) if total_cards > 0 else 0.0

    total_value_sek = owned_df["Värde idag (SEK)"].sum()
    total_cost_sek = owned_df["Köpt för (SEK)"].sum()
    total_profit_sek = total_value_sek - total_cost_sek

    # KPI Mätare
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Samlade Kort", f"{owned_count} / {total_cards}", f"{progress_pct*100:.1f}%")
    c2.metric("Totalt Värde (SEK)", f"{total_value_sek:,.2f} kr")
    c3.metric("Totalt Köpöpris (SEK)", f"{total_cost_sek:,.2f} kr")
    c4.metric("Vinst/Förlust (SEK)", f"{total_profit_sek:,.2f} kr")

    st.progress(progress_pct)
    st.divider()

    # Data Editor Inställningar
    column_config = {
        "_id": None,
        "Äger": st.column_config.CheckboxColumn("Äger", width=50),
        "Bild": st.column_config.ImageColumn("Bild", width=60),
        "Pärmnummer": st.column_config.NumberColumn("Pärmnr.", width=60, disabled=True),
        "Språk": st.column_config.TextColumn("Språk", width=60, disabled=True),
        "Namn": st.column_config.TextColumn("Namn", width=160, disabled=True),
        "Setnr.": st.column_config.TextColumn("Setnr.", width=80, disabled=True),
        "SetBet.": st.column_config.TextColumn("SetBet.", width=80, disabled=True),
        "Set": st.column_config.TextColumn("Set", width=160, disabled=True),
        "Sällsynthet": st.column_config.TextColumn("Rarity", width=120, disabled=True),
        "Utgivningsår": st.column_config.NumberColumn("År", width=60, disabled=True, format="%d"),
        "Övrigt": st.column_config.SelectboxColumn("Övrigt", options=["Normal", "Holo", "Reverse Holo", "Secret Rare", "Promo", "Full Art", "Classic Collection"], width=110),
        "Skick": st.column_config.SelectboxColumn("Skick", options=["NM", "EX", "GD", "LP", "PL", "PO"], width=70),
        "Köpt för (EUR)": st.column_config.NumberColumn("Köpt (EUR)", format="€%.2f", width=85),
        "Värde (EUR)": st.column_config.NumberColumn("Värde (EUR)", format="€%.2f", width=85),
        "Värde idag (SEK)": st.column_config.NumberColumn("Värde (SEK)", format="%.2f kr", width=100, disabled=True),
        "Google Sök": st.column_config.LinkColumn("Sök Cardmarket", display_text="🔍 Sök", width=100),
        "Egen Cardmarket Länk": st.column_config.TextColumn("Klistra in Cardmarket URL", width=200)
    }

    cols_display = [
        "Äger", "Bild", "Pärmnummer", "Språk", "Namn", "Setnr.", "SetBet.", "Set",
        "Sällsynthet", "Utgivningsår", "Övrigt", "Skick", "Köpt för (EUR)",
        "Värde (EUR)", "Värde idag (SEK)", "Google Sök", "Egen Cardmarket Länk", "_id"
    ]

    edited_df = st.data_editor(
        df[cols_display],
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="editor_30th_anniversary"
    )

    col_btn, col_info = st.columns([1, 4])
    with col_btn:
        if st.button("💾 Spara Ändringar", type="primary", use_container_width=True):
            updated_records = edited_df.to_dict(orient="records")
            
            # Säkra att alla numeriska värden sparas korrekt
            for row in updated_records:
                row["Köpt för (EUR)"] = float(row.get("Köpt för (EUR)", 0.0) or 0.0)
                row["Värde (EUR)"] = float(row.get("Värde (EUR)", 0.0) or 0.0)
                row["Köpt för (SEK)"] = round(row["Köpt för (EUR)"] * eur_to_sek, 2)
                row["Värde idag (SEK)"] = round(row["Värde (EUR)"] * eur_to_sek, 2)

            success, msg = github_save_file(DATA_FILE_PATH, updated_records, "Uppdaterade 30th Anniversary samling")
            if success:
                st.session_state["collection"] = updated_records
                st.success("Ändringarna sparades framgångsrikt!")
                st.rerun()
            else:
                st.error(f"Gick inte att spara: {msg}")
