import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx

from network_model import Network
from commands import handle_command
from state import load_network, save_network


# =========================
#   Config page large
# =========================

st.set_page_config(page_title="Interpréteur réseau", layout="wide")

# --- CSS pour le bloc de topologie à droite (fond + bordure) ---
st.markdown(
    """
    <style>
    /* Container avec key="topology_box" */
    .st-key-topology_box {
        background-color: #f9fafb;          /* fond gris clair */
        border: 2px solid #4b9cd3;          /* bordure bleue */
        border-radius: 12px;                /* coins arrondis */
        padding: 16px 20px 10px 20px;       /* marges internes */
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);  /* petite ombre */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
#   Initialisation réseau
# =========================

if "network" not in st.session_state:
    # Démarrer toujours avec un graphe vide pour l'UI
    st.session_state.network = Network(directed=False)
    # Et écraser l'ancien fichier d'état si tu veux vraiment repartir de zéro
    from state import save_network
    save_network(st.session_state.network)


if "command_history" not in st.session_state:
    st.session_state.command_history = []

if "show_console" not in st.session_state:
    st.session_state.show_console = False

net: Network = st.session_state.network

# =========================
#   Layout 2 colonnes
# =========================

col_left, col_right = st.columns([1.2, 2])


with col_left:
    st.title("Interpréteur réseau (Streamlit)")

    # Bouton pour recharger l'état modifié par le CLI
    if st.button("Recharger l'état depuis le terminal"):
        st.session_state.network = load_network()
        net = st.session_state.network
        st.success("État rechargé depuis le CLI.")

    # ------ BOUTON CONSOLE EN HAUT ------
    def open_console():
        st.session_state.show_console = True

    def close_console():
        st.session_state.show_console = False

    if not st.session_state.show_console:
        st.button("Afficher la console avancée", on_click=open_console)
    else:
        st.button("✕ Fermer la console avancée", on_click=close_console)
    

    # ------ CONSOLE AVANCÉE (si ouverte) ------
    if st.session_state.show_console:
        st.subheader("Console avancée")

        st.markdown(
            """
Commandes disponibles (exemples) :
- `list-nodes`
- `list-links`
- `show-node R1`
- `simulate-ping R1 R3`
- `add-node R5`
- `add-link R2 R5 10`
- `delete-node R1`
- `delete-link R1 R2`
- `update-link R1 R2 15`
- `rename-node R1 R10`
- `reset-network`
- `set-directed`
- `set-undirected`
- `help`
"""
        )

        cmd = st.text_input(
            "Commande",
            placeholder="Ex: list-nodes, simulate-ping R1 R3",
            key="console_cmd",
        )

        if st.button("Exécuter la commande"):
            if cmd:
                output = handle_command(net, cmd)
                # après une commande qui peut modifier le graphe, on sauvegarde
                save_network(net)
                st.session_state.command_history.append(f"> {cmd}\n{output}")

        st.markdown("**Historique des commandes**")
        history_text = "\n\n".join(st.session_state.command_history)
        st.text_area("Historique", value=history_text, height=200)

        st.markdown("---")

    # ------ TEXTE D'INTRO & FORMULAIRES ------
    st.markdown(
        """
Tu peux utiliser les formulaires ci-dessous pour construire ta topologie réseau
(nœuds, liens, mode orienté / non orienté).
"""
    )

    st.subheader("Édition du graphe")

    # --- Choix graphe orienté / non orienté ---
    mode = st.radio(
        "Type de graphe",
        options=["Non orienté", "Orienté"],
        index=1 if net.directed else 0,
    )

    if mode == "Orienté" and not net.directed:
        net.set_directed(True)
        save_network(net)
        st.info("Passage en graphe orienté.")
    elif mode == "Non orienté" and net.directed:
        net.set_directed(False)
        save_network(net)
        st.info("Passage en graphe non orienté.")

    st.markdown("---")

    # --- Formulaire ajout de nœud ---
    st.markdown("**Ajouter un nœud**")

    with st.form("add_node_form"):
        new_node = st.text_input("Nom du nouveau nœud (ex: R5)", key="new_node_name")
        submitted_node = st.form_submit_button("Ajouter le nœud")
        if submitted_node:
            if not new_node:
                st.warning("Veuillez saisir un nom de nœud.")
            else:
                if net.add_node(new_node):
                    save_network(net)
                    st.success(f"Nœud ajouté : {new_node}")
                else:
                    st.warning(f"Nœud déjà existant : {new_node}")

    st.markdown("**Ajouter un lien**")

    nodes = net.list_nodes()
    if len(nodes) < 2:
        st.info("Il faut au moins 2 nœuds pour créer un lien.")
    else:
        with st.form("add_link_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                n1 = st.selectbox("Nœud source", nodes, key="link_src")

            with col2:
                n2 = st.selectbox("Nœud destination", nodes, key="link_dst")

            with col3:
                latency = st.number_input(
                    "Latence (ms)",
                    min_value=1,
                    value=10,
                    step=1,
                    key="link_latency",
                )

            submitted_link = st.form_submit_button("Ajouter le lien")
            if submitted_link:
                if n1 == n2:
                    st.error("Source et destination doivent être différentes.")
                else:
                    if net.add_link(n1, n2, latency):
                        save_network(net)
                        arrow = "->" if net.directed else "--"
                        st.success(
                            f"Lien ajouté : {n1} {arrow} {n2} (latence={latency} ms)"
                        )
                    else:
                        st.error(
                            f"Impossible d'ajouter le lien, vérifiez que {n1} et {n2} existent."
                        )

    st.markdown("---")

    # ---------- Gestion des nœuds et liens ----------
    st.subheader("Gestion des nœuds et liens")

    # Supprimer un nœud
    st.markdown("**Supprimer un nœud**")
    if nodes:
        with st.form("delete_node_form"):
            node_to_delete = st.selectbox(
                "Nœud à supprimer", nodes, key="delete_node_sel"
            )
            submitted_del_node = st.form_submit_button("Supprimer ce nœud")
            if submitted_del_node:
                if net.delete_node(node_to_delete):
                    save_network(net)
                    st.success(f"Nœud supprimé : {node_to_delete}")
                else:
                    st.error("Suppression impossible.")
    else:
        st.info("Aucun nœud à supprimer.")

    # Supprimer un lien
    st.markdown("**Supprimer un lien**")
    links = net.list_links()
    if links:
        arrow_sym = "->" if net.directed else "--"
        link_labels = [f"{u} {arrow_sym} {v}" for (u, v, _data) in links]
        with st.form("delete_link_form"):
            link_label = st.selectbox(
                "Lien à supprimer", link_labels, key="delete_link_sel"
            )
            submitted_del_link = st.form_submit_button("Supprimer ce lien")
            if submitted_del_link:
                idx = link_labels.index(link_label)
                u, v, _ = links[idx]
                if net.delete_link(u, v):
                    save_network(net)
                    st.success(f"Lien supprimé : {link_label}")
                else:
                    st.error("Suppression de lien impossible.")
    else:
        st.info("Aucun lien à supprimer.")

    # Modifier la latence d'un lien
    st.markdown("**Modifier la latence d'un lien**")
    links = net.list_links()
    if links:
        arrow_sym = "->" if net.directed else "--"
        link_labels = [f"{u} {arrow_sym} {v}" for (u, v, _data) in links]
        with st.form("edit_link_form"):
            link_label = st.selectbox(
                "Lien à modifier", link_labels, key="edit_link_sel"
            )
            new_latency = st.number_input(
                "Nouvelle latence (ms)",
                min_value=1,
                value=10,
                step=1,
                key="edit_link_latency",
            )
            submitted_edit_link = st.form_submit_button("Modifier la latence")
            if submitted_edit_link:
                idx = link_labels.index(link_label)
                u, v, _ = links[idx]
                if net.update_link_latency(u, v, int(new_latency)):
                    save_network(net)
                    st.success(
                        f"Latence du lien {link_label} mise à jour à {int(new_latency)} ms."
                    )
                else:
                    st.error("Modification de latence impossible.")
    else:
        st.info("Aucun lien à modifier.")

    # Renommer un nœud
    st.markdown("**Renommer un nœud**")
    nodes = net.list_nodes()
    if nodes:
        with st.form("rename_node_form"):
            old_name = st.selectbox(
                "Nœud à renommer", nodes, key="rename_node_sel"
            )
            new_name = st.text_input("Nouveau nom", key="rename_node_new")
            submitted_rename = st.form_submit_button("Renommer")
            if submitted_rename:
                if not new_name:
                    st.warning("Veuillez saisir un nouveau nom.")
                else:
                    if net.rename_node(old_name, new_name):
                        save_network(net)
                        st.success(f"Nœud renommé : {old_name} -> {new_name}")
                    else:
                        st.error("Renommage impossible (nom déjà utilisé ?).")
    else:
        st.info("Aucun nœud à renommer.")

# ===== Colonne droite : topologie =====
with col_right:
    with st.container(key="topology_box"):
        top_col1, top_col2 = st.columns([3, 1])

        with top_col1:
            st.subheader("Topologie réseau")
        with top_col2:
            if st.button("Réinitialiser", key="reset_topology_btn"):
                net.reset()
                save_network(net)
                st.warning("Topologie réinitialisée.")

        fig, ax = plt.subplots()

        if net.graph.number_of_nodes() == 0:
            ax.text(
                0.5,
                0.5,
                "Aucune topologie pour le moment.\nAjoute des nœuds et des liens à gauche.",
                ha="center",
                va="center",
                fontsize=12,
            )
            ax.axis("off")
        else:
            # Mise en page simple et stable en cercle
            pos = nx.circular_layout(net.graph)

            nx.draw_networkx_nodes(net.graph, pos, ax=ax, node_color="lightblue")
            nx.draw_networkx_labels(net.graph, pos, ax=ax, font_size=10)

            if net.directed:
                nx.draw_networkx_edges(
                    net.graph,
                    pos,
                    ax=ax,
                    arrows=True,
                    arrowstyle="->",
                    arrowsize=20,
                    connectionstyle="arc3,rad=0.1",
                )
            else:
                nx.draw_networkx_edges(net.graph, pos, ax=ax)

            # On prépare deux dictionnaires de labels :
            # - forward_labels : pour un sens
            # - backward_labels : pour le sens inverse, légèrement décalé
            forward_labels = {}
            backward_labels = {}

            for u, v, data in net.graph.edges(data=True):
                label = f"{data.get('latency', '')} ms"

                if net.directed and net.graph.has_edge(v, u):
                    if (v, u) in forward_labels:
                        backward_labels[(u, v)] = label
                    else:
                        forward_labels[(u, v)] = label
                else:
                    forward_labels[(u, v)] = label

            # Première passe : labels "forward" (position un peu après le milieu)
            nx.draw_networkx_edge_labels(
                net.graph,
                pos,
                edge_labels=forward_labels,
                ax=ax,
                font_size=8,
                rotate=False,
                label_pos=0.6,
            )

            # Deuxième passe : labels "backward" (position un peu avant le milieu)
            if backward_labels:
                nx.draw_networkx_edge_labels(
                    net.graph,
                    pos,
                    edge_labels=backward_labels,
                    ax=ax,
                    font_size=8,
                    rotate=False,
                    label_pos=0.4,
                )

            ax.axis("off")

        st.pyplot(fig)
