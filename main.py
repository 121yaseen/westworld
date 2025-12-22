"""Text-based cooperative simulation inspired by Westworld (AI Edition).

Six AI-controlled visitors explore a node graph, question AI hosts, share clues in a
common notebook, and race to locate an artifact. 

USAGE:
1. Paste your Gemini API key in the GEMINI_API_KEY variable below.
2. Run with: python main.py
"""
from __future__ import annotations

import argparse
import random
import json
import time
import os
import textwrap
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"
# ---------------------

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def call_llm(prompt: str, json_mode: bool = False) -> str:
    """Helper to call Gemini API."""
    if not GEMINI_API_KEY or not HAS_GENAI:
        return ""
    
    try:
        if not hasattr(call_llm, "client"):
            call_llm.client = genai.Client(api_key=GEMINI_API_KEY)
            
        config = None
        if json_mode:
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )

        response = call_llm.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config
        )
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return ""


@dataclass
class Fact:
    text: str
    topic: str
    is_clue: bool = False


@dataclass
class Host:
    name: str
    persona: str
    knowledge: List[Fact]
    
    def chat(self, visitor_name: str, question: str) -> str:
        """Generates a response based on persona and knowledge."""
        if not GEMINI_API_KEY:
            # Fallback for no API key
            val = self.knowledge[0].text if self.knowledge else "I don't know anything about that."
            return f"{val} (AI Disabled)"

        clues = [f"- {k.text} (Important Clue!)" if k.is_clue else f"- {k.text}" for k in self.knowledge]
        knowledge_str = "\n".join(clues)
        
        prompt = f"""
        You are {self.name}, a {self.persona} in Westworld.
        Keep your response short (under 2 sentences). Speak in character.
        
        Your Knowledge Secrets:
        {knowledge_str}
        
        A visitor named {visitor_name} asks: "{question}"
        
        If the question is related to one of your secrets, reveal it in a subtle but helpful way. 
        If it's just 'Hello' or casual, make small talk.
        """
        response = call_llm(prompt)
        return response


@dataclass
class Node:
    node_id: int
    name: str
    pos: Tuple[int, int]
    neighbors: Set[int] = field(default_factory=set)
    hosts: List[Host] = field(default_factory=list)
    ambiance: str = ""


