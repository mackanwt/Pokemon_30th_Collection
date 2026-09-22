import streamlit as st
import pandas as pd
import json
import requests
import base64

# --- KONFIGURATION ---
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
        
    encoded_content = base64.b64encode(json.dumps(content, ensure_ascii=4).encode('utf-8')).decode('utf-8')
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
def fetch_eur_to_sek_rate() -> float:
    try:
        url = "https://api.exchangerate-api.com/v4/latest/EUR"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return float(resp.json().get("rates", {}).get("SEK", 11.28))
    except Exception:
        pass
    return 11.28

eur_to_sek = fetch_eur_to_sek_rate()

# --- LADDA DATA ---
if "app_data" not in st.session_state or st.session_state["app_data"] is None:
    loaded_data = github_load_file(DATA_FILE_PATH, [])
    if not isinstance(loaded_data, list):
        loaded_data = []
    st.session_state["app_data"] = loaded_data

collection = st.session_state["app_data"]

# --- LAYOUT & RUBRIK ---
col_title, col_rate = st.columns([3, 1])
with col_title:
    st.title("🎴 Pokémon 30th Anniversary Collection")
with col_rate:
    st.markdown(
        f"<div style='text-align: right; padding-top: 25px; color: #666; font-size: 14px;'>"
        f"💱 <b>Aktuell växelkurs:</b> 1 EUR = <b>{eur_to_sek:.2f} SEK</b>"
        f"</div>",
        unsafe_allow_html=True
    )

if collection:
    df = pd.DataFrame(collection)
    
    # Säkerställ att kolumner finns
    for col in ["Äger", "Köpt för (EUR)", "Värde (EUR)", "Skick", "Egen Cardmarket Länk"]:
        if col not in df.columns:
            df[col] = False if col == "Äger" else (0.0 if "EUR" in col else "")

    df["Köpt för (SEK)"] = (pd.to_numeric(df["Köpt för (EUR)"], errors='coerce').fillna(0.0) * eur_to_sek).round(2)
    df["Värde (SEK)"] = (pd.to_numeric(df["Värde (EUR)"], errors='coerce').fillna(0.0) * eur_to_sek).round(2)

    column_config_edit = {
        "_id": None,
        "Äger": st.column_config.CheckboxColumn("Äger", width=50),
        "Namn": st.column_config.TextColumn("Namn", disabled=True, width=150),
        "Setnr.": st.column_config.TextColumn("Setnr.", disabled=True, width=80),
        "Symbol": st.column_config.TextColumn("Symbol", disabled=True, width=70),
        "Sällsynthet": st.column_config.TextColumn("Sällsynthet", disabled=True, width=130),
        "Skick": st.column_config.SelectboxColumn("Skick", options=["NM", "EX", "GD", "LP", "PL", "PO"], width=70),
        "Köpt för (EUR)": st.column_config.NumberColumn("Köpt (€)", format="%.2f", width=80),
        "Köpt för (SEK)": st.column_config.NumberColumn("Köpt (SEK)", format="%.2f kr", width=90, disabled=True),
        "Värde (EUR)": st.column_config.NumberColumn("Värde (€)", format="%.2f", width=80),
        "Värde (SEK)": st.column_config.NumberColumn("Värde (SEK)", format="%.2f kr", width=90, disabled=True),
        "Google Sök": st.column_config.LinkColumn("Cardmarket Sök", display_text="🔍 Sök", width=100),
        "Egen Cardmarket Länk": st.column_config.TextColumn("Egen Länk", width=150)
    }

    edit_columns = [col for col in df.columns if col != "_id"]
    edit_columns = ["_id"] + edit_columns

    edited_df = st.data_editor(
        df[edit_columns],
        column_config=column_config_edit,
        use_container_width=True,
        hide_index=True,
        key="collection_editor"
    )

    if st.button("💾 Spara ändringar till GitHub", type="primary", use_container_width=True):
        raw_edited = edited_df.to_dict(orient="records")
        
        processed_list = []
        for row in raw_edited:
            k_eur = float(row.get("Köpt för (EUR)", 0.0) or 0.0)
            v_eur = float(row.get("Värde (EUR)", 0.0) or 0.0)
            
            clean_card = {
                "_id": row.get("_id"),
                "Äger": bool(row.get("Äger", False)),
                "Namn": row.get("Namn", ""),
                "Setnr.": row.get("Setnr.", ""),
                "Symbol": row.get("Symbol", ""),
                "Sällsynthet": row.get("Sällsynthet", ""),
                "Skick": row.get("Skick", "NM"),
                "Köpt för (EUR)": k_eur,
                "Köpt för (SEK)": round(k_eur * eur_to_sek, 2),
                "Värde (EUR)": v_eur,
                "Värde (SEK)": round(v_eur * eur_to_sek, 2),
                "Google Sök": row.get("Google Sök", ""),
                "Egen Cardmarket Länk": str(row.get("Egen Cardmarket Länk") or "").strip()
            }
            processed_list.append(clean_card)

        success, msg = github_save_file(DATA_FILE_PATH, processed_list, "Uppdaterade samling 30th Anniversary")
        
        if success:
            st.session_state["app_data"] = processed_list
            st.success("Ändringarna sparades och skickades direkt till GitHub!")
            st.rerun()
        else:
            st.error(f"Kunde inte spara till GitHub: {msg}")

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    owned_df = df[df["Äger"] == True]
    c1.metric("Kort Ägda", f"{len(owned_df)} / {len(df)}")
    c2.metric("Totalt Köpt (SEK)", f"{owned_df['Köpt för (SEK)'].sum():,.2f} kr")
    c3.metric("Totalt Värde (SEK)", f"{owned_df['Värde idag (SEK)' if 'Värde idag (SEK)' in owned_df else 'Värde (SEK)'].sum():,.2f} kr")
    c4.metric("Vinst / Förlust", f"{(owned_df['Värde (SEK)'].sum() - owned_df['Köpt för (SEK)'].sum()):,.2f} kr")
else:
    st.info("Ingen data hittades i JSON-filen.")
