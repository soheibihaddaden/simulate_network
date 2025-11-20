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
    /* Appliquer le même style aux 3 conteneurs */
    .st-key-topology_box,
    .st-key-topology_box_analyse,
    .st-key-topology_box_console {
        background-color: #f9fafb;
        border: 2px solid #4b9cd3;
        border-radius: 12px;
        padding: 16px 20px 10px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
#   Initialisation réseau
# =========================
# Page active dans la barre de menu
if "active_page" not in st.session_state:
    st.session_state.active_page = "topology"

if "network" not in st.session_state:
    st.session_state.network = Network(directed=False)
    save_network(st.session_state.network)

if "shortest_path" not in st.session_state:
    st.session_state.shortest_path = None

if "mst_edges" not in st.session_state:
    st.session_state.mst_edges = None

if "scc_list" not in st.session_state:
    st.session_state.scc_list = None

if "articulation_nodes" not in st.session_state:
    st.session_state.articulation_nodes = None

if "command_history" not in st.session_state:
    st.session_state.command_history = []

net: Network = st.session_state.network

# =========================
#   Fonction de dessin
# =========================

def draw_topology(net: Network):
    fig, ax = plt.subplots()

    if net.graph.number_of_nodes() == 0:
        ax.text(
            0.5,
            0.5,
            "Aucune topologie pour le moment.\nAjoute des nœuds et des liens.",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.axis("off")
        st.pyplot(fig)
        return

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

    nx.draw_networkx_edge_labels(
        net.graph,
        pos,
        edge_labels=forward_labels,
        ax=ax,
        font_size=8,
        rotate=False,
        label_pos=0.6,
    )

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

    # Surlignage Dijkstra
    path = st.session_state.get("shortest_path")
    if path:
        path_edges = list(zip(path, path[1:]))
        nx.draw_networkx_nodes(net.graph, pos, nodelist=path, node_color="red", ax=ax)
        nx.draw_networkx_edges(
            net.graph,
            pos,
            edgelist=path_edges,
            edge_color="red",
            width=3,
            ax=ax,
        )

    # Surlignage MST
    mst_edges = st.session_state.get("mst_edges")
    if mst_edges:
        nx.draw_networkx_edges(
            net.graph,
            pos,
            edgelist=mst_edges,
            edge_color="green",
            width=3,
            style="dashed",
            arrows=net.directed,
            ax=ax,
        )

    # Points d'articulation
    ap_nodes = st.session_state.get("articulation_nodes")
    if ap_nodes:
        nx.draw_networkx_nodes(
            net.graph,
            pos,
            nodelist=ap_nodes,
            node_color="orange",
            node_size=600,
            ax=ax,
        )

    ax.set_axis_off()
    st.pyplot(fig)

# =========================
#   Titre + onglets
# =========================

st.title("Interpréteur de topologie réseau (Streamlit)")

# ===== Barre de menu avec icônes =====
menu_col1, menu_col2, menu_col3 = st.columns(3)

with menu_col1:
    st.image("icons/topo.png", width=40)
    if st.button("Topologie", key="btn_topology"):
        st.session_state.active_page = "topology"

with menu_col2:
    st.image("icons/analyse.png", width=40)
    if st.button("Analyse", key="btn_analyse"):
        st.session_state.active_page = "analyse"

with menu_col3:
    st.image("icons/console.png", width=40)
    if st.button("Console", key="btn_console"):
        st.session_state.active_page = "console"

st.markdown("---")



# =========================
#   Onglet 1 : Topologie & édition
# =========================
page = st.session_state.active_page

if page=="topology":

    col_left, col_right = st.columns([1.2, 2])

    with col_left:
        st.subheader("Édition du graphe")

        # Type de graphe
        mode = st.radio(
            "Type de graphe",
            options=["Non orienté", "Orienté"],
            index=1 if net.directed else 0,
        )

        if mode == "Orienté" and not net.directed:
            net.set_directed(True)
            save_network(net)
            st.info("Passage en graphe orienté.")
            st.rerun()
        elif mode == "Non orienté" and net.directed:
            net.set_directed(False)
            save_network(net)
            st.info("Passage en graphe non orienté.")
            st.rerun()

        st.markdown("---")

        # Ajouter un nœud
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
                        st.rerun()
                    else:
                        st.warning(f"Nœud déjà existant : {new_node}")

        # Ajouter un lien
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
                            st.rerun()
                        else:
                            st.error(
                                f"Impossible d'ajouter le lien, vérifiez que {n1} et {n2} existent."
                            )

        st.markdown("---")
        st.subheader("Gestion des nœuds et liens")

        # Supprimer un nœud
        st.markdown("**Supprimer un nœud**")
        nodes = net.list_nodes()
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
                        st.rerun()
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
                        st.rerun()
                    else:
                        st.error("Suppression de lien impossible.")
        else:
            st.info("Aucun lien à supprimer.")

        # Modifier latence
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
                        st.rerun()
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
                            st.rerun()
                        else:
                            st.error("Renommage impossible (nom déjà utilisé ?).")
        else:
            st.info("Aucun nœud à renommer.")

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
                    st.rerun()

            draw_topology(net)

elif page== "analyse":

    col_a1, col_a2 = st.columns([1.2, 2])

    with col_a1:
        st.subheader("Plus court chemin (Dijkstra)")
        nodes = sorted(net.graph.nodes())
        if len(nodes) >= 2:
            src = st.selectbox("Nœud source", nodes, key="dijkstra_src")
            dst = st.selectbox("Nœud destination", nodes, key="dijkstra_dst")

            cols = st.columns(2)
            with cols[0]:
                if st.button("Calculer le plus court chemin"):
                    path, dist = net.shortest_path_dijkstra(src, dst)
                    if path is None:
                        st.warning(f"Aucun chemin trouvé entre {src} et {dst}.")
                        st.session_state.shortest_path = None
                    else:
                        st.success(
                            f"Chemin le plus court de {src} à {dst} : "
                            f"{' -> '.join(path)} (latence totale = {dist} ms)"
                        )
                        st.session_state.shortest_path = path
                        save_network(net)
            with cols[1]:
                if st.button("Effacer le chemin Dijkstra"):
                    st.session_state.shortest_path = None
                    st.info("Chemin Dijkstra effacé (topologie inchangée).")

        else:
            st.info("Ajoute au moins deux nœuds pour utiliser Dijkstra.")

        st.markdown("---")
        st.subheader("Arbre couvrant minimum (Kruskal / Prim)")

        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            if st.button("MST (Kruskal)"):
                edges = net.mst_edges(algo="kruskal")
                if not edges:
                    st.warning("Aucun arbre couvrant (graphe vide ?).")
                    st.session_state.mst_edges = None
                else:
                    st.session_state.mst_edges = edges
                    st.success(f"ACM (Kruskal) calculé avec {len(edges)} arêtes.")
        with col_m2:
            if st.button("MST (Prim)"):
                edges = net.mst_edges(algo="prim")
                if not edges:
                    st.warning("Aucun arbre couvrant (graphe vide ?).")
                    st.session_state.mst_edges = None
                else:
                    st.session_state.mst_edges = edges
                    st.success(f"ACM (Prim) calculé avec {len(edges)} arêtes.")
        with col_m3:
            if st.button("Effacer MST"):
                st.session_state.mst_edges = None
                st.info("Résultat MST effacé.")

        st.markdown("---")
        st.subheader("Analyse de connectivité (Tarjan)")

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            if st.button("CFC"):
                scc = net.strongly_connected_components()
                st.session_state.scc_list = scc
                if not scc:
                    st.warning("Aucune composante (graphe vide).")
                else:
                    st.success(f"{len(scc)} composante(s) fortement connexe(s).")
        with col_t2:
            if st.button("Points d'articulation"):
                aps = net.articulation_points()
                st.session_state.articulation_nodes = aps
                if not aps:
                    st.info("Aucun point d'articulation.")
                else:
                    st.success(f"{len(aps)} point(s) d'articulation trouvé(s).")
        with col_t3:
            if st.button("Effacer Tarjan"):
                st.session_state.scc_list = None
                st.session_state.articulation_nodes = None
                st.info("Résultats Tarjan effacés.")

        st.markdown("---")
        
        st.subheader("Analyse de cycles")
        if st.button("Tester si le graphe est acyclique"):
            if net.graph.number_of_nodes() == 0:
                st.info("Graphe vide : considéré comme acyclique (aucun nœud, aucun cycle).")
            else:
                if net.is_acyclic():
                    if net.directed:
                        st.success("Le graphe est acyclique (DAG).")
                    else:
                        st.success("Le graphe est acyclique (forêt, aucun cycle).")
                else:
                    st.error("Le graphe contient au moins un cycle.")


    with col_a2:
        with st.container(key="topology_box_analyse"):
            st.subheader("Topologie (vue analyse)")
            draw_topology(net)

# =========================
#   Onglet 3 : Console avancée
# =========================

elif page=="console":

    col_c1, col_c2 = st.columns([1.3, 1.7])

    with col_c1:
        st.subheader("Console avancée (CLI intégrée)")

        if st.button("Recharger l'état depuis le terminal"):
            st.session_state.network = load_network()
            net = st.session_state.network
            st.success("État rechargé depuis le CLI.")

        st.markdown(
            """
Commandes disponibles (exemples) :

- `list-nodes`
- `list-links`
- `show-node R1`
- `simulate-ping R1 R3`
- `add-node R1`
- `add-link R2 R1 10`
- `delete-node R1`
- `delete-link R1 R2`
- `update-link R1 R2 15`
- `rename-node R1 R10`
- `reset-network`
- `set-directed`
- `set-undirected`
- `dijkstra R1 R2`
- `mst-kruskal`
- `mst-prim`
- `scc`
- `articulation`
- `is-acyclic`
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
                save_network(net)
                st.session_state.command_history.append(f"> {cmd}\n{output}")

        st.markdown("**Historique des commandes**")
        history_text = "\n\n".join(st.session_state.command_history)
        st.text_area("Historique", value=history_text, height=260)

    with col_c2:
        with st.container(key="topology_box_console"):
            st.subheader("Topologie réseau")
            draw_topology(net)
