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

    # Sätt standardvärden för saknade kolumner
    defaults = {"Äger": False, "Antal": 1, "Köpt för (EUR)": 0.0, "Värde (EUR)": 0.0}
    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val

    # Rensa ut ovälkomna kolumner om de finns
    df = df.drop(columns=[c for c in ["Skick", "Egen Cardmarket Länk", "Egen Länk"] if c in df.columns])

    # Skapa SEK-kolumner om de saknas
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

    # Bestäm kolumnordning
    display_columns = [col for col in filtered_df.columns if col != "_id"]
    desired_order = ["Äger", "Antal", "Namn", "Setnr.", "Symbol", "Sällsynthet", "Köpt för (EUR)", "Köpt för (SEK)", "Värde (EUR)", "Värde (SEK)", "Google Sök"]
    display_columns = [c for c in desired_order if c in display_columns] + [c for c in display_columns if c not in desired_order]

    st.markdown("---")
    st.markdown("### 📋 Kortlista")

    edited_df = st.data_editor(
        filtered_df[display_columns],
        column_config={
            "Äger": st.column_config.CheckboxColumn("Äger", default=False),
            "Antal": st.column_config.NumberColumn("Antal", min_value=1, step=1, format="%d"),
            "Namn": st.column_config.TextColumn("Namn", disabled=True),
            "Setnr.": st.column_config.TextColumn("Setnr.", disabled=True),
            "Symbol": st.column_config.TextColumn("Symbol", disabled=True),
            "Sällsynthet": st.column_config.TextColumn("Sällsynthet", disabled=True),
            "Köpt för (EUR)": st.column_config.NumberColumn("Köpt för (EUR)", format="%.2f €"),
            "Köpt för (SEK)": st.column_config.NumberColumn("Köpt för (SEK)", format="%.2f kr"),
            "Värde (EUR)": st.column_config.NumberColumn("Värde (EUR)", format="%.2f €"),
            "Värde (SEK)": st.column_config.NumberColumn("Värde (SEK)", format="%.2f kr"),
            "Google Sök": st.column_config.LinkColumn("Cardmarket / Sök", display_text="🔍 Sök på Cardmarket"),
        },
        disabled=["Namn", "Setnr.", "Symbol", "Sällsynthet", "Google Sök"],
        hide_index=True,
        use_container_width=True,
        key="editor"
    )

    if st.button("💾 Spara ändringar till GitHub", type="primary"):
        edited_map = {row["Setnr."]: row for row in edited_df.to_dict(orient="records")}
        updated_data = []

        for orig_row in st.session_state.cards_data:
            s_nr = orig_row.get("Setnr.")
            if s_nr in edited_map:
                r = edited_map[s_nr]
                orig_row["Äger"] = bool(r.get("Äger", False))
                try:
                    orig_row["Antal"] = int(r.get("Antal", 1))
                except (ValueError, TypeError):
                    orig_row["Antal"] = 1
                
                # Uppdatera prislogik (EUR / SEK)
                for prefix in ["Köpt för", "Värde"]:
                    eur_key, sek_key = f"{prefix} (EUR)", f"{prefix} (SEK)"
                    old_eur = float(orig_row.get(eur_key, 0.0) or 0.0)
                    old_sek = float(orig_row.get(sek_key, (old_eur * exchange_rate)) or 0.0)
                    
                    new_eur = float(r.get(eur_key, 0.0) or 0.0)
                    new_sek = float(r.get(sek_key, 0.0) or 0.0)

                    if new_sek != round(old_eur * exchange_rate, 2) and new_sek != old_sek:
                        orig_row[sek_key] = round(new_sek, 2)
                        orig_row[eur_key] = round(new_sek / exchange_rate, 2)
                    else:
                        orig_row[eur_key] = round(new_eur, 2)
                        orig_row[sek_key] = round(new_eur * exchange_rate, 2)
            
            updated_data.append(orig_row)

        success, msg = github_save_file(DATA_FILE_PATH, updated_data, "Uppdaterade 30th Anniversary samling")

        if success:
            st.session_state["cards_data"] = updated_data
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
