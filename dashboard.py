import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import time

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Élections Sénégal - Tableau de Bord en Temps Réel",
    page_icon="🇸🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour se connecter à la base de données
@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=os.environ.get("DATABASE_PORT", 5432),
        user=os.environ.get("DATABASE_USER", "papamor"),
        password=os.environ.get("DATABASE_PASSWORD", "papamor"),
        database=os.environ.get("DATABASE_NAME", "ElectionDB")
    )

# Fonction pour exécuter une requête et retourner un DataFrame
def query_to_dataframe(query):
    try:
        conn = get_connection()
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Erreur lors de la requête : {e}")
        return pd.DataFrame()

# Titre principal
st.title("Tableau de Bord des Élections du Sénégal")
st.markdown("Visualisation des résultats des élections présidentielles en temps réel")

# Création des onglets
tab1, tab2, tab3, tab4 = st.tabs(["📊 Résultats Généraux", "🗺️ Votes par Région", "👥 Démographie", "📈 Tendances"])

# Onglet 1 : Résultats Généraux
with tab1:
    st.header("Résultats Généraux")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Récupération des résultats généraux
        results_df = query_to_dataframe("""
            SELECT candidat_prenom, candidat_nom, total_votes 
            FROM vote_counts 
            ORDER BY total_votes DESC
        """)
        
        if not results_df.empty:
            # Calcul du total des votes
            total_votes = results_df['total_votes'].sum()
            
            # Ajout des pourcentages
            results_df['pourcentage'] = (results_df['total_votes'] / total_votes * 100).round(2)
            results_df['candidat'] = results_df['candidat_prenom'] + ' ' + results_df['candidat_nom']
            
            # Création du graphique
            fig = px.bar(
                results_df,
                x='candidat',
                y='total_votes',
                text='pourcentage',
                labels={'candidat': 'Candidat', 'total_votes': 'Nombre de votes'},
                title=f'Résultats des élections (Total: {total_votes} votes)',
                color='candidat',
                height=500
            )
            
            fig.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun résultat disponible pour le moment. Les données commenceront à apparaître dès que les premiers votes seront comptabilisés.")
    
    with col2:
        if not results_df.empty:
            # Affichage du podium
            st.subheader("Podium Actuel")
            
            top_candidates = results_df.head(3)
            for i, (_, row) in enumerate(top_candidates.iterrows()):
                medal = ["🥇", "🥈", "🥉"][i]
                st.markdown(f"""
                    <div style='background-color:#f0f2f6;color:#000000;padding:10px;border-radius:5px;margin-bottom:10px'>
                        <h3 style='margin:0'>{medal} {row['candidat']}</h3>
                        <p style='margin:0'><strong>{row['total_votes']}</strong> votes ({row['pourcentage']}%)</p>
                    </div>
                """, unsafe_allow_html=True)

            # Affichage du tableau des résultats
            st.subheader("Tableau des résultats")
            st.dataframe(
                results_df[['candidat', 'total_votes', 'pourcentage']].rename(
                    columns={'candidat': 'Candidat', 'total_votes': 'Votes', 'pourcentage': 'Pourcentage (%)'})
            )

# Onglet 2 : Votes par région
with tab2:
    st.header("Répartition des votes par région")
    
    # Récupération des données par lieu
    lieu_df = query_to_dataframe("""
        SELECT candidat_prenom, candidat_nom, lieu_vote, votes_par_lieu 
        FROM votes_par_lieu 
        ORDER BY votes_par_lieu DESC
    """)
    
    if not lieu_df.empty:
        lieu_df['candidat'] = lieu_df['candidat_prenom'] + ' ' + lieu_df['candidat_nom']
        
        # Création d'un selectbox pour choisir un candidat spécifique ou voir tous les candidats
        candidats_list = ['Tous les candidats'] + list(lieu_df['candidat'].unique())
        selected_candidat = st.selectbox("Sélectionner un candidat", candidats_list)
        
        if selected_candidat == 'Tous les candidats':
            # Agréger les votes par lieu pour tous les candidats
            lieu_agg = lieu_df.groupby('lieu_vote')['votes_par_lieu'].sum().reset_index()
            fig = px.bar(
                lieu_agg,
                x='lieu_vote',
                y='votes_par_lieu',
                labels={'lieu_vote': 'Région', 'votes_par_lieu': 'Nombre de votes'},
                title='Votes par région (tous candidats confondus)',
                color='lieu_vote',
                height=500
            )
        else:
            # Filtrer pour le candidat sélectionné
            candidat_lieu_df = lieu_df[lieu_df['candidat'] == selected_candidat]
            fig = px.bar(
                candidat_lieu_df,
                x='lieu_vote',
                y='votes_par_lieu',
                labels={'lieu_vote': 'Région', 'votes_par_lieu': 'Nombre de votes'},
                title=f'Votes par région pour {selected_candidat}',
                color='lieu_vote',
                height=500
            )
            
        st.plotly_chart(fig, use_container_width=True)
        
        # Tableau des régions avec le candidat leader
        st.subheader("Leader par région")
        leader_by_region = lieu_df.sort_values('votes_par_lieu', ascending=False).drop_duplicates('lieu_vote')
        leader_df = leader_by_region[['lieu_vote', 'candidat', 'votes_par_lieu']].rename(
            columns={'lieu_vote': 'Région', 'candidat': 'Candidat en tête', 'votes_par_lieu': 'Votes'}
        )
        st.dataframe(leader_df.sort_values('Région'))
    else:
        st.info("Aucune donnée disponible par région pour le moment.")

