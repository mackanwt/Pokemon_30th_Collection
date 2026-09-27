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

df_all = pd.DataFrame(st.session_state.cards_data)

if not df_all.empty:
    for col in ["Äger", "Antal", "Köpt för (EUR)", "Värde (EUR)"]:
        if col not in df_all.columns:
            if col == "Äger":
                df_all[col] = False
            elif col == "Antal":
                df_all[col] = 1
            else:
                df_all[col] = 0.0

    for c in ["Skick", "Egen Cardmarket Länk", "Egen Länk"]:
        if c in df_all.columns:
            df_all = df_all.drop(columns=[c])

    # Se till att SEK-kolumner finns i dataframe
    if "Köpt för (SEK)" not in df_all.columns:
        df_all["Köpt för (SEK)"] = (pd.to_numeric(df_all["Köpt för (EUR)"], errors='coerce').fillna(0.0) * exchange_rate).round(2)
    if "Värde (SEK)" not in df_all.columns:
        df_all["Värde (SEK)"] = (pd.to_numeric(df_all["Värde (EUR)"], errors='coerce').fillna(0.0) * exchange_rate).round(2)

    # --- FILTER & SORTERING ---
    st.markdown("### 🔍 Filter & Sortering")
    f_col1, f_col2 = st.columns([3, 1])

    all_rarities = df_all["Sällsynthet"].dropna().unique().tolist() if "Sällsynthet" in df_all.columns else []

    with f_col1:
        selected_rarities = st.pills("Filtrera på Sällsynthet:", options=all_rarities, selection_mode="multi", default=all_rarities)

    with f_col2:
        filter_status = st.radio("Visa:", ["Alla", "Bara Ägda", "Bara Saknade"], horizontal=True)

    # Applicera filter för visning
    filtered_df = df_all.copy()
    if selected_rarities:
        filtered_df = filtered_df[filtered_df["Sällsynthet"].isin(selected_rarities)]
    
    if filter_status == "Bara Ägda":
        filtered_df = filtered_df[filtered_df["Äger"] == True]
    elif filter_status == "Bara Saknade":
        filtered_df = filtered_df[filtered_df["Äger"] == False]

    st.markdown("---")
    st.markdown("### 📋 Kortlista")

    # Tabellhuvud som matchar kolumnerna
    header_cols = st.columns([0.8, 1.5, 2.5, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])
    with header_cols[0]: st.markdown("**Äger**")
    with header_cols[1]: st.markdown("**Antal**")
    with header_cols[2]: st.markdown("**Namn**")
    with header_cols[3]: st.markdown("**Setnr.**")
    with header_cols[4]: st.markdown("**Symbol**")
    with header_cols[5]: st.markdown("**Sällsynthet**")
    with header_cols[6]: st.markdown("**Köpt för (EUR)**")
    with header_cols[7]: st.markdown("**Köpt för (SEK)**")
    with header_cols[8]: st.markdown("**Värde (EUR)**")
    with header_cols[9]: st.markdown("**Värde (SEK)**")
    with header_cols[10]: st.markdown("**Cardmarket / Sök**")

    # Rendera rader med exakt (- antal +) struktur i antal-kolumnen
    for _, row in filtered_df.iterrows():
        s_nr = row["Setnr."]
        card_obj = next((c for c in st.session_state.cards_data if c.get("Setnr.") == s_nr), None)
        if not card_obj:
            continue

        r_cols = st.columns([0.8, 1.5, 2.5, 1, 1, 1.5, 1.5, 1.5, 1.5, 1.5, 1.5])

        with r_cols[0]:
            new_ager = st.checkbox("", value=bool(card_obj.get("Äger", False)), key=f"ager_{s_nr}", label_visibility="collapsed")
            if new_ager != card_obj.get("Äger", False):
                card_obj["Äger"] = new_ager

        with r_cols[1]:
            # Kompakt layout för minus, siffra, plus inuti kolumnen
            sub_c1, sub_c2, sub_c3 = st.columns([1, 1.2, 1])
            current_antal = int(card_obj.get("Antal", 1) or 1)
            
            with sub_c1:
                if st.button("➖", key=f"minus_{s_nr}"):
                    if current_antal > 1:
                        card_obj["Antal"] = current_antal - 1
                        st.rerun()
            with sub_c2:
                st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: bold;'>{current_antal}</div>", unsafe_allow_html=True)
            with sub_c3:
                if st.button("➕", key=f"plus_{s_nr}"):
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
            old_k_eur = float(card_obj.get("Köpt för (EUR)", 0.0) or 0.0)
            new_k_eur = st.number_input("", value=old_k_eur, format="%.2f", key=f"k_eur_{s_nr}", label_visibility="collapsed")
            if new_k_eur != old_k_eur:
                card_obj["Köpt för (EUR)"] = round(new_k_eur, 2)
                card_obj["Köpt för (SEK)"] = round(new_k_eur * exchange_rate, 2)

        with r_cols[7]:
            sek_kopt = float(card_obj.get("Köpt för (EUR)", 0.0) or 0.0) * exchange_rate
            st.text(f"{sek_kopt:.2f} kr")

        with r_cols[8]:
            old_v_eur = float(card_obj.get("Värde (EUR)", 0.0) or 0.0)
            new_v_eur = st.number_input("", value=old_v_eur, format="%.2f", key=f"v_eur_{s_nr}", label_visibility="collapsed")
            if new_v_eur != old_v_eur:
                card_obj["Värde (EUR)"] = round(new_v_eur, 2)
                card_obj["Värde (SEK)"] = round(new_v_eur * exchange_rate, 2)

        with r_cols[9]:
            sek_varde = float(card_obj.get("Värde (EUR)", 0.0) or 0.0) * exchange_rate
            st.text(f"{sek_varde:.2f} kr")

        with r_cols[10]:
            google_url = card_obj.get("Google Sök", "")
            if google_url:
                st.markdown(f"[🔍 Sök på Cardmarket]({google_url})")

    st.markdown("---")
    if st.button("💾 Spara ändringar till GitHub", type="primary"):
        success, msg = github_save_file(DATA_FILE_PATH, st.session_state.cards_data, "Uppdaterade 30th Anniversary samling")
        if success:
            st.success("Ändringarna sparades direkt till GitHub!")
            st.rerun()
        else:
            st.error(f"Kunde inte spara till GitHub: {msg}")

    # Sammanfattning längst ned (beräknas på hela samlingen med hänsyn till dubletter)
    temp_df = pd.DataFrame(st.session_state.cards_data)
    for col in ["Äger", "Antal", "Köpt för (EUR)", "Värde (EUR)", "Köpt för (SEK)", "Värde (SEK)"]:
        if col not in temp_df.columns:
            if col == "Äger":
                temp_df[col] = False
            elif col == "Antal":
                temp_df[col] = 1
            else:
                temp_df[col] = 0.0

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
