import os
import pickle
from typing import Optional
from state import load_network, save_network
from commands import handle_command

import typer

from network_model import Network

app = typer.Typer(help="CLI pour le réseau (basée sur Network et Typer).")

STATE_FILE = "network_state.pkl"


# ---------- Fonctions utilitaires : chargement / sauvegarde ----------

def load_network() -> Network:
    """
    Charge l'état du réseau depuis un fichier pickle, ou crée un nouveau réseau vide.
    """
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            net = pickle.load(f)
        # petit garde-fou : si jamais ce n'est pas un Network, on repart de zéro
        if not isinstance(net, Network):
            net = Network(directed=False)
    else:
        net = Network(directed=False)
    return net


def save_network(net: Network) -> None:
    """
    Sauvegarde l'état du réseau dans un fichier pickle.
    """
    with open(STATE_FILE, "wb") as f:
        pickle.dump(net, f)


# ---------- Commandes CLI ----------

@app.command("init")
def init(
    directed: bool = typer.Option(
        False,
        "--directed/--undirected",
        help="Choisir si le graphe initial est orienté ou non.",
    )
):
    """
    Réinitialise complètement le réseau (vide) avec le mode souhaité.
    """
    net = Network(directed=directed)
    save_network(net)
    typer.echo(f"Réseau initialisé (directed={net.directed}).")


@app.command("set-directed")
def cmd_set_directed():
    """
    Passe le réseau en mode orienté (DiGraph).
    """
    net = load_network()
    net.set_directed(True)
    save_network(net)
    typer.echo("Mode graphe orienté activé.")


@app.command("set-undirected")
def cmd_set_undirected():
    """
    Passe le réseau en mode non orienté (Graph).
    """
    net = load_network()
    net.set_directed(False)
    save_network(net)
    typer.echo("Mode graphe non orienté activé.")


@app.command("list-nodes")
def cmd_list_nodes():
    """
    Affiche la liste des nœuds.
    """
    net = load_network()
    nodes = net.list_nodes()
    if not nodes:
        typer.echo("Aucun nœud.")
    else:
        for n in nodes:
            typer.echo(n)


@app.command("list-links")
def cmd_list_links():
    """
    Affiche la liste des liens avec leur latence.
    """
    net = load_network()
    links = net.list_links()
    if not links:
        typer.echo("Aucun lien.")
        return
    arrow = "->" if net.directed else "--"
    for u, v, data in links:
        latency = data.get("latency", "?")
        typer.echo(f"{u} {arrow} {v}  latency={latency} ms")


@app.command("add-node")
def cmd_add_node(node_id: str):
    """
    Ajoute un nœud au réseau.
    """
    net = load_network()
    if net.add_node(node_id):
        save_network(net)
        typer.echo(f"Nœud ajouté : {node_id}")
    else:
        typer.echo(f"Nœud déjà existant : {node_id}")


@app.command("delete-node")
def cmd_delete_node(node_id: str):
    """
    Supprime un nœud et tous ses liens.
    """
    net = load_network()
    if net.delete_node(node_id):
        save_network(net)
        typer.echo(f"Nœud supprimé : {node_id}")
    else:
        typer.echo(f"Nœud introuvable : {node_id}")


@app.command("add-link")
def cmd_add_link(
    n1: str,
    n2: str,
    latency: int = typer.Option(1, "--latency", "-l", help="Latence en ms."),
):
    """
    Ajoute un lien entre n1 et n2, avec une latence.
    """
    net = load_network()
    if net.add_link(n1, n2, latency):
        save_network(net)
        arrow = "->" if net.directed else "--"
        typer.echo(f"Lien ajouté : {n1} {arrow} {n2} (latency={latency} ms)")
    else:
        typer.echo(f"Impossible d'ajouter le lien, vérifiez que {n1} et {n2} existent.")


@app.command("delete-link")
def cmd_delete_link(n1: str, n2: str):
    """
    Supprime un lien entre n1 et n2 (dans le sens n1 -> n2).
    """
    net = load_network()
    if net.delete_link(n1, n2):
        save_network(net)
        arrow = "->" if net.directed else "--"
        typer.echo(f"Lien supprimé : {n1} {arrow} {n2}")
    else:
        typer.echo("Lien introuvable.")


@app.command("update-link")
def cmd_update_link(n1: str, n2: str, latency: int):
    """
    Modifie la latence d'un lien existant.
    """
    net = load_network()
    if net.update_link_latency(n1, n2, latency):
        save_network(net)
        arrow = "->" if net.directed else "--"
        typer.echo(
            f"Latence du lien {n1} {arrow} {n2} mise à jour à {latency} ms."
        )
    else:
        typer.echo("Lien introuvable.")


@app.command("rename-node")
def cmd_rename_node(old_id: str, new_id: str):
    """
    Renomme un nœud en conservant ses liens.
    """
    net = load_network()
    if net.rename_node(old_id, new_id):
        save_network(net)
        typer.echo(f"Nœud renommé : {old_id} -> {new_id}")
    else:
        typer.echo("Renommage impossible (vérifie les noms).")


@app.command("show-node")
def cmd_show_node(node_id: str):
    """
    Affiche les infos détaillées d'un nœud.
    """
    net = load_network()
    info = net.show_node(node_id)
    if info is None:
        typer.echo(f"Nœud introuvable : {node_id}")
    else:
        typer.echo(f"Id       : {info['id']}")
        typer.echo(f"Degree   : {info['degree']}")
        neighbors = ", ".join(info["neighbors"]) if info["neighbors"] else "(aucun)"
        typer.echo(f"Voisins  : {neighbors}")


@app.command("simulate-ping")
def cmd_simulate_ping(src: str, dst: str):
    """
    Simule un ping entre deux nœuds.
    """
    net = load_network()
    res = net.simulate_ping(src, dst)
    if not res["ok"]:
        typer.echo(f"Erreur : {res['error']}")
    else:
        path_str = " -> ".join(res["path"])
        typer.echo("PING OK")
        typer.echo(f"Chemin  : {path_str}")
        typer.echo(f"Latence : {res['latency_ms']} ms")


@app.command("reset-network")
def cmd_reset_network():
    """
    Efface complètement la topologie actuelle.
    """
    net = load_network()
    net.reset()
    save_network(net)
    typer.echo("Topologie réinitialisée (mais mode directed/non directed conservé).")

@app.command("repl")
def repl():
    """
    Interpréteur interactif : tu tapes directement
    add-node r1, list-links, etc.
    """
    typer.echo("Interpréteur réseau interactif.")
    typer.echo("Tape 'help' pour voir les commandes.")
    typer.echo("Tape 'quit' ou 'exit' pour sortir.")
    typer.echo("")
    typer.echo("You can now type commands below, for example: add-node r1")
    typer.echo("")

    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            typer.echo("\nFin de session, réinitialisation de la topologie...")
            # on remet l'état à zéro
            empty = Network(directed=False)
            save_network(empty)
            break

        if cmd in ("quit", "exit"):
            typer.echo("Au revoir, réinitialisation de la topologie...")
            empty = Network(directed=False)
            save_network(empty)
            break

        if not cmd:
            continue

        # IMPORTANT : recharger l'état avant CHAQUE commande
        net = load_network()

        # réutilise toute la logique de commands.py
        out = handle_command(net, cmd)

        # sauvegarder après la commande (UI + CLI voient le même graphe)
        save_network(net)

        if out:
            typer.echo(out)


if __name__ == "__main__":
    app()
