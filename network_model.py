import networkx as nx


class Network:
    def __init__(self, directed: bool = False):
        """
        directed = False  -> graphe non orienté (nx.Graph)
        directed = True   -> graphe orienté   (nx.DiGraph)
        """
        self.directed = directed
        self.graph = nx.DiGraph() if directed else nx.Graph()
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
        # relabel_nodes renvoie un nouveau graphe
        self.graph = nx.relabel_nodes(self.graph, mapping)
        return True
