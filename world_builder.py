import random
from typing import Dict, List, Tuple
from models import Node, Host, Fact, Visitor, GameState
from themes import Theme

def make_graph(num_nodes: int, rng: random.Random, theme: Theme) -> Dict[int, Node]:
    # Ensure num_nodes doesn't exceed available names
    available_names = list(theme.node_names)
    if num_nodes > len(available_names):
        num_nodes = len(available_names)
        
    names = rng.sample(available_names, num_nodes)
    nodes: Dict[int, Node] = {}
    coords = set()
    for i in range(num_nodes):
        while True:
            # Grid size
            pos = (rng.randint(0, 5), rng.randint(0, 5))
            if pos not in coords:
                coords.add(pos)
                break
        nodes[i] = Node(
            node_id=i,
            name=names[i],
            pos=pos,
            ambiance=rng.choice(theme.ambiance_tags),
        )

    order = list(nodes.keys())
    rng.shuffle(order)
    # Ensure connectivity
    for i in range(1, num_nodes):
        a, b = order[i - 1], order[i]
        nodes[a].neighbors.add(b)
        nodes[b].neighbors.add(a)

    extra_edges = max(2, num_nodes // 3)
    for _ in range(extra_edges):
        a, b = rng.sample(list(nodes.keys()), 2)
        if a != b:
            nodes[a].neighbors.add(b)
            nodes[b].neighbors.add(a)

    return nodes


def attach_hosts(nodes: Dict[int, Node], artifact_node: int, rng: random.Random, theme: Theme) -> None:
    host_names = list(theme.host_names)
    rng.shuffle(host_names)

    artifact_node_name = nodes[artifact_node].name
    neighbors = list(nodes[artifact_node].neighbors)
    neighbor_names = [nodes[n].name for n in neighbors]
    
    # Get theme specific info for clues
    other_node_index = (artifact_node + 1) % len(nodes)
    other_node_name = nodes[other_node_index].name
    
    clue_texts = theme.get_clues(artifact_node_name, neighbor_names, other_node_name)
    red_herrings = theme.get_red_herrings()

    host_index = 0
    # Place hosts
    for node in nodes.values():
        host_count = rng.randint(0, 2)
        node.hosts = []
        for _ in range(host_count):
            name = host_names[host_index % len(host_names)]
            host_index += 1
            persona = rng.choice(theme.host_personas)
            knowledge: List[Fact] = []

            # Assign clues sparsely
            if clue_texts and rng.random() > 0.6:
                knowledge.append(Fact(text=clue_texts.pop(0), topic="clue", is_clue=True))
            else:
                filler = rng.choice(red_herrings)
                knowledge.append(Fact(text=filler, topic="filler", is_clue=False))
            
            node.hosts.append(Host(name=name, persona=persona, knowledge=knowledge))


def init_visitors(nodes: Dict[int, Node], rng: random.Random, theme: Theme) -> List[Visitor]:
    start_node = rng.choice(list(nodes.keys()))
    visitors = []
    
    for i, (name, role) in enumerate(theme.visitor_archetypes):
        visitors.append(Visitor(visitor_id=i, name=name, role=role, node_id=start_node))
    return visitors


def build_world(turns: int, seed: int, theme: Theme) -> GameState:
    rng = random.Random(seed)
    # Smaller graph for demo
    nodes = make_graph(num_nodes=8, rng=rng, theme=theme)
    artifact_node_id = rng.choice(list(nodes.keys()))
    attach_hosts(nodes, artifact_node_id, rng, theme)
    visitors = init_visitors(nodes, rng, theme)

    state = GameState(
        nodes=nodes,
        visitors=visitors,
        artifact_node_id=artifact_node_id,
        shared_notebook=[],
        found_clues=set(),
    )
    return state
