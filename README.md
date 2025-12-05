# projet_python

Petit tableau de bord Streamlit affichant les bornes de recharge électriques (IRVE) en France.

**Fichiers importants**
 - `app.py` : application Streamlit principale (chargement, filtres, cartes, graphiques).
 - `requirements.txt` : dépendances requises (`streamlit`, `pandas`, `plotly`).

**Prérequis**
 - Python 3.8+ installé.
 - `pip` disponible.

**Installation (local / conteneur)**
 1. Depuis la racine du projet, installez les dépendances :

 ```bash
 pip3 install -r requirements.txt
 ```

 2. Lancer l'application localement :

 ```bash
 streamlit run app.py
 ```

 Ouvrez l'URL indiquée par Streamlit (souvent `http://localhost:8501`).

**Fonctionnalités**
 - Téléchargement et mise en cache des données IRVE depuis data.gouv.fr.
 - Filtrage par département et puissance de charge.
 - Carte interactive des bornes (Plotly + Mapbox open-street-map).
 - Graphique des top opérateurs et tableau des données filtrées.

**Détails d'implémentation**
 - La fonction `load_data()` (dans `app.py`) utilise `pandas.read_csv` pour charger un extrait (nrows=20000) et applique un mapping des colonnes présentes.
 - Le département est déduit soit depuis le code INSEE (`code_insee_commune`), soit depuis l'adresse (regex cherchant un code postal à 5 chiffres).
 - `st.cache_data` est utilisé pour mettre en cache le chargement des données.

**Dépannage**
 - Erreur `ModuleNotFoundError` pour `plotly.express` : exécuter `pip3 install -r requirements.txt`.
 - Si le chargement échoue (403 ou autre), vérifiez la connectivité et que l'URL source est accessible depuis votre environnement.
 - Pour vider le cache manuellement lors de tests, utilisez le bouton `Recharger les données (Vider Cache)` dans la barre latérale de l'app.

**Déploiement (Streamlit Cloud / autre)**
 - Assurez-vous que `requirements.txt` est présent à la racine du dépôt ; Streamlit Cloud installera automatiquement les dépendances.
 - Poussez sur GitHub puis créez une app sur Streamlit Cloud en pointant vers ce repo/branche.

**Commandes utiles**
 - Vérifier la version de Plotly :

 ```bash
 python3 -c "import plotly.express as px; print('plotly', px.__version__)"
 ```

**Remarques**
 - Les noms de colonnes du dataset public peuvent changer ; `app.py` tente de détecter et de renommer les colonnes présentes.
 - Pour une utilisation en production, envisagez de persister les données dans un cache externe ou un petit stockage pour éviter de télécharger le fichier à chaque redémarrage.

Si vous voulez, je peux :
 - exécuter l'installation des dépendances ici et tester l'import de `plotly.express` ; ou
 - créer un petit script de tests automatisés pour valider l'environnement.


© Projet généré — instructions d'utilisation en français.
# projet_python
