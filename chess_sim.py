import chess
import time
import random
import json
from typing import List, Dict, Optional, Any
from llm_client import call_llm

# --- Evaluation Tables (Simplified Sunfish/Stockfish style) ---
# Values for [Pawn, Knight, Bishop, Rook, Queen, King]
PIECE_VALUES = [100, 320, 330, 500, 900, 20000]

# Piece-Square Tables (white perspective)
# 1D array of 64 values, a1=0, b1=1 ... h8=63
pst = {
    chess.PAWN: (
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ),
    chess.KNIGHT: (
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50,
    ),
    chess.BISHOP: (
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ),
    chess.ROOK: (
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ),
    chess.QUEEN: (
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ),
    chess.KING: (
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    )
}

class StrongPythonEngine:
    """
    An improved pure-Python chess engine using Negamax, Alpha-Beta Pruning,
    Piece-Square Tables, and Move Ordering.
    Strength: Significantly better than random/basic minimax (~1500-1800 ELO depending on hardware).
    """

    def __init__(self, time_limit: float = 2.0):
        self.time_limit = time_limit
        self.nodes_visited = 0
        self.start_time = 0

    def evaluate(self, board: chess.Board) -> int:
        """
        Static evaluation of the board position.
        Positive score = Good for White.
        Negative score = Good for Black.
        """
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        pm = board.piece_map()
        
        for square, piece in pm.items():
            material = PIECE_VALUES[piece.piece_type - 1]
            
            if piece.color == chess.WHITE:
                rank = chess.square_rank(square)
                file = chess.square_file(square)
                # Formula: (7 - rank) * 8 + file
                table_idx = (7 - rank) * 8 + file
                
                positional = pst[piece.piece_type][table_idx]
                score += (material + positional)
                
            else:
                rank = chess.square_rank(square)
                file = chess.square_file(square)
                rank_w = 7 - rank
                table_idx = (7 - rank_w) * 8 + file
                
                positional = pst[piece.piece_type][table_idx]
                score -= (material + positional)

        return score

    def quiescence(self, board: chess.Board, alpha: int, beta: int) -> int:
        self.nodes_visited += 1
        
        # If in check, we must search all moves to avoid illegal stand-pat or missing checkmate
        in_check = board.is_check()
        
        if not in_check:
            stand_pat = self.evaluate(board)
            if board.turn == chess.BLACK:
                stand_pat = -stand_pat

            if stand_pat >= beta:
                return beta
            if alpha < stand_pat:
                alpha = stand_pat
        
        legal_moves = list(board.legal_moves)
        
        if in_check:
            # Search all moves if in check (evasions)
            moves_to_search = legal_moves
        else:
            # Otherwise only captures
            moves_to_search = [m for m in legal_moves if board.is_capture(m)]

        # Move ordering: MVV-LVA
        moves_to_search.sort(key=lambda m: 0 if not board.piece_at(m.to_square) else PIECE_VALUES[board.piece_at(m.to_square).piece_type - 1], reverse=True)

        for move in moves_to_search:
            board.push(move)
            score = -self.quiescence(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
                
        return alpha

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int) -> int:
        self.nodes_visited += 1
        
        if depth == 0:
            return self.quiescence(board, alpha, beta)
            
        if board.is_game_over():
            if board.is_checkmate():
                # We (side to move) are mated. Return very low score.
                # Penalize by depth so engine prefers faster mates.
                return -99999 + depth 
            return 0 # Draw

        legal_moves = list(board.legal_moves)
        
        # Move Ordering
        def move_score(move):
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                val = PIECE_VALUES[victim.piece_type - 1] if victim else 0
                return 1000 + val
            return 0
            
        legal_moves.sort(key=move_score, reverse=True)
        
        max_score = -float('inf')
        
        for move in legal_moves:
            board.push(move)
            score = -self.negamax(board, depth - 1, -beta, -alpha)
            board.pop()
            
            if score > max_score:
                max_score = score
                
            if max_score > alpha:
                alpha = max_score
                
            if alpha >= beta:
                # DEBUG
                if True: # Always print for now to debug
                   # print(f"Move: {move}, Score: {score}")
                   pass
                break # Pruning
                
        return max_score

    def get_best_move(self, board: chess.Board) -> chess.Move:
        self.nodes_visited = 0
        self.start_time = time.time()
        
        best_move = None
        alpha = -float('inf')
        beta = float('inf')
        
        current_depth = 1
        max_depth = 4 # Cap
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
            
        # Initial sort
        legal_moves.sort(key=lambda m: 1 if board.is_capture(m) else 0, reverse=True)
        
        print(f"Thinking...", end="", flush=True)
        
        while current_depth <= max_depth:
            depth_best_move = None
            depth_best_score = -float('inf')
            
            # Reset alpha/beta for each depth
            alpha = -float('inf')
            beta = float('inf')
            
            for move in legal_moves:
                board.push(move)
                score = -self.negamax(board, current_depth - 1, -beta, -alpha)
                board.pop()
                
                if score > depth_best_score:
                    depth_best_score = score
                    depth_best_move = move
                
                if score > alpha:
                    alpha = score
                    
                if time.time() - self.start_time > self.time_limit:
                    break
            
            if time.time() - self.start_time > self.time_limit:
                if depth_best_move and not best_move:
                    best_move = depth_best_move
                break
            else:
                best_move = depth_best_move
                print(f" [D{current_depth}]", end="", flush=True)
                current_depth += 1
                
        elapsed = time.time() - self.start_time
        print(f"\nEngine played {best_move} (Depth {current_depth-1}, Nodes: {self.nodes_visited}, Time: {elapsed:.2f}s)")
        return best_move

