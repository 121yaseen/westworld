import time
import random
from typing import List
from debate_models import Debater, DebateState
from llm_client import GEMINI_API_KEY
from docs_logger import DocsLogger

def init_debate() -> DebateState:
    # Team Theist (The Believers - New Squad)
    theists = [
        Debater(1, "Sheikh Abdullah", "Theist", "Traditional Islam", 
                "Unapologetic traditionalist. Cites scripture with authority. Believes in objective morality derived solely from Revelation."),
        Debater(2, "Bishop Vance", "Theist", "High Church Christianity", 
                "Focuses on the 'Argument from Beauty' and transcendent experience. Intellectual, poetic, sees God in art and order."),
        Debater(3, "Dr. Aarya", "Theist", "Modern Vedanta/Hinduism", 
                "Quantum Physicist & Mystic. Argues that Consciousness is the ground of all being (Brahman). Science is catching up to the Vedas."),
        Debater(4, "Rabbi Lev", "Theist", "Kabbalist Judaism", 
                "Mystic. Finds hidden patterns and mathematical miracles in the universe. Focuses on the 'Divine Spark' in everyone.")
    ]
    
    # Team Atheist (The Skeptics - New Squad)
    atheists = [
        Debater(5, "Cyber-Punk Zed", "Atheist", "Transhumanism", 
                "We don't need God; we are becoming Gods through tech. Death is a bug to be fixed. Religion is obsolete software."),
        Debater(6, "Empiricus", "Atheist", "Logical Positivism", 
                "If it can't be measured or verified in a lab, it is nonsense. Rejects metaphysics entirely. Cold and analytical."),
        Debater(7, "Sasha Absurdist", "Atheist", "Camus-style Absurdism", 
                "Life has no meaning, and that's funny. Embraces the void. Thinks searching for 'God' is a cowardly escape from freedom."),
        Debater(8, "Historian Marcus", "Atheist", "Mythicism/Critical History", 
                "Deconstructs holy texts as man-made mythology. Points out historical inaccuracies and pagan borrowings. 'God' is a cultural fiction.")
    ]
    
    debaters = theists + atheists
    return DebateState(debaters=debaters)

def run_debate_sim(turns: int):
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY required for Debate Mode.")
        return

    logger = DocsLogger() 
    state = init_debate()
    
    header = "\n" + "="*60 + "\n🔥 THE GREAT DEBATE: GOD vs NO GOD 🔥\n" + "="*60 + "\n"
    print(header)
    logger.log(header) 
    
    # Intro roll call
    print("✨ Team THEIST (United Faiths):")
    logger.log("✨ Team THEIST (United Faiths):")
    for d in state.debaters:
        if d.team == "Theist": 
            line = f" - {d.name} [{d.ideology}]: {d.personality}"
            print(line)
            logger.log(line)
            
    print("\n⚛️  Team ATHEIST (Skeptics):")
    logger.log("\n⚛️  Team ATHEIST (Skeptics):")
    for d in state.debaters:
        if d.team == "Atheist": 
             line = f" - {d.name} [{d.ideology}]: {d.personality}"
             print(line)
             logger.log(line)
    
    print("\n--- DEBATE START ---\n")
    logger.log("\n--- DEBATE START ---\n")
    
    last_speaker_id = -1
    
    for t in range(turns):
        round_header = f"\n[Round {t+1}]"
        print(round_header)
        logger.log(round_header)
        
        # Pick speaker (Preventing immediate repeat)
        # Filter out the person who just spoke
        candidates = [d for d in state.debaters if d.id != last_speaker_id]
        if not candidates:
            candidates = state.debaters # Fallback if only 1 person exists
            
        speaker = random.choice(candidates)
        last_speaker_id = speaker.id
        
        target_team = "Atheist" if speaker.team == "Theist" else "Theist"
        
        # 1. Speak
        print(f"🎤 {speaker.name} ({speaker.team}) takes the mic...")
        argument = speaker.construct_argument(state.history, target_team)
        
        log_arg = f"🎤 {speaker.name} ({speaker.team}): \"{argument}\""
        print(f"   🗣️  \"{argument}\"")
        logger.log(log_arg)
        
        state.history.append(f"{speaker.name} to {target_team}: {argument}")
        
        time.sleep(2)
        
        # 2. Reaction / Conversion Check
        opponents = [d for d in state.debaters if d.team == target_team and not d.is_converted]
        
        if not opponents:
            msg = f"   (No unconverted opponents left in team {target_team}!)"
            print(msg)
            logger.log(msg)
        
        for opp in opponents:
            # Chance to listen
            if random.random() < 0.6: 
                converted = opp.evaluate_conversion(argument, speaker.name, speaker.team)
                if converted:
                    event_msg = ""
                    if speaker.team == "Theist":
                         event_msg = f"🌟 MIRACLE! {opp.name} has found Faith and joined Team THEIST!"
                         opp.personality += " (BELIEVER)"
                    else:
                         event_msg = f"⚫ LOST FAITH! {opp.name} has abandoned God and joined Team ATHEIST!"
                         opp.personality += " (SKEPTIC)"
                    
                    print(f"   {event_msg}")
                    logger.log(f"   >>> {event_msg}")
                         
                    opp.team = speaker.team
                    opp.is_converted = True
                    state.history.append(f"*** SYSTEM: {opp.name} switched to {speaker.team}! ***")
        
        # Check Winner
        theist_count = sum(1 for d in state.debaters if d.team == "Theist")
        atheist_count = sum(1 for d in state.debaters if d.team == "Atheist")
        
        score_line = f"   [Scoreboard: Theists {theist_count} - {atheist_count} Atheists]"
        print(score_line)
        logger.log(score_line)
        
        if atheist_count == 0:
            win_msg = "\n🏆 VICTORY FOR FAITH! The world now believes."
            print(win_msg)
            logger.log(win_msg)
            break
        elif theist_count == 0:
             loss_msg = "\n❌ DEFEAT. God is dead (in this simulation)."
             print(loss_msg)
             logger.log(loss_msg)
             break
            
        time.sleep(1)
