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
        return float(response.json()["rates"]["SEK"])
    except Exception:
        return 11.28

exchange_rate = get_eur_sek_rate()

# --- HJÄLPFUNKTION FÖR DATAFRAME ---
def prepare_card_dataframe(data: list) -> pd.DataFrame:
    df = pd.DataFrame(data)
    if df.empty:
        return df

    defaults = {"Äger": False, "Antal": 1, "Köpt för (EUR)": 0.0, "Värde (EUR)": 0.0}
    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val

    df = df.drop(columns=[c for c in ["Skick", "Egen Cardmarket Länk", "Egen Länk"] if c in df.columns])

    if "Köpt för (SEK)" not in df.columns:
        df["Köpt för (SEK)"] = (pd.to_numeric(df["Köpt för (EUR)"], errors='coerce').fillna(0.0) * exchange_rate).round(2)
    if "Värde (SEK)" not in df.columns:
        df["Värde (SEK)"] = (pd.to_numeric(df["Värde (EUR)"], errors='coerce').fillna(0.0) * exchange_rate).round(2)

    return df

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

df_all = prepare_card_dataframe(st.session_state.cards_data)

if not df_all.empty:
    # --- FILTER & SORTERING ---
    st.markdown("### 🔍 Filter & Sortering")
    f_col1, f_col2 = st.columns([3, 1])

    all_rarities = df_all["Sällsynthet"].dropna().unique().tolist() if "Sällsynthet" in df_all.columns else []

    with f_col1:
        selected_rarities = st.pills("Filtrera på Sällsynthet:", options=all_rarities, selection_mode="multi", default=all_rarities)

    with f_col2:
        filter_status = st.radio("Visa:", ["Alla", "Bara Ägda", "Bara Saknade"], horizontal=True)

    filtered_df = df_all.copy()
    if selected_rarities:
        filtered_df = filtered_df[filtered_df["Sällsynthet"].isin(selected_rarities)]
    
    if filter_status == "Bara Ägda":
        filtered_df = filtered_df[filtered_df["Äger"] == True]
    elif filter_status == "Bara Saknade":
        filtered_df = filtered_df[filtered_df["Äger"] == False]

    st.markdown("---")
    st.markdown("### 📋 Kortlista")

    # Tabellrubriker
    h_cols = st.columns([0.8, 1.8, 2, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
    with h_cols[0]: st.markdown("**Äger**")
    with h_cols[1]: st.markdown("**Antal**")
    with h_cols[2]: st.markdown("**Namn**")
    with h_cols[3]: st.markdown("**Setnr.**")
    with h_cols[4]: st.markdown("**Symbol**")
    with h_cols[5]: st.markdown("**Sällsynthet**")
    with h_cols[6]: st.markdown("**Köpt för (€)**")
    with h_cols[7]: st.markdown("**Köpt för (kr)**")
    with h_cols[8]: st.markdown("**Värde (€)**")
    with h_cols[9]: st.markdown("**Värde (kr)**")
    with h_cols[10]: st.markdown("**Cardmarket**")

    # Rendera rader med minus/plus för antal
    for idx, row in filtered_df.iterrows():
        s_nr = row["Setnr."]
        card_obj = next((c for c in st.session_state.cards_data if c.get("Setnr.") == s_nr), None)
        if not card_obj:
            continue

        r_cols = st.columns([0.8, 1.8, 2, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])

        with r_cols[0]:
            new_ager = st.checkbox("", value=bool(card_obj.get("Äger", False)), key=f"ager_{s_nr}", label_visibility="collapsed")
            if new_ager != card_obj.get("Äger", False):
                card_obj["Äger"] = new_ager

        with r_cols[1]:
            sub_c1, sub_c2, sub_c3 = st.columns([1, 1.2, 1])
            current_antal = int(card_obj.get("Antal", 1))
            with sub_c1:
                if st.button("➖", key=f"minus_{s_nr}", help="Minska antal"):
                    if current_antal > 1:
                        card_obj["Antal"] = current_antal - 1
                        st.rerun()
            with sub_c2:
                st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: bold;'>{current_antal}</div>", unsafe_allow_html=True)
            with sub_c3:
                if st.button("➕", key=f"plus_{s_nr}", help="Öka antal"):
                    card_obj["Antal"] = current_antal + 1
                    st.rerun()

        with r_cols[2]:
            st.text(card_obj.get("Namn", ""))
        with r_cols[3]:
            st.text(card_obj.get("Setnr.", ""))
        with r_cols[4]:
            st.text(card_obj.get("Symbol", ""))
        with r_cols[5]:
            st.text(card_obj.get("Sällsynthet", ""))

        with r_cols[6]:
            new_k_eur = st.number_input("", value=float(card_obj.get("Köpt för (EUR)", 0.0) or 0.0), format="%.2f", key=f"k_eur_{s_nr}", label_visibility="collapsed")
            if new_k_eur != float(card_obj.get("Köpt för (EUR)", 0.0) or 0.0):
                card_obj["Köpt för (EUR)"] = round(new_k_eur, 2)
                card_obj["Köpt för (SEK)"] = round(new_k_eur * exchange_rate, 2)

        with r_cols[7]:
            sek_kopt = float(card_obj.get("Köpt för (EUR)", 0.0) or 0.0) * exchange_rate
            st.text(f"{sek_kopt:.2f} kr")

        with r_cols[8]:
            new_v_eur = st.number_input("", value=float(card_obj.get("Värde (EUR)", 0.0) or 0.0), format="%.2f", key=f"v_eur_{s_nr}", label_visibility="collapsed")
            if new_v_eur != float(card_obj.get("Värde (EUR)", 0.0) or 0.0):
                card_obj["Värde (EUR)"] = round(new_v_eur, 2)
                card_obj["Värde (SEK)"] = round(new_v_eur * exchange_rate, 2)

        with r_cols[9]:
            sek_varde = float(card_obj.get("Värde (EUR)", 0.0) or 0.0) * exchange_rate
            st.text(f"{sek_varde:.2f} kr")

        with r_cols[10]:
            google_url = card_obj.get("Google Sök", "")
            if google_url:
                st.markdown(f"[🔍 Sök]({google_url})")

    st.markdown("---")
    if st.button("💾 Spara ändringar till GitHub", type="primary"):
        success, msg = github_save_file(DATA_FILE_PATH, st.session_state.cards_data, "Uppdaterade 30th Anniversary samling")
        if success:
            st.success("Ändringarna sparades direkt till GitHub!")
            st.rerun()
        else:
            st.error(f"Kunde inte spara till GitHub: {msg}")

    # Sammanfattning längst ned
    temp_df = prepare_card_dataframe(st.session_state.cards_data)

    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)

    total_owned = temp_df["Äger"].sum()
    owned_mask = temp_df["Äger"] == True
    quantities = pd.to_numeric(temp_df.loc[owned_mask, "Antal"], errors='coerce').fillna(1)

    total_bought_eur = (temp_df.loc[owned_mask, "Köpt för (EUR)"].astype(float) * quantities).sum()
    total_val_eur = (temp_df.loc[owned_mask, "Värde (EUR)"].astype(float) * quantities).sum()
    total_bought_sek = (temp_df.loc[owned_mask, "Köpt för (SEK)"].astype(float) * quantities).sum()
    total_val_sek = (temp_df.loc[owned_mask, "Värde (SEK)"].astype(float) * quantities).sum()

    c1.metric("Kort Ägda", f"{total_owned} / {len(temp_df)}")
    c2.metric("Totalt Köpt", f"{total_bought_eur:.2f} €", f"{total_bought_sek:.2f} SEK")
    c3.metric("Totalt Värde", f"{total_val_eur:.2f} €", f"{total_val_sek:.2f} SEK")
    c4.metric("Vinst / Förlust", f"{(total_val_eur - total_bought_eur):.2f} €", f"{(total_val_sek - total_bought_sek):.2f} SEK")
else:
    st.info("Ingen data hittades.")
