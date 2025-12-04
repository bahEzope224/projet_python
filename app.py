
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Moniteur Bornes Électriques", layout="wide")

@st.cache_data # Cette commande garde les données en mémoire pour aller plus vite
def load_data():
    # URL directe du fichier CSV sur data.gouv.fr
    url = "https://www.data.gouv.fr/api/1/datasets/r/2729b192-40ab-4454-904d-735084dca3a3"
    
    # Chargement (on limite à 10000 lignes pour la démo si le fichier est trop lourd, sinon enlever nrows)
    df = pd.read_csv(url, sep=",", nrows=20000) 
    
    # --- NETTOYAGE ---
    # On garde uniquement les colonnes utiles pour l'utilisateur
    cols_utiles = ['nom_operateur', 'puissance_nominale', 'consolidated_longitude', 'consolidated_latitude', 'code_insee_commune', 'adresse_station']
    df = df[cols_utiles]
    
    # Renommer pour que ce soit lisible
    df.columns = ['Opérateur', 'Puissance (kW)', 'Longitude', 'Latitude', 'Code_Commune', 'Adresse']
    
    # Nettoyage des valeurs manquantes critiques
    df = df.dropna(subset=['Longitude', 'Latitude'])
    df['Opérateur'] = df['Opérateur'].fillna("Opérateur Inconnu")
    
    # Extraction du département (les 2 premiers chiffres du code commune)
    df['Département'] = df['Code_Commune'].astype(str).str[:2]
    
    return df


# Chargement des données avec un message d'attente
with st.spinner('Récupération des données sur data.gouv.fr...'):
    df = load_data()


# Titre et explications simples
st.title("Tableau de Bord : Bornes de Recharge Électrique")
st.markdown("""
Bienvenue. Ce tableau de bord vous permet d'analyser la répartition des bornes de recharge en France.
**Utilisez le menu à gauche** pour filtrer les résultats.
""")

st.divider()

st.sidebar.header("🔍 Filtres")

# Filtre par Département
liste_dep = sorted(df['Département'].unique())
choix_dep = st.sidebar.selectbox("Choisir un département :", ["Tous"] + liste_dep)

# Filtre par Puissance min
min_power = st.sidebar.slider("Puissance minimum (kW)", 0, int(df['Puissance (kW)'].max()), 0)

# Application des filtres
df_filtered = df[df['Puissance (kW)'] >= min_power]
if choix_dep != "Tous":
    df_filtered = df_filtered[df_filtered['Département'] == choix_dep]

# Affichage en colonnes pour un effet "Dashboard"
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.metric(label="Bornes trouvées", value=f"{len(df_filtered)}")
with kpi2:
    puissance_moyenne = round(df_filtered['Puissance (kW)'].mean(), 1)
    st.metric(label="Puissance Moyenne", value=f"{puissance_moyenne} kW")
with kpi3:
    top_op = df_filtered['Opérateur'].mode()[0] if not df_filtered.empty else "N/A"
    st.metric(label="Opérateur Dominant", value=top_op)

st.divider()


col_graph1, col_graph2 = st.columns([2, 1])

# Graphique 1 : La Carte (Indispensable pour des données géographiques)
with col_graph1:
    st.subheader("📍 Carte des bornes")
    if not df_filtered.empty:
        fig_map = px.scatter_mapbox(
            df_filtered, 
            lat="Latitude", 
            lon="Longitude", 
            color="Puissance (kW)",
            hover_name="Opérateur",
            hover_data=["Adresse", "Puissance (kW)"],
            zoom=8 if choix_dep != "Tous" else 5,
            mapbox_style="open-street-map",
            color_continuous_scale=px.colors.cyclical.IceFire,
            height=500
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Aucune donnée pour ces filtres.")

# Graphique 2 : Répartition par Opérateur (Top 10)
with col_graph2:
    st.subheader("📊 Top 10 Opérateurs")
    if not df_filtered.empty:
        top_operators = df_filtered['Opérateur'].value_counts().head(10).reset_index()
        top_operators.columns = ['Opérateur', 'Nombre']
        
        fig_bar = px.bar(
            top_operators, 
            x='Nombre', 
            y='Opérateur', 
            orientation='h',
            text_auto=True,
            color='Nombre'
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

with st.expander("Voir les données détaillées (Tableau)"):
    st.dataframe(df_filtered)