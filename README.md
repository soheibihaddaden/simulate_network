# Interpréteur de topologie réseau (Streamlit)

Cette application permet de construire et visualiser une topologie réseau (nœuds, liens, latences, graphe orienté / non orienté) via une interface Streamlit avec une console de commandes intégrée.

## 1. Utilisation en ligne (Streamlit Cloud)

Vous pouvez utiliser l'application directement dans votre navigateur, sans rien installer, via Streamlit Community Cloud :

- Ouvrez l'URL : `https://<ton-user>-simulate_network.streamlit.app`  (remplacez par l'URL réelle de votre déploiement).

Dans cette version en ligne, utilisez la **console avancée** dans l'interface pour taper des commandes comme :

- `add-node R1`
- `add-link R1 R2 10`
- `list-nodes`
- `list-links`
- `simulate-ping R1 R3`

Toutes les commandes sont décrites dans la section "Console avancée" de l'interface.

## 2. Utilisation en local (avec CLI + interface)

### 2.1 Installation

git clone https://github.com/soheibihaddaden/simulate_network.git
cd simulate_network

python -m venv venv
source venv/bin/activate # Windows : venv\Scripts\activate

pip install -r requirements.txt
chmod +x run_network.sh


### 2.2 Lancement
./run_network.sh


- Le script lance **Streamlit** en arrière-plan (`app.py`) et ouvre le serveur local sur `http://localhost:8501`.  
- Dans le **terminal**, un interpréteur (`repl`) apparaît avec un prompt `>` : tapez directement les commandes, par exemple :

add-node R1
add-node R2
add-link R1 R2 10
list-links
simulate-ping R1 R2
quit


La topologie affichée dans Streamlit et l'état manipulé par le terminal sont synchronisés via un fichier d'état partagé.

### 2.3 Remise à zéro

Vous pouvez :

- cliquer sur **"Nouveau projet (réinitialiser)"** dans l'interface Streamlit pour vider complètement la topologie,  
- ou taper `quit` dans le REPL : en quittant, la topologie est réinitialisée pour la prochaine session.

## 3. Technologies utilisées

- [Streamlit](https://streamlit.io/) pour l'interface web.  
- [NetworkX](https://networkx.org/) pour la modélisation du graphe réseau.  
- [Matplotlib](https://matplotlib.org/) pour le dessin de la topologie.  
- [Typer](https://typer.tiangolo.com/) pour la CLI locale.