class AIChessPlayer:
    """
    AI Player powered by Gemini using Function Calling (Simulated).
    Level 2: Active Tools.
    """
    def __init__(self, color: bool, engine: StrongPythonEngine):
        self.color = color # True = White, False = Black
        self.engine = engine
        self.name = "Gemini Grandmaster"

    def get_move(self, board: chess.Board) -> chess.Move:
        legal_moves_list = [m.uci() for m in board.legal_moves]
        san_moves_list = [board.san(m) for m in board.legal_moves]
        
        # Provide both UCI and SAN for convenience
        moves_map = {board.san(m): m.uci() for m in board.legal_moves}
        
        prompt_history = []
        
        system_prompt = f"""
        You are a Chess Grandmaster AI. You are playing as {'White' if self.color else 'Black'}.
        Your goal is to defeat the opponent engine.
        
        TOOLS AVAILABLE:
        1. analyze_moves(moves: List[str]) -> Dict[str, int]
           - Input: List of moves in SAN notation (e.g., ["e4", "Nf3"]).
           - Output: Evaluation score for each move (Higher is better for White, Lower is better for Black).
           - Use this to check if a move is a blunder or a good idea.
        
        2. make_move(move: str)
           - Input: The final move you choose in SAN notation (e.g., "e4").
           - This ends your turn.

        INSTRUCTIONS:
        - Analyze the position.
        - Use `analyze_moves` to check 2-3 candidate moves if you are unsure.
        - Select the best move using `make_move`.
        - Do NOT explain your reasoning to the user. Just use the tools.
        - Respond ONLY in JSON format.
        
        FORMAT:
        {{
            "tool": "analyze_moves" | "make_move",
            "args": {{ ... }}
        }}
        """
        
        # Initial Context
        turn_context = f"""
        CURRENT BOARD (FEN): {board.fen()}
        LEGAL MOVES (SAN): {json.dumps(san_moves_list)}
        
        Choose your action.
        """
        
        max_turns = 3
        current_turn = 0
        
        while current_turn < max_turns:
            full_prompt = system_prompt + "\n" + "\n".join(prompt_history) + "\n" + turn_context
            
            try:
                response = call_llm(full_prompt, json_mode=True)
                if not response:
                     raise ValueError("Empty response from LLM")
                     
                action = json.loads(response)
                tool_name = action.get("tool")
                args = action.get("args", {})
                
                if tool_name == "make_move":
                    move_san = args.get("move")
                    if move_san in moves_map:
                        return board.parse_san(move_san)
                    elif move_san in legal_moves_list: # Handle UCI fallback
                        return chess.Move.from_uci(move_san)
                    else:
                        # AI Hallucinated move, random fallback
                        return random.choice(list(board.legal_moves))
                        
                elif tool_name == "analyze_moves":
                    candidates = args.get("moves", [])
                    results = {}
                    for m_san in candidates:
                        try:
                            # Convert SAN to Move object
                            # We need to be careful: parsing SAN requires board context
                            move_obj = None
                            try:
                                move_obj = board.parse_san(m_san)
                            except:
                                # Try UCI if SAN fails
                                try:
                                    move_obj = chess.Move.from_uci(m_san)
                                except:
                                    pass
                            
                            if move_obj and move_obj in board.legal_moves:
                                board.push(move_obj)
                                # Evaluate returns static score of position
                                score = self.engine.evaluate(board)
                                results[m_san] = score
                                board.pop()
                            else:
                                results[m_san] = "Invalid Move"
                        except Exception:
                            results[m_san] = "Error"
                    
                    # Feed result back to LLM
                    tool_output = f"TOOL RESULT (analyze_moves): {json.dumps(results)}"
                    prompt_history.append(f"AI: {response}")
                    prompt_history.append(tool_output)
                    current_turn += 1
                    continue
                
                else:
                     # Unknown tool, force random move to avoid stall
                     return random.choice(list(board.legal_moves))

            except Exception as e:
                # print(f"AI Error: {e}")
                pass
                
        # Fallback if max turns reached
        return random.choice(list(board.legal_moves))


