import streamlit as st
import pandas as pd
import plotly.express as px
import re  # Module pour chercher les codes postaux

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Dashboard IRVE", layout="wide")

# --- 0. GESTION DU CACHE (Pour éviter votre erreur KeyError) ---
if "clear_cache" not in st.session_state:
    st.session_state["clear_cache"] = False

# --- 1. FONCTION DE CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    # URL du fichier consolidé des bornes de recharge
    url = "https://www.data.gouv.fr/api/1/datasets/r/2729b192-40ab-4454-904d-735084dca3a3"

    
    try:
        # OPTIONS POUR ÉVITER LE BLOCAGE (Erreur 403)
        # On se fait passer pour un navigateur web
        storage_options = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        # Chargement (limité à 20000 lignes pour aller vite)
        df = pd.read_csv(url, sep=",", nrows=20000, storage_options=storage_options, on_bad_lines='skip')
        
        # MAPPING DES COLONNES (Pour standardiser les noms)
        cols_map = {
            'nom_operateur': 'Opérateur',
            'puissance_nominale': 'Puissance (kW)', 
            'consolidated_longitude': 'Longitude', 
            'consolidated_latitude': 'Latitude', 
            'code_insee_commune': 'Code_Commune', 
            'adresse_station': 'Adresse'
        }
        
        # On ne garde que les colonnes trouvées
        cols_presentes = [c for c in cols_map.keys() if c in df.columns]
        df = df[cols_presentes]
        df = df.rename(columns=cols_map)
        
        # NETTOYAGE DE BASE
        if 'Longitude' in df.columns and 'Latitude' in df.columns:
            df = df.dropna(subset=['Longitude', 'Latitude'])
            
        if 'Opérateur' in df.columns:
            df['Opérateur'] = df['Opérateur'].fillna("Opérateur Inconnu")
            
        if 'Adresse' in df.columns:
            df['Adresse'] = df['Adresse'].fillna("")

        # --- LOGIQUE INTELLIGENTE : DÉDUIRE LE DÉPARTEMENT ---
        def trouver_departement(row):
            # 1. Essai via Code Commune (s'il existe)
            if 'Code_Commune' in row and pd.notna(row['Code_Commune']):
                code = str(row['Code_Commune'])
                # Si le code ressemble à un code INSEE valide
                if len(code) >= 2 and code.isdigit():
                    return code[:2]
            
            # 2. Essai via Adresse (Regex cherche 5 chiffres consécutifs : le code postal)
            if 'Adresse' in row:
                # Cherche un motif de 5 chiffres entourés de frontières de mots
                match = re.search(r'\b(\d{5})\b', str(row['Adresse']))
                if match:
                    return match.group(1)[:2] # Retourne les 2 premiers chiffres
            
            return "Inconnu"

        # Application de la fonction
        df['Département'] = df.apply(trouver_departement, axis=1)
        
        # On retire les données inutilisables pour le filtre département
        df = df[df['Département'] != "Inconnu"]
        
        return df

    except Exception as e:
        st.error(f"Erreur technique lors du chargement : {e}")
        return pd.DataFrame()

# Chargement effectif
with st.spinner('Chargement et analyse des données en cours...'):
    df = load_data()

# Arrêt si échec
if df.empty:
    st.warning("Aucune donnée chargée. Vérifiez votre connexion internet.")
    st.stop()

# --- 2. INTERFACE DASHBOARD ---

st.title("⚡ Tableau de Bord : Bornes Électriques France")
st.markdown("Explorez les infrastructures de recharge (Données Data.gouv.fr)")
st.divider()

# --- 3. BARRE LATÉRALE (FILTRES) ---
st.sidebar.header("🔍 Filtres & Options")

# Bouton de secours pour votre erreur de cache
if st.sidebar.button("🔄 Recharger les données (Vider Cache)"):
    st.cache_data.clear()
    st.rerun()

# Filtre Département (Sécurisé)
if 'Département' in df.columns:
    liste_dep = sorted(df['Département'].unique())
    choix_dep = st.sidebar.selectbox("Choisir un Département :", ["Tous"] + liste_dep)
else:
    st.error("Colonne 'Département' manquante. Cliquez sur 'Recharger les données' ci-dessus.")
    choix_dep = "Tous"

# Filtre Puissance
max_p = int(df['Puissance (kW)'].max()) if 'Puissance (kW)' in df.columns else 250
min_power = st.sidebar.slider("Puissance Minimum (kW)", 0, max_p, 0)

# Application des filtres
df_filtered = df.copy()

if choix_dep != "Tous":
    df_filtered = df_filtered[df_filtered['Département'] == choix_dep]

if 'Puissance (kW)' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Puissance (kW)'] >= min_power]

# --- 4. INDICATEURS CLÉS (KPIs) ---
k1, k2, k3 = st.columns(3)
k1.metric("Bornes affichées", len(df_filtered))

moyenne = round(df_filtered['Puissance (kW)'].mean(), 1) if not df_filtered.empty else 0
k2.metric("Puissance Moyenne", f"{moyenne} kW")

top_op = df_filtered['Opérateur'].mode()[0] if not df_filtered.empty else "-"
k3.metric("Opérateur Principal", top_op)

st.divider()

# --- 5. GRAPHIQUES ---
col_map, col_stats = st.columns([2, 1])

with col_map:
    st.subheader("📍 Carte Interactive")
    if not df_filtered.empty:
        fig_map = px.scatter_mapbox(
            df_filtered, 
            lat="Latitude", lon="Longitude", 
            color="Puissance (kW)",
            hover_name="Opérateur",
            hover_data={"Adresse": True, "Latitude": False, "Longitude": False},
            zoom=8 if choix_dep != "Tous" else 5,
            mapbox_style="open-street-map",
            color_continuous_scale="Teal",
            height=500
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Aucune borne ne correspond à ces critères.")

with col_stats:
    st.subheader("🏆 Top 10 Opérateurs")
    if not df_filtered.empty:
        top_data = df_filtered['Opérateur'].value_counts().head(10).reset_index()
        top_data.columns = ['Opérateur', 'Nombre de bornes']
        
        fig_bar = px.bar(
            top_data, 
            x='Nombre de bornes', 
            y='Opérateur', 
            orientation='h',
            text_auto=True
        )
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# --- 6. DONNÉES BRUTES ---
with st.expander("📂 Voir le tableau de données"):
    st.dataframe(df_filtered)