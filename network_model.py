import networkx as nx

from networkx.algorithms import tree as nx_tree

class Network:
    def __init__(self, directed: bool = False):
        """
        directed = False  -> graphe non orienté (nx.Graph)
        directed = True   -> graphe orienté   (nx.DiGraph)
        """
        self.directed = directed
        self.graph = nx.DiGraph() if directed else nx.Graph()
        self.last_shortest_path = None
        # graphe vide au démarrage

    def set_directed(self, directed: bool):
        """
        Change le type de graphe en conservant les nœuds et liens existants.
        (attention : en orienté, chaque lien devient (u, v) + (v, u))
        """
        if directed == self.directed:
            return

        if directed:
            # Graph -> DiGraph
            self.graph = self.graph.to_directed()
        else:
            # DiGraph -> Graph
            self.graph = self.graph.to_undirected()

        self.directed = directed

    # ---------- Reset complet ----------

    def reset(self):
        """Efface totalement la topologie (tous les nœuds et liens)."""
        self.graph.clear()

    # ---------- Commandes de base ----------

    def list_nodes(self):
        return list(self.graph.nodes)

    def list_links(self):
        # retourne (u, v, data)
        return list(self.graph.edges(data=True))

    def show_node(self, node_id):
        if node_id not in self.graph:
            return None
        return {
            "id": node_id,
            "degree": self.graph.degree[node_id],
            "neighbors": list(self.graph.neighbors(node_id)),
        }

    def simulate_ping(self, src, dst):
        if src not in self.graph or dst not in self.graph:
            return {
                "ok": False,
                "error": f"Unknown host: {src} or {dst}",
            }
        try:
            path = nx.shortest_path(self.graph, src, dst)
            total_latency = 0
            for u, v in zip(path, path[1:]):
                total_latency += self.graph[u][v].get("latency", 1)

            return {
                "ok": True,
                "path": path,
                "latency_ms": total_latency,
            }
        except Exception:
            return {
                "ok": False,
                "error": "No route between hosts",
            }

    # ---------- CRUD sur nœuds / liens ----------

    def add_node(self, node_id):
        if node_id in self.graph:
            return False
        self.graph.add_node(node_id)
        return True

    def add_link(self, n1, n2, latency=1):
        if n1 not in self.graph or n2 not in self.graph:
            return False
        self.graph.add_edge(n1, n2, latency=latency)
        return True

    def delete_node(self, node_id):
        """Supprime un nœud et tous les liens associés."""
        if node_id not in self.graph:
            return False
        self.graph.remove_node(node_id)
        return True

    def delete_link(self, n1, n2):
        """Supprime un lien entre n1 et n2 (sens unique si orienté)."""
        if not self.graph.has_edge(n1, n2):
            return False
        self.graph.remove_edge(n1, n2)
        return True

    def update_link_latency(self, n1, n2, latency: int):
        """Modifie la latence d'un lien existant."""
        if not self.graph.has_edge(n1, n2):
            return False
        self.graph[n1][n2]["latency"] = latency
        return True

    def rename_node(self, old_id: str, new_id: str):
        """Renomme un nœud en conservant tous ses liens."""
        if old_id not in self.graph or new_id in self.graph:
            return False
        mapping = {old_id: new_id}
        
        self.graph = nx.relabel_nodes(self.graph, mapping)
        return True

    def shortest_path_dijkstra(self, src: str, dst: str):
        if src not in self.graph or dst not in self.graph:
            return None, None

        try:
            path = nx.dijkstra_path(
                self.graph,
                source=src,
                target=dst,
                weight="latency",
            )
            distance = nx.dijkstra_path_length(
                self.graph,
                source=src,
                target=dst,
                weight="latency",
            )
            return path, distance
        except nx.NetworkXNoPath:
            return None, None

    def strongly_connected_components(self):
        """
        Retourne la liste des composantes fortement connexes (Tarjan).
        N'a de sens que pour un graphe orienté.
        """
        if not self.directed:
            # on travaille sur version orientée si besoin
            G = self.graph.to_directed()
        else:
            G = self.graph

        comps = list(nx.strongly_connected_components(G))
        # chaque comp est un set de nœuds
        return [sorted(c) for c in comps]

    def mst_edges(self, algo: str = "kruskal"):
        """
        Retourne la liste des arêtes de l'arbre couvrant minimum
        selon l'algorithme choisi : 'kruskal' ou 'prim'.
        Utilise l'attribut 'latency' comme poids.
        """
        if self.directed:
            # MST classique sur graphe non orienté
            G = self.graph.to_undirected()
        else:
            G = self.graph

        if G.number_of_nodes() == 0:
            return []

        mst_iter = nx_tree.minimum_spanning_edges(
            G,
            algorithm=algo,
            weight="latency",
            data=False,   # on veut juste (u, v)
        )
        return list(mst_iter)

    def articulation_points(self):
        """
        Retourne la liste des points d'articulation (Tarjan) sur le graphe non orienté.
        """
        if self.directed:
            G = self.graph.to_undirected()
        else:
            G = self.graph

        return list(nx.articulation_points(G))

    def is_acyclic(self) -> bool:
        """
        Retourne True si le graphe est acyclique, False sinon.

        - Si le graphe est orienté : teste si c'est un DAG.
        - Si le graphe est non orienté : teste s'il s'agit d'une forêt (aucun cycle).
        """
        if self.directed:
            # DAG = directed acyclic graph
            return nx.is_directed_acyclic_graph(self.graph)
        else:
            # Une forêt est un graphe non orienté sans cycles
            return nx_tree.is_forest(self.graph)
