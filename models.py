from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any
import random
import json
from llm_client import call_llm, GEMINI_API_KEY

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
        You are {self.name}, a {self.persona}.
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