# Onglet 3 : Démographie
with tab3:
    st.header("Analyse démographique des votes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Récupération des votes par tranche d'âge
        age_df = query_to_dataframe("""
            SELECT candidat_prenom, candidat_nom, age_group, votes_par_age 
            FROM votes_par_age
            ORDER BY age_group, votes_par_age DESC
        """)
        
        if not age_df.empty:
            age_df['candidat'] = age_df['candidat_prenom'] + ' ' + age_df['candidat_nom']
            
            # Assurer un ordre cohérent des tranches d'âge
            age_order = ["18-25", "26-35", "36-45", "46-60", "60+"]
            age_df['age_group'] = pd.Categorical(age_df['age_group'], categories=age_order, ordered=True)
            age_df = age_df.sort_values('age_group')
            
            fig = px.bar(
                age_df,
                x='age_group',
                y='votes_par_age',
                color='candidat',
                labels={'age_group': 'Tranche d\'âge', 'votes_par_age': 'Nombre de votes', 'candidat': 'Candidat'},
                title='Votes par tranche d\'âge',
                barmode='group',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible par tranche d'âge pour le moment.")
    
    with col2:
        # Récupération des votes par sexe
        sexe_df = query_to_dataframe("""
            SELECT candidat_prenom, candidat_nom, sexe, votes_par_sexe
            FROM votes_par_sexe
            ORDER BY sexe, votes_par_sexe DESC
        """)
        
        if not sexe_df.empty:
            sexe_df['candidat'] = sexe_df['candidat_prenom'] + ' ' + sexe_df['candidat_nom']
            
            # Mapper les codes de sexe à des libellés plus explicites
            sexe_df['sexe'] = sexe_df['sexe'].map({'M': 'Hommes', 'F': 'Femmes'})
            
            fig = px.pie(
                sexe_df,
                values='votes_par_sexe',
                names='candidat',
                facet_col='sexe',
                title='Répartition des votes par sexe',
                height=400
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée disponible par sexe pour le moment.")

# Onglet 4 : Tendances
with tab4:
    st.header("Tendances en temps réel")
    st.markdown("""
    Les graphiques ci-dessous se mettent à jour automatiquement pour montrer l'évolution des votes.
    Rafraîchir la page pour voir les dernières données.
    """)
    
    # Ici, on pourrait ajouter une visualisation de l'évolution des votes dans le temps
    # Pour l'instant, sans suivi temporel dans la base, on affiche juste une visualisation différente
    
    results_df = query_to_dataframe("""
        SELECT candidat_prenom, candidat_nom, total_votes 
        FROM vote_counts 
        ORDER BY total_votes DESC
    """)
    
    if not results_df.empty:
        results_df['candidat'] = results_df['candidat_prenom'] + ' ' + results_df['candidat_nom']
        total_votes = results_df['total_votes'].sum()
        results_df['pourcentage'] = (results_df['total_votes'] / total_votes * 100).round(2)
        
        fig = go.Figure(go.Pie(
            labels=results_df['candidat'],
            values=results_df['total_votes'],
            hole=.4,
            textinfo='label+percent',
            insidetextorientation='radial'
        ))
        
        fig.update_layout(
            title_text=f'Répartition des {total_votes} votes',
            annotations=[dict(text=f'{total_votes} votes', x=0.5, y=0.5, font_size=20, showarrow=False)]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucune donnée disponible pour le moment.")

# Mise à jour automatique
st.sidebar.title("Informations")
st.sidebar.info("""
Ce tableau de bord présente les résultats des élections présidentielles du Sénégal en temps réel.
Les données sont mises à jour automatiquement à mesure que les votes sont comptabilisés.
""")

last_update = time.strftime("%d/%m/%Y à %H:%M:%S")
st.sidebar.write(f"Dernière mise à jour: {last_update}")

# Ajout d'un bouton de rafraîchissement
if st.sidebar.button("Rafraîchir les données"):
    st.rerun()