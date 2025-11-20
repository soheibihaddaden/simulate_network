from typing import List
import difflib

from network_model import Network

VALID_COMMANDS: List[str] = [
    "list-nodes",
    "list-links",
    "show-node",
    "simulate-ping",
    "add-node",
    "add-link",
    "delete-node",
    "delete-link",
    "update-link",
    "rename-node",
    "reset-network",
    "set-directed",
    "set-undirected",
    "dijkstra",
    "mst-kruskal",
    "mst-prim",
    "scc",   
    "articulation",
    "is-acyclic",
    "help",
]


def format_help() -> str:
    lines = [
        "Commandes disponibles :",
        "  list-nodes",
        "  list-links",
        "  show-node <id>",
        "  simulate-ping <src> <dst>",
        "  add-node <id>",
        "  add-link <n1> <n2> [latency]",
        "  delete-node <id>",
        "  delete-link <n1> <n2>",
        "  update-link <n1> <n2> <latency>",
        "  rename-node <old_id> <new_id>",
        "  reset-network",
        "  set-directed",
        "  set-undirected",
        "  dijkstra <src> <dst>",
        "  mst-kruskal",
        "  mst-prim",
        "  scc",   
        "  is-acyclic",
        "  articulation",
        "  help",
    ]
    return "\n".join(lines)


