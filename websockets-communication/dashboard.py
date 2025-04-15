import streamlit as st
import websocket
import threading
import queue
from streamlit.runtime.scriptrunner import add_script_run_ctx
import pandas as pd
import json
import altair as alt
import time

#   === Le dashboard marche bien! ===
#   Visualisation à améliorer (choisir les bons graphes)
#   Bouton de rafraîchissement manuel

st.set_page_config(
    page_title="Élections Sénégal - Tableau de Bord en Temps Réel",
    page_icon="🇸🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

AGG_KEYS = {
    "votes_par_candidat": ("🗳️ Votes par Candidat", "candidat_complet", "total_votes"),
    "votes_par_lieu": ("📍 Votes par Lieu", "lieu_vote", "votes_par_lieu"),
    "votes_par_age": ("👥 Votes par Âge", "age_group", "votes_par_age"),
    "votes_par_sexe": ("⚖️ Votes par Sexe", "sexe", "votes_par_sexe")
}

# Initialisation
if "aggregations" not in st.session_state:
    st.session_state.aggregations = {key: pd.DataFrame() for key in AGG_KEYS}

if "message_queue" not in st.session_state:
    st.session_state.message_queue = queue.Queue()

if "websocket_thread" not in st.session_state:
    st.session_state.websocket_thread = None

if "last_update" not in st.session_state:
    st.session_state.last_update = time.strftime("%d/%m/%Y à %H:%M:%S")

# === Fonctions WebSocket ===
def on_message(ws, message):
    st.session_state.message_queue.put(message)

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket fermé")

def on_open(ws):
    print("WebSocket connection opened")

def run_websocket():
    ws = websocket.WebSocketApp(
        "ws://websocket_server:8765",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()


def update_dataframe(current_df, new_df, group_key, value_col):
    if current_df.empty:
        return new_df
    else:
        merged_df = pd.concat([current_df, new_df])
        return merged_df.groupby(group_key, as_index=False)[value_col].sum()

def update_aggregations():
    while not st.session_state.message_queue.empty():
        message = st.session_state.message_queue.get()
        try:
            data = json.loads(message)
            for key, (_, x_col, y_col) in AGG_KEYS.items():
                agg_data = data.get(key)
                if isinstance(agg_data, list) and len(agg_data) > 0:
                    df = pd.DataFrame(agg_data)

                    if key == "votes_par_candidat" and "candidat_prenom" in df.columns and "candidat_nom" in df.columns:
                        df["candidat_complet"] = df["candidat_prenom"].astype(str) + " " + df["candidat_nom"].astype(str)

                    st.session_state.aggregations[key] = update_dataframe(
                        st.session_state.aggregations[key],
                        df,
                        group_key=x_col,
                        value_col=y_col
                    )
                    st.session_state.last_update = time.strftime("%d/%m/%Y à %H:%M:%S")
        except Exception as e:
            print("Erreur de parsing :", e)


# === Thread WebSocket ===
if st.session_state.websocket_thread is None or not st.session_state.websocket_thread.is_alive():
    websocket_thread = threading.Thread(target=run_websocket, daemon=True)
    add_script_run_ctx(websocket_thread)
    websocket_thread.start()
    st.session_state.websocket_thread = websocket_thread

# === SIDEBAR ===
st.sidebar.title("🧾 Informations")
st.sidebar.info("""
Ce tableau de bord présente les résultats des élections présidentielles du Sénégal en temps réel.
Les données sont mises à jour automatiquement à mesure que les votes sont comptabilisés.
""")
st.sidebar.write(f"🕒 Dernière mise à jour : `{st.session_state.last_update}`")

# Bouton de rafraîchissement manuel
if st.sidebar.button("🔄 Rafraîchir maintenant"):
    update_aggregations()

# === MAIN ===
st.title("📡 Suivi des Votes Présidentiels - Sénégal 🇸🇳")

tabs = st.tabs([title for title, *_ in AGG_KEYS.values()])

for i, (key, (title, x_col, y_col)) in enumerate(AGG_KEYS.items()):
    with tabs[i]:
        df = st.session_state.aggregations[key]
        if df.empty:
            st.info(f"Aucune donnée reçue pour {title}")
        else:
            # Affichage des infos
            st.markdown(f"### {title}")
            st.markdown(f"🧮 **Nombre total de votes comptabilisés** : `{int(df[y_col].sum()):,}`")
            st.markdown(f"📊 Répartition des votes selon **{x_col}**")
            
            #st.dataframe(df, use_container_width=True)
            st.write("Colonnes du dataframe :", df.columns)
            st.write(df.dtypes)

            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X(f"{x_col}:N", title=x_col.replace("_", " ").capitalize()),
                y=alt.Y(f"{y_col}:Q", title="Nombre de votes"),
                color=alt.Color(f"{x_col}:N", legend=None)
            ).properties(
                width="container",
                height=400,
                title=title
            )
            st.altair_chart(chart, use_container_width=True)