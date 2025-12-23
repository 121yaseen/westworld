"""Text-based cooperative simulation (AI Edition).

Six AI-controlled visitors explore a node graph, question AI hosts, share clues in a
common notebook, and race to locate an artifact/horcrux.

USAGE:
1. Ensure GEMINI_API_KEY is set in .env.
2. Run with: python main.py
"""
from __future__ import annotations

import argparse
import random
import time
import os
import sys

# Local imports
from llm_client import GEMINI_API_KEY, MODEL_NAME
from models import GameState
from themes import WestworldTheme, HarryPotterTheme, Theme
from world_builder import build_world


def run_simulation(state: GameState, turns: int) -> None:
    print(f"--- WORLD GENERATED ---")
    goal_item = "Horcrux" if "Hogwarts" in state.nodes[0].ambiance else "Artifact" # Simple heuristic or pass theme
    print(f"Goal: Find the {goal_item}. Hidden at Node {state.artifact_node_id} ('{state.nodes[state.artifact_node_id].name}')")
    print("-------------------------------------")

    rng = random.Random(time.time()) # Runtime randomness for interactions

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
                print(f"🔍 {visitor.name} is inspecting {node.name}...")
                if visitor.node_id == state.artifact_node_id and len(state.found_clues) >= 3:
                     win_msg = f"{visitor.name} UNLOCKED the target at {node.name}! VICTORY!"
                     print(f"🏆 {win_msg}")
                     state.shared_notebook.append(win_msg)
                     state.finished = True
                else:
                    fail_reason = "Wrong location" if visitor.node_id != state.artifact_node_id else "Not enough clues"
                    print(f"❌ Failed to unlock. reason: {fail_reason}")
                    state.shared_notebook.append(f"{visitor.name} inspected {node.name} but failed ({fail_reason}).")

            if GEMINI_API_KEY:
                time.sleep(1) 


def render_map(nodes) -> str:
    lines = ["Map Structure:"]
    for nid in sorted(nodes):
        node = nodes[nid]
        neigh = ", ".join(nodes[n].name for n in sorted(node.neighbors))
        hosts = ", ".join(h.name for h in node.hosts)
        lines.append(f"  [{nid}] {node.name:20} -> Connects to: [{neigh}] | Hosts: {hosts if hosts else 'None'}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Theme AI Sim")
    parser.add_argument("--turns", type=int, default=15, help="Number of turns")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--theme", type=str, choices=["westworld", "harrypotter"], help="Pre-select theme")
    args = parser.parse_args()

    # Mode Selection
    print("\nSelect Simulation Mode:")
    print("1. Westworld Adventure (Game Mode)")
    print("2. Extreme Debate (Atheists vs Believers)")
    try:
        mode_choice = input("Enter choice (1 or 2): ").strip()
    except EOFError:
        mode_choice = "1"
        
    if mode_choice == "2":
        from debate_sim import run_debate_sim
        run_debate_sim(args.turns)
        return

    if not GEMINI_API_KEY:
        print("\n⚠️  WARNING: GEMINI_API_KEY is not set. The simulation will run in logic-fallback mode.")
    else:
        print(f"\n🧠 AI Enabled (Model: {MODEL_NAME})")

    # Select Theme
    theme: Theme
    if args.theme:
        choice = args.theme
    else:
        print("\nSelect a World Theme:")
        print("1. Westworld (Cowboys, Robots, Mysteries)")
        print("2. Harry Potter (Wizards, Ghosts, Horcruxes)")
        try:
            selection = input("Enter choice (1 or 2): ").strip()
        except EOFError:
             selection = "1"
             
        if selection == "2":
            choice = "harrypotter"
        else:
            choice = "westworld"
    
    if choice == "harrypotter":
        print("⚡ Entering the Wizarding World...")
        theme = HarryPotterTheme()
    else:
        print("🌵 Entering Westworld...")
        theme = WestworldTheme()

    # Build World
    state = build_world(turns=args.turns, seed=args.seed, theme=theme)

    # Run Game
    run_simulation(state, args.turns)

    print("\n" + "="*30)
    print("FINAL REPORT")
    print("="*30)
    print(render_map(state.nodes))
    print("\nNotebook Highlights:")
    # Print last 15 lines of notebook
    for line in state.shared_notebook:
        print(f" - {line}")

    if state.finished:
        print("\nResult: SUCCESS - Mission Accomplished.")
    else:
        print("\nResult: FAILURE - Time ran out.")

if __name__ == "__main__":
    main()