def handle_command(net: Network, cmd: str) -> str:
    cmd = cmd.strip()
    if not cmd:
        return ""

    parts = cmd.split()
    name = parts[0]
    args = parts[1:]

    # list-nodes
    if name == "list-nodes":
        nodes = net.list_nodes()
        if not nodes:
            return "Aucun nœud."
        return "\n".join(nodes)

    # list-links
    if name == "list-links":
        links = net.list_links()
        if not links:
            return "Aucun lien."
        lines = []
        for u, v, data in links:
            latency = data.get("latency", "?")
            arrow = "->" if net.directed else "--"
            lines.append(f"{u} {arrow} {v}  latency={latency} ms")
        return "\n".join(lines)

    # show-node <id>
    if name == "show-node":
        if len(args) != 1:
            return "Usage : show-node <id>"
        info = net.show_node(args[0])
        if info is None:
            return f"Nœud introuvable : {args[0]}"
        return (
            f"Id       : {info['id']}\n"
            f"Degree   : {info['degree']}\n"
            f"Voisins  : {', '.join(info['neighbors']) if info['neighbors'] else '(aucun)'}"
        )

    # simulate-ping <src> <dst>
    if name == "simulate-ping":
        if len(args) != 2:
            return "Usage : simulate-ping <src> <dst>"
        res = net.simulate_ping(args[0], args[1])
        if not res["ok"]:
            return f"Erreur : {res['error']}"
        path_str = " -> ".join(res["path"])
        return f"PING OK\nChemin  : {path_str}\nLatence : {res['latency_ms']} ms"

    # add-node <id>
    if name == "add-node":
        if len(args) != 1:
            return "Usage : add-node <id>"
        if net.add_node(args[0]):
            return f"Nœud ajouté : {args[0]}"
        else:
            return f"Nœud déjà existant : {args[0]}"

    # add-link <n1> <n2> [latency]
    if name == "add-link":
        if len(args) < 2:
            return "Usage : add-link <n1> <n2> [latency]"
        n1, n2 = args[0], args[1]
        latency = 1
        if len(args) >= 3:
            try:
                latency = int(args[2])
            except ValueError:
                return "Latence invalide, doit être un entier."
        if net.add_link(n1, n2, latency):
            arrow = "->" if net.directed else "--"
            return f"Lien ajouté : {n1} {arrow} {n2} (latency={latency} ms)"
        else:
            return f"Impossible d'ajouter le lien, vérifiez que {n1} et {n2} existent."

    # delete-node <id>
    if name == "delete-node":
        if len(args) != 1:
            return "Usage : delete-node <id>"
        if net.delete_node(args[0]):
            return f"Nœud supprimé : {args[0]}"
        else:
            return f"Nœud introuvable : {args[0]}"

    # delete-link <n1> <n2>
    if name == "delete-link":
        if len(args) != 2:
            return "Usage : delete-link <n1> <n2>"
        n1, n2 = args[0], args[1]
        if net.delete_link(n1, n2):
            arrow = "->" if net.directed else "--"
            return f"Lien supprimé : {n1} {arrow} {n2}"
        else:
            return "Lien introuvable."

    # update-link <n1> <n2> <latency>
    if name == "update-link":
        if len(args) != 3:
            return "Usage : update-link <n1> <n2> <latency>"
        n1, n2, lat_str = args
        try:
            latency = int(lat_str)
        except ValueError:
            return "Latence invalide, doit être un entier."
        if net.update_link_latency(n1, n2, latency):
            arrow = "->" if net.directed else "--"
            return f"Latence du lien {n1} {arrow} {n2} mise à jour à {latency} ms."
        else:
            return "Lien introuvable."

    # rename-node <old_id> <new_id>
    if name == "rename-node":
        if len(args) != 2:
            return "Usage : rename-node <old_id> <new_id>"
        old_id, new_id = args
        if net.rename_node(old_id, new_id):
            return f"Nœud renommé : {old_id} -> {new_id}"
        else:
            return "Renommage impossible (vérifie les noms)."

    # reset-network
    if name == "reset-network":
        net.reset()
        return "Topologie réinitialisée."

    # set-directed
    if name == "set-directed":
        net.set_directed(True)
        return "Mode graphe orienté activé."

    # set-undirected
    if name == "set-undirected":
        net.set_directed(False)
        return "Mode graphe non orienté activé."

    # dijkstra
    if name == "dijkstra":

        if len(args) != 2:
            return "Usage : dijkstra <src> <dst>"

        src, dst = args
        path, dist = net.shortest_path_dijkstra(src, dst)

        if path is None:
            return f"Aucun chemin trouvé entre {src} et {dst}."

        path_str = " -> ".join(path)
        return (
            f"Chemin le plus court (Dijkstra) de {src} à {dst} : {path_str}\n"
            f"Latence totale = {dist} ms"
        )
    
    # mst-kruskal
    if name == "mst-kruskal":
        edges = net.mst_edges(algo="kruskal")
        if not edges:
            return "Aucun arbre couvrant (graphe vide ?)."
        lines = ["Arbre couvrant minimum (Kruskal) :"]
        for u, v in edges:
            w = net.graph[u][v].get("latency", 1)
            lines.append(f"- {u} -- {v} (latence = {w} ms)")
        return "\n".join(lines)

    # mst-prim
    if name == "mst-prim":
        edges = net.mst_edges(algo="prim")
        if not edges:
            return "Aucun arbre couvrant (graphe vide ?)."
        lines = ["Arbre couvrant minimum (Prim) :"]
        for u, v in edges:
            w = net.graph[u][v].get("latency", 1)
            lines.append(f"- {u} -- {v} (latence = {w} ms)")
        return "\n".join(lines)

    if name == "scc":
        comps = net.strongly_connected_components()
        if not comps:
            return "Aucune composante (graphe vide)."
        lines = ["Composantes fortement connexes (Tarjan) :"]
        for i, comp in enumerate(comps, 1):
            nodes_str = ", ".join(comp)
            lines.append(f"- C{i} : {nodes_str}")
        return "\n".join(lines)
    
    # articulation
    if name == "articulation":
        aps = net.articulation_points()
        if not aps:
            return "Aucun point d'articulation (graphe biconnexe ou vide)."
        lines = ["Points d'articulation (Tarjan) :"]
        for n in aps:
            lines.append(f"- {n}")
        return "\n".join(lines)

    if name == "is-acyclic":
        if net.is_acyclic():
            if net.directed:
                return "Le graphe est acyclique (DAG)."
            else:
                return "Le graphe est acyclique (forêt, aucun cycle)."
        else:
            return "Le graphe contient au moins un cycle."
    

    # help
    if name == "help":
        return format_help()

    # Commande inconnue + suggestion
    suggestion = difflib.get_close_matches(name, VALID_COMMANDS, n=1, cutoff=0.6)
    if suggestion:
        return f"Commande inconnue : {name}\nDid you mean: {suggestion[0]} ?"
    else:
        return f"Commande inconnue : {name}"
    