def render_board(board: chess.Board):
    print("\n" + str(board) + "\n")

def run_chess_sim():
    print("\n=== CHESS MODE ===")
    print("1. Human vs Engine")
    print("2. AI (Gemini) vs Engine")
    
    choice = input("Select mode (1 or 2): ").strip()
    
    board = chess.Board()
    engine = StrongPythonEngine(time_limit=2.0) # Used for both opponent and AI tool
    
    player_is_ai = (choice == "2")
    
    # Choose side
    while True:
        user_side_str = input(f"Play as White (w) or Black (b)? {'(AI will take this side)' if player_is_ai else ''} ").lower()
        if user_side_str in ['w', 'b', 'white', 'black']:
            break
            
    white_player_is_main = user_side_str.startswith('w')
    
    # Setup AI if needed
    ai_agent = None
    if player_is_ai:
        ai_agent = AIChessPlayer(color=white_player_is_main, engine=engine)
        print(f"\n🧠 AI Agent initialized. It will play as {'White' if white_player_is_main else 'Black'}.")
    
    while not board.is_game_over():
        render_board(board)
        
        is_main_turn = (board.turn == chess.WHITE and white_player_is_main) or \
                       (board.turn == chess.BLACK and not white_player_is_main)
        
        turn_name = "White" if board.turn == chess.WHITE else "Black"
        
        if is_main_turn:
            if player_is_ai:
                print(f"🤖 {turn_name} (AI) is thinking...")
                move = ai_agent.get_move(board)
                print(f"AI plays: {board.san(move)}")
                board.push(move)
            else:
                # Human Turn
                move_str = input(f"{turn_name} to move: ").strip()
                if move_str.lower() in ['quit', 'exit']:
                    break
                try:
                    try:
                        move = board.parse_san(move_str)
                    except ValueError:
                        move = board.parse_uci(move_str)
                    
                    if move in board.legal_moves:
                        board.push(move)
                    else:
                        print("Illegal move, try again.")
                except ValueError:
                    print("Invalid move format.")
        else:
            # Engine Turn
            print(f"⚙️  {turn_name} (Python Engine) is thinking...")
            best_move = engine.get_best_move(board)
            if best_move:
                board.push(best_move)
            else:
                print("Engine resigns.")
                break
    
    print("\nGame Over!")
    print(f"Result: {board.result()}")
    render_board(board)

if __name__ == "__main__":
    run_chess_sim()
