import chess
from autogen.agentchat import ChatResult
from typing import Dict, List

from agents import BoardAgent, ChessPlayerAgent


class ChessWrapper(object):
    sys_msg_tmpl = """Your name is {name} and you are a chess player. 
    You are playing against {opponent_name}. 
    You are playing as {color}. 
    You communicate your move using universal chess interface language.
    You also chit-chat with your opponent when you communicate a move to light up the mood.
    You should make sure both you and the opponent are making legal moves.
    For every move you communicate, you also draw the chess board after the move.
    You draw the chess board using simple ASCII characters, for example:
    r . b q k b . r
    p p p p . Q p p
    . . n . . n . .
    . . . . p . . .
    . . B . P . . .
    . . . . . . . .
    P P P P . P P P
    R N B . K . N R

    Have fun!
    """

    def __init__(self, config_list: List[Dict], number_of_moves: int) -> None:
        board = chess.Board()
        self.board_agent = BoardAgent(board=board, config_list=config_list)
        self.player_black = ChessPlayerAgent(
            color="black",
            board_agent=self.board_agent,
            max_turns=number_of_moves,
            llm_config={"cache_seed": None, "temperature": 0.5, "config_list": config_list},
        )
        self.player_white = ChessPlayerAgent(
            color="white",
            board_agent=self.board_agent,
            max_turns=number_of_moves,
            llm_config={"cache_seed": None, "temperature": 0.5, "config_list": config_list},
        )

    def initiate_play(self) -> ChatResult:
        return self.player_black.initiate_chat(self.player_white, message="Your turn.")