@dataclass
class Visitor:
    visitor_id: int
    name: str
    role: str
    node_id: int
    private_notes: List[str] = field(default_factory=list)
    seen_hosts: Set[str] = field(default_factory=set)

    def think_and_act(self, state: 'GameState', rng: random.Random) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Decides the next action using AI or fallback logic.
        Returns: (ActionType, Target, Metadata/Message)
        Actions: MOVE, ASK, CHAT, INSPECT
        """
        node = state.nodes[self.node_id]
        neighbors = {nid: state.nodes[nid].name for nid in node.neighbors}
        present_hosts = [h.name for h in node.hosts]
        other_visitors = [v.name for v in state.visitors if v.node_id == self.node_id and v.visitor_id != self.visitor_id]
        
        # Format the shared notebook effectively
        notebook_summary = "\n".join(state.shared_notebook[-10:]) # Last 10 entries to save context
        known_clues = list(state.found_clues)
        
        if not GEMINI_API_KEY:
            # Fallback logic (heuristics from original game)
            if len(state.found_clues) >= 3 and self.node_id == state.artifact_node_id:
               return ("inspect", None, "Checking for artifact...")
            
            for h in node.hosts:
                 if h.name not in self.seen_hosts:
                     return ("ask", h.name, "What can you tell me?")
            
            # Random move
            target = rng.choice(list(node.neighbors))
            return ("move", str(target), "Roaming...")

        # AI Logic
        prompt = f"""
        You are {self.name}, a {self.role}. You are in a cooperative game to find a hidden Artifact.
        
        GOAL: Collect 3 unique clues from Hosts, then go to the Artifact Location and INSPECT it.
        CURRENT PROGRESS: {len(known_clues)}/3 Clues found: {known_clues}
        
        LOCATION: {node.name} (Ambiance: {node.ambiance})
        NEIGHBORS (Exits): {json.dumps(neighbors)}
        
        PEOPLE HERE:
        - Hosts (NPCs): {present_hosts} 
        - Other Visitors (Teammates): {other_visitors}
        
        SHARED NOTEBOOK (Recent):
        {notebook_summary}
        
        DECISION:
        Choose one action. 
        - "move": Go to a neighbor ID. 
        - "ask": Ask a Host a specific question.
        - "chat": Tell a specific Teammate something or "all" to speak to everyone in room.
        - "inspect": If you think this is the artifact location and you have 3 clues.
        
        Respond in JSON format: 
        {{
          "reasoning": "short thought process",
          "action": "move" | "ask" | "chat" | "inspect", 
          "target": "neighbor_id_int" | "host_name" | "visitor_name/all",
          "content": "question_or_message" 
        }}
        """
        
        try:
            response_text = call_llm(prompt, json_mode=True)
            decision = json.loads(response_text)
            
            act = decision.get("action", "move").lower()
            reason = decision.get("reasoning", "")
            target = decision.get("target")
            content = decision.get("content", "")
            
            # Post-process targets to valid types
            if act == "move":
                # Ensure target is valid int
                try:
                   t_int = int(target)
                   if t_int in node.neighbors:
                       return ("move", str(t_int), reason)
                except:
                    pass
                # Fallback move if AI hallucinates invalid node
                safe_target = rng.choice(list(node.neighbors))
                return ("move", str(safe_target), f"AI Attempted invalid move to {target}. Fallback random.")
            
            elif act == "ask":
                if target in present_hosts:
                    return ("ask", target, content or "Do you know any secrets?")
            
            elif act == "chat":
                if target == "all" or target in other_visitors:
                    return ("chat", target, content)
            
            elif act == "inspect":
                return ("inspect", None, reason)
                
        except Exception as e:
            print(f"AI Decision Error: {e}")
        
        # Fallback if AI fails parsing
        target = rng.choice(list(node.neighbors))
        return ("move", str(target), "AI Error fallback")


@dataclass
class GameState:
    nodes: Dict[int, Node]
    visitors: List[Visitor]
    artifact_node_id: int
    shared_notebook: List[str]
    found_clues: Set[str]
    turn: int = 0
    finished: bool = False
    transcript: List[str] = field(default_factory=list)


HOST_PERSONAS = [
    "bartender", "sheriff", "rancher", "card dealer", "drifter", "herbalist",
    "armorer", "railway clerk", "hacker in disguise", "archivist", "prospector",
]

NODE_NAMES = [
    "Mesa Hub", "Sweetwater Plaza", "Ghost Ridge", "Copper Spur", "Lazarus Gulch",
    "Coyote Pass", "Ironwood", "Mirror Lake", "Dust Town", "Glass Arroyo",
    "Red Mesa", "Nightfall Station",
]

AMBIANCE_TAGS = [
    "dusty", "lantern-lit", "echoing", "quiet", "busy", "stormy", "sunlit",
    "foggy", "windy", "shadowy",
]

VISITOR_ARCHETYPES = [
    ("Avery", "Analyst"),
    ("Blake", "Diplomat"),
    ("Cass", "Scout"),
]


def make_graph(num_nodes: int, rng: random.Random) -> Dict[int, Node]:
    names = rng.sample(NODE_NAMES, num_nodes)
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
            ambiance=rng.choice(AMBIANCE_TAGS),
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


def attach_hosts(nodes: Dict[int, Node], artifact_node: int, rng: random.Random) -> None:
    host_names = [
        "Maeve", "Dolores", "Teddy", "Stubbs", "Armistice", "Clementine",
        "Elsie", "Hector", "Lawrence", "Angela", "Coughlin", "Juliet",
    ]
    rng.shuffle(host_names)

    artifact_node_name = nodes[artifact_node].name
    neighbors = list(nodes[artifact_node].neighbors)
    neighbor_names = [nodes[n].name for n in neighbors]
    
    # Logic Clues
    clue_texts = [
        f"The artifact is hidden in {artifact_node_name}.",
        f"You must go to the place connected to {neighbor_names[0]}.",
        "The lock requires three confirmed rumors to open.",
        f"It is not in {nodes[(artifact_node + 1) % len(nodes)].name}."
    ]

    red_herrings = [
        "The rattlesnakes are restless.",
        "I heard a ghost haunts the old mine.",
        "The train is late today.",
        "These violent delights have violent ends.",
    ]

    host_index = 0
    # Place hosts
    for node in nodes.values():
        host_count = rng.randint(0, 2)
        node.hosts = []
        for _ in range(host_count):
            name = host_names[host_index % len(host_names)]
            host_index += 1
            persona = rng.choice(HOST_PERSONAS)
            knowledge: List[Fact] = []

            # Assign clues sparsely
            if clue_texts and rng.random() > 0.6:
                knowledge.append(Fact(text=clue_texts.pop(0), topic="clue", is_clue=True))
            else:
                filler = rng.choice(red_herrings)
                knowledge.append(Fact(text=filler, topic="filler", is_clue=False))
            
            node.hosts.append(Host(name=name, persona=persona, knowledge=knowledge))


def init_visitors(nodes: Dict[int, Node], rng: random.Random) -> List[Visitor]:
    start_node = rng.choice(list(nodes.keys()))
    visitors = []
    # Use fewer visitors for AI mode to save API calls, or full set? 
    # Let's use the defined list which is 3 now.
    for i, (name, role) in enumerate(VISITOR_ARCHETYPES):
        visitors.append(Visitor(visitor_id=i, name=name, role=role, node_id=start_node))
    return visitors


def run_game(turns: int, seed: int) -> GameState:
    rng = random.Random(seed)
    # Smaller graph for demo
    nodes = make_graph(num_nodes=8, rng=rng)
    artifact_node_id = rng.choice(list(nodes.keys()))
    attach_hosts(nodes, artifact_node_id, rng)
    visitors = init_visitors(nodes, rng)

    state = GameState(
        nodes=nodes,
        visitors=visitors,
        artifact_node_id=artifact_node_id,
        shared_notebook=[],
        found_clues=set(),
    )

    print(f"--- WORLD GENERATED (Seed {seed}) ---")
    print(f"Goal: Find the Artifact. Hidden at Node {artifact_node_id} ('{nodes[artifact_node_id].name}')")
    print("-------------------------------------")

    for t in range(turns):
        state.turn = t + 1
        if state.finished:
            break
            
        print(f"\n=== TURN {state.turn} ===")
        
        # Shuffle visitors so they don't always act in same order
        active_visitors = list(state.visitors)
        rng.shuffle(active_visitors)
        
        for visitor in active_visitors:
            if state.finished:
                break

            act, target, msg = visitor.think_and_act(state, rng)
            node = state.nodes[visitor.node_id]

            log_entry = ""

            if act == "ask":
                # Find host
                host_obj = next((h for h in node.hosts if h.name == target), None)
                if host_obj:
                    # Host interaction
                    answer = host_obj.chat(visitor.name, msg)
                    visitor.seen_hosts.add(host_obj.name)
                    
                    log_entry = f"{visitor.name} asked {host_obj.name}: '{msg}' -> Answer: '{answer}'"
                    print(f"🗣️  {log_entry}")
                    state.shared_notebook.append(f"Turn {state.turn}: {log_entry}")
                    
                    # Check for clues (simplified: if host had a clue, we assume the AI extracted it or got it)
                    # For game mechanics, we check if the host HAS a clue and if the answer was generated.
                    # To be robust, we just mark the clue as found if the host has one, assuming the AI gave it up.
                    for fact in host_obj.knowledge:
                        if fact.is_clue and fact.text not in state.found_clues:
                            state.found_clues.add(fact.text)
                            print(f"💡 CLUE FOUND: {fact.text}")
                            state.shared_notebook.append(f"*** CLUE ACQUIRED: {fact.text} ***")

            elif act == "chat":
                log_entry = f"{visitor.name} says to {target}: '{msg}'"
                print(f"💬 {log_entry}")
                state.shared_notebook.append(f"Turn {state.turn}: {log_entry}")

            elif act == "move":
                dest = int(target)
                prev_name = node.name
                visitor.node_id = dest
                new_node = state.nodes[dest]
                log_entry = f"{visitor.name} moved from {prev_name} to {new_node.name}. ({msg})"
                print(f"👣 {log_entry}")
                state.transcript.append(f"Turn {state.turn}: {log_entry}")

            elif act == "inspect":
                print(f"🔍 {visitor.name} is inspecting {node.name} for the artifact...")
                if visitor.node_id == state.artifact_node_id and len(state.found_clues) >= 3:
                     win_msg = f"{visitor.name} UNLOCKED the artifact at {node.name}! VICTORY!"
                     print(f"🏆 {win_msg}")
                     state.shared_notebook.append(win_msg)
                     state.finished = True
                else:
                    fail_reason = "Wrong location" if visitor.node_id != state.artifact_node_id else "Not enough clues"
                    print(f"❌ Failed to unlock. reason: {fail_reason}")
                    state.shared_notebook.append(f"{visitor.name} inspected {node.name} but failed ({fail_reason}).")

            # Small delay to avoid rate limits if running fast
            if GEMINI_API_KEY:
                time.sleep(1) 

    return state


def render_map(nodes: Dict[int, Node]) -> str:
    lines = ["Map Structure:"]
    for nid in sorted(nodes):
        node = nodes[nid]
        neigh = ", ".join(nodes[n].name for n in sorted(node.neighbors))
        hosts = ", ".join(h.name for h in node.hosts)
        lines.append(f"  [{nid}] {node.name:20} -> Connects to: [{neigh}] | Hosts: {hosts if hosts else 'None'}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Westworld AI Sim")
    parser.add_argument("--turns", type=int, default=15, help="Number of turns")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    if not GEMINI_API_KEY:
        print("\n⚠️  WARNING: GEMINI_API_KEY is not set. The simulation will run in logic-fallback mode.")
        print("   To enable AI, edit main.py and paste your API key.\n")
    else:
        print(f"\n🧠 AI Enabled (Model: {MODEL_NAME})")

    state = run_game(turns=args.turns, seed=args.seed)

    print("\n" + "="*30)
    print("FINAL REPORT")
    print("="*30)
    print(render_map(state.nodes))
    print("\nNotebook Highlights:")
    for line in state.shared_notebook:
        print(f" - {line}")

    if state.finished:
        print("\nResult: SUCCESS - Artifact Recovered.")
    else:
        print("\nResult: FAILURE - Time ran out.")

if __name__ == "__main__":
    main()
