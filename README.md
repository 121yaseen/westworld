# Westworld - AI-Powered Cooperative Simulation

A text-based cooperative simulation game featuring AI-controlled characters exploring themed worlds, solving mysteries, and engaging in philosophical debates.

## 🎮 Features

### Game Mode

- **Cooperative Exploration**: Six AI-controlled visitors work together to explore a node graph world
- **AI Host Interactions**: Question AI hosts to gather clues and information
- **Shared Notebook**: All visitors share clues and discoveries in a common notebook
- **Multi-Theme Support**: Choose between different themed worlds:
  - **Westworld**: Cowboys, robots, and mysteries in the Wild West
  - **Harry Potter**: Wizards, ghosts, and horcruxes in the wizarding world
- **Victory Condition**: Collect 3 unique clues, then locate and unlock the hidden artifact/horcrux

### Debate Mode

- **Extreme Debate Simulation**: Watch AI debaters engage in philosophical debates
- **Two Teams**: Theists vs Atheists with diverse ideologies
- **Dynamic Conversion**: Debaters can convert opponents to their side based on argument strength
- **Real-time Logging**: Optional Google Docs integration for live debate transcripts

### Chess Mode

- **Human vs Computer**: Play against a custom Strong Python Engine (Negamax + Alpha-Beta Pruning).
- **AI (Gemini) vs Computer**: Watch the Gemini AI Agent (Level 2 Tool User) play against the Python Engine.
  - The AI Agent analyzes candidate moves using the engine as a tool before committing to a move.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Google Gemini API key

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd westworld
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

1. Set up environment variables:

```bash
cp .env.example .env
```

1. Add your Gemini API key to `.env`:

```
GEMINI_API_KEY=your_api_key_here
```

### Running the Simulation

#### Game Mode

Run the main simulation:

```bash
python main.py
```

You'll be prompted to:

1. Choose between Game Mode (1), Debate Mode (2), or Chess Mode (3)
2. Select a theme (Westworld or Harry Potter)
3. The simulation will run for 15 turns by default

**Command-line options:**

```bash
python main.py --turns 20 --seed 42 --theme westworld
```

- `--turns`: Number of turns to run (default: 15)
- `--seed`: Random seed for reproducibility (default: 42)
- `--theme`: Pre-select theme: `westworld` or `harrypotter`

#### Debate Mode

When prompted, select option `2` for Debate Mode. The simulation features:

- 4 Theist debaters (Sheikh Abdullah, Bishop Vance, Dr. Aarya, Rabbi Lev)
- 4 Atheist debaters (Cyber-Punk Zed, Empiricus, Sasha Absurdist, Historian Marcus)
- Dynamic conversion mechanics based on argument strength
- Optional Google Docs logging (requires additional setup)

#### Chess Mode

When prompted, select option `3` for Chess Mode.

- **Sub-mode 1**: Human vs Engine. You play against the Python Engine.
- **Sub-mode 2**: AI (Gemini) vs Engine. The AI Agent plays against the Python Engine.

## 🏗️ Project Structure

```
westworld/
├── main.py              # Main entry point and game loop
├── models.py            # Core data models (Node, Host, Visitor, GameState)
├── world_builder.py     # World generation and graph construction
├── themes.py            # Theme definitions (Westworld, Harry Potter)
├── llm_client.py        # Google Gemini API wrapper
├── debate_sim.py        # Debate mode simulation
├── debate_models.py     # Debate-specific models (Debater, DebateState)
├── chess_sim.py         # Chess mode (Engine + AI Player)
├── docs_logger.py       # Google Docs logging integration
├── requirements.txt     # Python dependencies
└── .env.example        # Environment variable template
```

## 🎯 How It Works

### Game Mode Flow

1. **World Generation**: Creates a connected graph of nodes (locations) based on the selected theme
2. **Host Placement**: AI hosts are placed at various nodes with knowledge (clues and red herrings)
3. **Visitor Initialization**: AI-controlled visitors start at a random location
4. **Turn-Based Gameplay**: Each turn, visitors:
   - Analyze their current situation
   - Decide actions (move, ask hosts, chat with teammates, inspect for artifact)
   - Share discoveries in the shared notebook
5. **Victory**: When a visitor has 3 clues and is at the artifact location, they can unlock it

### AI Decision Making

Visitors use Google Gemini AI to:

- Understand context (location, available hosts, shared notebook)
- Plan strategic actions
- Generate natural language questions and conversations
- Make intelligent movement decisions

### Debate Mode Flow

1. **Team Initialization**: Two teams of 4 debaters each
2. **Round-Based Debates**: Each round, a random debater presents an argument
3. **Conversion Check**: Opponents evaluate arguments and may convert if persuaded
4. **Victory Condition**: First team to convert all opponents wins

### Chess AI Agent (ReAct)

The `AIChessPlayer` uses a ReAct (Reasoning + Acting) loop:

1. **Perceive**: Receives the board state (FEN) and legal moves.
2. **Reason**: Decides which moves to investigate.
3. **Act (Tool Use)**: Calls `analyze_moves()` to simulate outcomes using the internal engine.
4. **Decide**: Commits to the best move using `make_move()`.

## 🔧 Configuration

### Environment Variables

- `GEMINI_API_KEY`: Required for AI functionality. Get one from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Google Docs Logging (Optional)

For debate mode logging to Google Docs:

1. Set up Google Cloud credentials
2. Run: `gcloud auth application-default login --scopes='https://www.googleapis.com/auth/documents,https://www.googleapis.com/auth/drive'`
3. The logger will automatically append to the configured Google Doc

## 🎨 Themes

### Westworld Theme

- **Locations**: Mesa Hub, Sweetwater Plaza, Ghost Ridge, etc.
- **Hosts**: Maeve, Dolores, Teddy, Stubbs, etc.
- **Visitors**: Avery (Analyst), Blake (Diplomat), Cass (Scout)
- **Goal**: Find the hidden Artifact

### Harry Potter Theme

- **Locations**: Great Hall, Potions Dungeon, Forbidden Forest, etc.
- **Hosts**: Nearly Headless Nick, The Bloody Baron, Peeves, etc.
- **Visitors**: Harry (The Chosen One), Hermione (The Brightest Witch), Ron (The Loyal Friend)
- **Goal**: Find the hidden Horcrux

## 📝 Example Output

```
=== TURN 1 ===
🗣️  Avery asked Maeve: 'What can you tell me about this place?' -> Answer: 'This dusty town has seen better days...'
💡 CLUE FOUND: The artifact is hidden in Mesa Hub.
👣 Blake moved from Sweetwater Plaza to Ghost Ridge. (Exploring the area)
💬 Cass says to all: 'I found something interesting at Copper Spur!'
```

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Add new themes
- Improve AI decision-making logic
- Enhance the debate mechanics
- Add new features

## 📄 License

MIT License

## 🙏 Acknowledgments

- Built with Google Gemini AI
- Inspired by Westworld and Harry Potter universes
