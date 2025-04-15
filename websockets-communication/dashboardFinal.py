import streamlit as st
import websocket
import threading
import queue
import pandas as pd
import json
import altair as alt
import time
from streamlit.runtime.scriptrunner import add_script_run_ctx
from streamlit_autorefresh import st_autorefresh

#   === Le dashboard marche bien! ===
#   Graphes choisis : 
#       - KPIs globaux : total des votes, pourcentage de voix, nombre de lieux de vote
#       - diagrammes circulaires pour les votes globaux par genre et par âge
#       - barres empilées pour les votes par candidat selon le genre et l'âge
#   Bouton de rafraîchissement manuel

st.set_page_config(
    page_title="Élections Sénégal - Tableau de Bord en Temps Réel",
    page_icon="🇸🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st_autorefresh(interval=5000, key="autorefresh")

# Initialisation des états
if "votes_candidat_df" not in st.session_state:
    st.session_state.votes_candidat_df = pd.DataFrame()
if "votes_genre_df" not in st.session_state:
    st.session_state.votes_genre_df = pd.DataFrame()
if "votes_age_df" not in st.session_state:
    st.session_state.votes_age_df = pd.DataFrame()
if "votes_lieu_df" not in st.session_state:
    st.session_state.votes_lieu_df = pd.DataFrame()
if "message_queue" not in st.session_state:
    st.session_state.message_queue = queue.Queue()
if "websocket_thread" not in st.session_state:
    st.session_state.websocket_thread = None
if "last_update" not in st.session_state:
    st.session_state.last_update = time.strftime("%d/%m/%Y à %H:%M:%S")


# WebSocket
def on_message(ws, message):
    st.session_state.message_queue.put(message)

def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("WebSocket fermé")

def on_open(ws):
    print("WebSocket ouvert")

def run_websocket():
    ws = websocket.WebSocketApp(
        "ws://websocket_server:8765",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()


# Fonction de concaténation du nom du candidat
def preprocess_df(df):
    if "candidat_prenom" in df.columns and "candidat_nom" in df.columns:
        df["candidat_complet"] = df["candidat_prenom"].astype(str) + " " + df["candidat_nom"].astype(str)
    else:
        df["candidat_complet"] = "Inconnu"
    return df

def update_dataframe(current_df, new_df, group_keys, value_col):
    if current_df.empty:
        return new_df
    else:
        df = pd.concat([current_df, new_df])
        return df.groupby(group_keys, as_index=False)[value_col].sum()

# Update via messages WebSocket
def update_aggregations():
    while not st.session_state.message_queue.empty():
        message = st.session_state.message_queue.get()
        try:
            data = json.loads(message)

            if "votes_par_candidat" in data:
                df = pd.DataFrame(data["votes_par_candidat"])
                df = preprocess_df(df)
                st.session_state.votes_candidat_df = update_dataframe(st.session_state.votes_candidat_df, df, ["candidat_complet"], "total_votes")

            if "votes_par_sexe" in data:
                df = pd.DataFrame(data["votes_par_sexe"])
                df = preprocess_df(df)
                st.session_state.votes_genre_df = update_dataframe(st.session_state.votes_genre_df, df, ["candidat_complet", "sexe"], "votes_par_sexe")

            if "votes_par_age" in data:
                df = pd.DataFrame(data["votes_par_age"])
                df = preprocess_df(df)
                st.session_state.votes_age_df = update_dataframe(st.session_state.votes_age_df, df, ["candidat_complet", "age_group"], "votes_par_age")

            if "votes_par_lieu" in data:
                df = pd.DataFrame(data["votes_par_lieu"])
                st.session_state.votes_lieu_df = update_dataframe(st.session_state.votes_lieu_df, df, ["lieu_vote"], "votes_par_lieu")

            st.session_state.last_update = time.strftime("%d/%m/%Y à %H:%M:%S")

        except Exception as e:
            print("Erreur de parsing:", e)

# Lancer le WebSocket
if st.session_state.websocket_thread is None or not st.session_state.websocket_thread.is_alive():
    websocket_thread = threading.Thread(target=run_websocket, daemon=True)
    add_script_run_ctx(websocket_thread)
    websocket_thread.start()
    st.session_state.websocket_thread = websocket_thread

# === MAJ des données à chaque exécution ===
update_aggregations()

# Sidebar
st.sidebar.title("🧾 Informations")
st.sidebar.markdown("📡 Tableau de bord des élections présidentielles du Sénégal.")
st.sidebar.write(f"🕒 Dernière mise à jour : `{st.session_state.last_update}`")
#if st.sidebar.button("🔄 Rafraîchir maintenant"):
#    st.rerun()

st.title("📡 Suivi des élections présidentielles au Sénégal 🇸🇳")
st.subheader("📈 Statistiques Globales")

# === KPIs globaux ===
candidat_df = st.session_state.votes_candidat_df
lieu_df = st.session_state.votes_lieu_df

total_votes = int(candidat_df["total_votes"].sum() if not candidat_df.empty else 0)
nb_lieux = lieu_df["lieu_vote"].nunique() if not lieu_df.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🗳️ Total des Votes", f"{total_votes:,}")
col2.metric("📍 Lieux de Vote", nb_lieux)


# Tabs principaux
tab1, tab2 = st.tabs(["📊 Résultats Globaux", "📈 Analyses détaillées"])

# -------------------------------
# 🟢 TAB 1 - Résultats Globaux
# -------------------------------
with tab1:
    #st.header("📊 Résultats Globaux")

    if not candidat_df.empty:
        df = candidat_df.sort_values("total_votes", ascending=False)
        df["pourcentage"] = (df["total_votes"] / total_votes * 100).round(2)

        st.subheader("📋 Voix de chaque candidat")
        st.dataframe(df[["candidat_complet", "total_votes", "pourcentage"]], use_container_width=True)

        st.subheader("📌 Répartition par tranche d'âge")
        age_df = st.session_state.votes_age_df
        if not age_df.empty:
            pie = alt.Chart(age_df).mark_arc().encode(
                theta="votes_par_age:Q",
                color="age_group:N",
                tooltip=["age_group:N", "votes_par_age:Q"]
            )
            st.altair_chart(pie, use_container_width=True)

        st.subheader("📌 Répartition par genre")
        genre_df = st.session_state.votes_genre_df
        if not genre_df.empty:
            pie = alt.Chart(genre_df).mark_arc().encode(
                theta="votes_par_sexe:Q",
                color="sexe:N",
                tooltip=["sexe:N", "votes_par_sexe:Q"]
            )
            st.altair_chart(pie, use_container_width=True)

        st.subheader("📍 Répartition par lieu de vote")
        if not lieu_df.empty:
            chart = alt.Chart(lieu_df).mark_bar().encode(
                x=alt.X("lieu_vote:N", sort='-y', title="Lieu"),
                y=alt.Y("votes_par_lieu:Q", title="Votes"),
                tooltip=["lieu_vote:N", "votes_par_lieu:Q"]
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
    else:
        st.info("En attente de données...")

# -------------------------------
# 🟣 TAB 2 - Analyses détaillées
# -------------------------------
with tab2:
    #st.header("📈 Analyses par Genre et Âge")

    st.subheader("⚖️ Votes par Genre et Candidat")
    genre_df = st.session_state.votes_genre_df
    if not genre_df.empty:
        bar_genre = alt.Chart(genre_df).mark_bar().encode(
            x=alt.X("candidat_complet:N", title="Candidat"),
            y=alt.Y("votes_par_sexe:Q", title="Nombre de votes"),
            color="sexe:N",
            tooltip=["candidat_complet", "sexe", "votes_par_sexe"]
        ).properties(height=400)
        st.altair_chart(bar_genre, use_container_width=True)

    st.subheader("👥 Votes par Tranche d'Âge et Candidat")
    age_df = st.session_state.votes_age_df
    if not age_df.empty:
        bar_age = alt.Chart(age_df).mark_bar().encode(
            x=alt.X("candidat_complet:N", title="Candidat"),
            y=alt.Y("votes_par_age:Q", title="Nombre de votes"),
            color="age_group:N",
            tooltip=["candidat_complet", "age_group", "votes_par_age"]
        ).properties(height=400)
        st.altair_chart(bar_age, use_container_width=True)