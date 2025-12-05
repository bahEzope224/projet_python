import streamlit as st
import pandas as pd
import plotly.express as px
import re  # Module pour chercher les codes postaux

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Dashboard IRVE", layout="wide")

# --- 0. GESTION DU CACHE ---
if "clear_cache" not in st.session_state:
    st.session_state["clear_cache"] = False

# --- 1. FONCTION DE CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    # URL stable
    url = "https://www.data.gouv.fr/api/1/datasets/r/2729b192-40ab-4454-904d-735084dca3a3"
    
    try:
        # User-Agent pour éviter le blocage 403
        storage_options = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        # Chargement
        df = pd.read_csv(url, sep=",", nrows=20000, storage_options=storage_options, on_bad_lines='skip')
        
        # Mapping des colonnes
        cols_map = {
            'nom_operateur': 'Opérateur',
            'puissance_nominale': 'Puissance (kW)', 
            'consolidated_longitude': 'Longitude', 
            'consolidated_latitude': 'Latitude', 
            'code_insee_commune': 'Code_Commune', 
            'adresse_station': 'Adresse'
        }
        
        # Sélection et renommage
        cols_presentes = [c for c in cols_map.keys() if c in df.columns]
        df = df[cols_presentes]
        df = df.rename(columns=cols_map)
        
        # Nettoyage de base
        if 'Longitude' in df.columns and 'Latitude' in df.columns:
            df = df.dropna(subset=['Longitude', 'Latitude'])
            
        if 'Opérateur' in df.columns:
            df['Opérateur'] = df['Opérateur'].fillna("Opérateur Inconnu")
            
        if 'Adresse' in df.columns:
            df['Adresse'] = df['Adresse'].fillna("")

        # --- LOGIQUE INTELLIGENTE ---
        def trouver_code_postal(row):
            # 1. Cherche 5 chiffres dans l'adresse
            if 'Adresse' in row:
                match = re.search(r'\b(\d{5})\b', str(row['Adresse']))
                if match:
                    return match.group(1)
            
            # 2. Sinon utilise Code_Commune
            if 'Code_Commune' in row and pd.notna(row['Code_Commune']):
                code = str(row['Code_Commune'])
                if len(code) == 5 and code.isdigit():
                    return code
            return "Inconnu"

        # Calculs
        df['Code_Postal'] = df.apply(trouver_code_postal, axis=1)
        df['Département'] = df['Code_Postal'].apply(lambda x: x[:2] if x != "Inconnu" else "Inconnu")
        
        # Nettoyage des lignes sans département
        df = df[df['Département'] != "Inconnu"]
        
        # --- SUPPRESSION DE LA COLONNE CODE COMMUNE ---
        # Maintenant qu'on a fini les calculs, on supprime cette colonne pour ne pas polluer l'affichage
        if 'Code_Commune' in df.columns:
            df = df.drop(columns=['Code_Commune'])
        
        return df

    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return pd.DataFrame()

# Chargement
with st.spinner('Chargement et analyse des données...'):
    df = load_data()

if df.empty:
    st.warning("Aucune donnée chargée.")
    st.stop()

# --- 2. INTERFACE DASHBOARD ---

st.title("⚡ Tableau de Bord : Bornes Électriques France")
st.markdown("Explorez les infrastructures de recharge (Données Data.gouv.fr)")
st.divider()

# --- 3. FILTRES ---
st.sidebar.header("🔍 Filtres & Options")

if st.sidebar.button("🔄 Recharger les données (Vider Cache)"):
    st.cache_data.clear()
    st.rerun()

if 'Département' in df.columns:
    liste_dep = sorted(df['Département'].unique())
    choix_dep = st.sidebar.selectbox("Département :", ["Tous"] + liste_dep)
else:
    choix_dep = "Tous"

max_p = int(df['Puissance (kW)'].max()) if 'Puissance (kW)' in df.columns else 250
min_power = st.sidebar.slider("Puissance Min (kW)", 0, max_p, 0)

# Application Filtres
df_filtered = df.copy()

if choix_dep != "Tous":
    df_filtered = df_filtered[df_filtered['Département'] == choix_dep]

if 'Puissance (kW)' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Puissance (kW)'] >= min_power]

# --- 4. KPIs ---
k1, k2, k3 = st.columns(3)
k1.metric("Bornes", len(df_filtered))
moy = round(df_filtered['Puissance (kW)'].mean(), 1) if not df_filtered.empty else 0
k2.metric("Puissance Moyenne", f"{moy} kW")
top = df_filtered['Opérateur'].mode()[0] if not df_filtered.empty else "-"
k3.metric("Opérateur Principal", top)

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
            # On affiche bien le Code Postal ici
            hover_name="Opérateur",
            hover_data={"Adresse": True, "Code_Postal": True, "Latitude": False, "Longitude": False},
            zoom=8 if choix_dep != "Tous" else 5,
            mapbox_style="open-street-map",
            color_continuous_scale="Teal",
            height=500
        )
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.info("Aucune donnée.")

with col_stats:
    st.subheader("🏆 Top Opérateurs")
    if not df_filtered.empty:
        top_data = df_filtered['Opérateur'].value_counts().head(10).reset_index()
        top_data.columns = ['Opérateur', 'Nombre']
        fig_bar = px.bar(top_data, x='Nombre', y='Opérateur', orientation='h', text_auto=True)
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

# --- 6. TABLEAU DE DONNÉES ---
with st.expander("📂 Voir le tableau de données"):
    # On définit l'ordre d'affichage (Code_Postal est inclus, mais plus Code_Commune)
    cols_ordre = ['Opérateur', 'Puissance (kW)', 'Code_Postal', 'Département', 'Adresse', 'Longitude', 'Latitude']
    cols_finales = [c for c in cols_ordre if c in df_filtered.columns]
    
    st.dataframe(df_filtered[cols_finales])