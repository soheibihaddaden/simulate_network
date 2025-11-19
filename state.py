# state.py
import os
import pickle
from network_model import Network

STATE_FILE = "network_state.pkl"


def load_network() -> Network:
    """
    Charge le réseau depuis un fichier pickle, ou crée un nouveau réseau vide.
    """
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            net = pickle.load(f)
        if not isinstance(net, Network):
            net = Network(directed=False)
    else:
        net = Network(directed=False)
    return net


def save_network(net: Network) -> None:
    """
    Sauvegarde le réseau dans un fichier pickle.
    """
    with open(STATE_FILE, "wb") as f:
        pickle.dump(net, f)
