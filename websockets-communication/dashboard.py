import streamlit as st
import websocket
import threading
import queue
from streamlit.runtime.scriptrunner import add_script_run_ctx
import pandas as pd
import json
import ast
import altair as alt

st.set_page_config(layout="wide")

# Liste des candidats
CANDIDATES = ["Pape Mor", "Kany", "Assane", "Thiane", "Ndaraw"]

# Initialisation
if "votes_df" not in st.session_state:
    st.session_state.votes_df = pd.DataFrame({
        "candidate": CANDIDATES,
        "votes": [0 for _ in CANDIDATES]
    })

if "message_queue" not in st.session_state:
    st.session_state.message_queue = queue.Queue()

if "websocket_thread" not in st.session_state:
    st.session_state.websocket_thread = None

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

def update_votes_from_messages(df):
    while not st.session_state.message_queue.empty():
        message = st.session_state.message_queue.get()
        try:
            list_of_json_strings = ast.literal_eval(message)
            votes_list = [json.loads(item) for item in list_of_json_strings]

            for vote_data in votes_list:
                candidateName = vote_data.get("candidateName")
                count = vote_data.get("count", 0)
                if candidateName in df["candidate"].values:
                    df.loc[df["candidate"] == candidateName, "votes"] = count
        except Exception as e:
            print("Erreur de traitement :", e)
    return df

# === Thread WebSocket ===
if st.session_state.websocket_thread is None or not st.session_state.websocket_thread.is_alive():
    websocket_thread = threading.Thread(target=run_websocket, daemon=True)
    add_script_run_ctx(websocket_thread)
    websocket_thread.start()
    st.session_state.websocket_thread = websocket_thread

# === UI Streamlit ===
st.title("📊 Résultats de vote en temps réel")

# Bouton manuel 
if st.button("🔄 Rafraîchir les résultats"):
    st.session_state.votes_df = update_votes_from_messages(st.session_state.votes_df)

# Affichage tableau
st.dataframe(
    st.session_state.votes_df,
    column_config={
        "candidate": st.column_config.TextColumn("Candidat"),
        "votes": st.column_config.NumberColumn("Votes")
    },
    use_container_width=True
)

# Affichage graphique
chart = alt.Chart(st.session_state.votes_df).mark_bar().encode(
    x=alt.X("candidate:N", title="Candidat"),
    y=alt.Y("votes:Q", title="Nombre de votes"),
    color=alt.Color("candidate:N", legend=None)
).properties(
    width=700,
    height=400,
    title="Répartition des votes"
)

st.altair_chart(chart, use_container_width=True)