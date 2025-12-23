from dataclasses import dataclass, field
from typing import List, Optional
import json
import random
from llm_client import call_llm

@dataclass
class Debater:
    id: int
    name: str
    team: str  # "Believer" or "Atheist" or "Converted"
    ideology: str  # "Islam", "Christianity", "Judaism", "Hinduism", "Scientific Materialism", "Nihilism", etc.
    personality: str
    is_converted: bool = False
    
    def construct_argument(self, history: List[str], target_team: str) -> str:
        """Generates a debate argument using Web Search for facts."""
        
        # Explicit target definition
        if self.team == "Theist":
            mission = f"Prove the existence of God and the validity of {self.ideology} using logic, science, and history."
        else:
            mission = f"Prove that God is a myth, {self.ideology} is the only reality, and debunk religious claims."
        
        prompt = f"""
        You are {self.name}, representing {self.ideology}. 
        Team: {self.team}. Personality: {self.personality}.
        
        CONTEXT: High-level intellectual debate: Theism vs Atheism.
        MISSION: {mission}
        TARGET: Win over the opposition ({target_team}) by debunking their specific claims and presenting undeniable proofs for your side.
        
        TECHNIQUES TO USE (Choose one):
        - **Steel-manning**: Address the strongest version of their argument.
        - **Reductio ad Absurdum**: Show their logic leads to absurdity.
        - **Empirical Evidence**: Cite specific studies, laws of nature, or historical events.
        - **Socratic Method**: Ask a devastating question.
        
        INSTRUCTIONS:
        1. **Internal Monologue**: First, PLAN your argument. Check recent history. Search for facts.
        2. **The Response**: Then, write your actual spoken response relative to the debate.
           - **CONSTRAINT**: Keep the spoken response CRISP (Max 10 sentences). Be punchy.
        3. **Separation**: You MUST put "###RESPONSE###" between your plan and your spoken response.
        
        RECENT HISTORY:
        {"\n".join(history[-5:])}
        
        FORMAT:
        [Internal Thought Process: "I will use X to debunk Y..."]
        ###RESPONSE###
        [Actual Output Speech (Max 10 sentences)]
        """
        
        # We use a stop sequence to potentially catch runaway generation, though the separator is the main fix.
        # "User:" or "Round" usually won't appear in the speech itself.
        full_output = call_llm(prompt, web_search=True, stop_sequences=["\n[Round", "\nUser:", "###END###"])
        
        # Parse output to fix "Leaky Thought" bug
        if "###RESPONSE###" in full_output:
            _, speech = full_output.split("###RESPONSE###", 1)
            return speech.strip()
        else:
            # Fallback if model forgets separator (rare with this prompt)
            return full_output.strip()

    def evaluate_conversion(self, message: str, speaker_name: str, speaker_team: str) -> bool:
        """Reflects on an argument and decides if converted using a Scoring System."""
        if self.team == speaker_team:
            return False 
            
        prompt = f"""
        You are {self.name} ({self.ideology}).
        You are listening to {speaker_name} ({speaker_team}).
        
        Argument: "{message}"
        
        Your Personality: {self.personality}.
        
        TASK: Evaluate the persuasion level of this argument.
        
        SCORING CRITERIA (0-100):
        - **0-20**: Weak, fallacious, or easily dismissed.
        - **21-50**: Standard argument, I have heard it before. Unconvincing.
        - **51-70**: Good point, makes me think, but does not break my faith.
        - **71-85**: Very strong. Undermines a core pillar of my belief. I am shaken.
        - **86-100**: UNDENIABLE TRUTH. My worldview has collapsed. I must convert.
        
        Logic Check:
        - Did they cite irrefutable evidence?
        - Did they expose a logical contradiction in my view?
        
        Respond in JSON:
        {{
            "thought_process": "Analyze the argument relative to your beliefs.",
            "resistance_score": (Integer 0-100 representing how much you resist),
            "persuasion_score": (Integer 0-100 representing how strong their argument is),
            "converted": true (if persuasion_score > 85) or false
        }}
        """
        try:
            response = call_llm(prompt, json_mode=True)
            data = json.loads(response)
            return data.get("converted", False)
        except:
            return False

@dataclass
class DebateState:
    debaters: List[Debater]
    history: List[str] = field(default_factory=list)
    turn_count: int = 0
    fnished: bool = False
