import chess
import chess.svg
import streamlit as st
from autogen import ConversableAgent, register_function
from autogen.agentchat import ChatResult
from functools import partial
from typing import Dict, List
from typing_extensions import Annotated


class ChessBoardState(object):

    def __init__(self) -> None:
        self.board = chess.Board()
        self.made_move = False


# Adapted from https://github.com/microsoft/autogen/blob/main/notebook/agentchat_nested_chats_chess.ipynb
class ChessNestedChatsWrapper(object):

    def __init__(self, config_list: List[Dict], number_of_moves: int) -> None:
        self.number_of_moves = number_of_moves
        self.state = ChessBoardState()

        self.player_white = ConversableAgent(
            name="Player White",
            system_message="You are a chess player and you play as white. "
            "First call get_legal_moves() first, to get list of legal moves. "
            "Then call make_move(move) to make a move.",
            llm_config={"config_list": config_list, "cache_seed": None},
            human_input_mode="NEVER",
        )
        self.player_black = ConversableAgent(
            name="Player Black",
            system_message="You are a chess player and you play as black. "
            "First call get_legal_moves() first, to get list of legal moves. "
            "Then call make_move(move) to make a move.",
            llm_config={"config_list": config_list, "cache_seed": None},
            human_input_mode="NEVER",
        )
        self.board_proxy = ConversableAgent(
            name="Board Proxy",
            llm_config=False,
            # The board proxy will only terminate the conversation if the player has made a move.
            is_termination_msg=partial(self.check_made_move, self.state),
            # The auto reply message is set to keep the player agent retrying until a move is made.
            default_auto_reply="Please make a move.",
            human_input_mode="NEVER",
        )

        self.register_functions()
        self.register_nested_chats()

    def register_functions(self) -> None:
        register_function(
            partial(self.make_move, self.state),
            caller=self.player_white,
            executor=self.board_proxy,
            name="make_move",
            description="Call this tool to make a move.",
        )

        register_function(
            partial(self.get_legal_moves, self.state),
            caller=self.player_white,
            executor=self.board_proxy,
            name="get_legal_moves",
            description="Get legal moves.",
        )

        register_function(
            partial(self.make_move, self.state),
            caller=self.player_black,
            executor=self.board_proxy,
            name="make_move",
            description="Call this tool to make a move.",
        )

        register_function(
            partial(self.get_legal_moves, self.state),
            caller=self.player_black,
            executor=self.board_proxy,
            name="get_legal_moves",
            description="Get legal moves.",
        )

    def register_nested_chats(self) -> None:
        self.player_white.register_nested_chats(
            trigger=self.player_black,
            chat_queue=[
                {
                    # The initial message is the one received by the player agent from
                    # the other player agent.
                    "sender": self.board_proxy,
                    "recipient": self.player_white,
                    # The final message is sent to the player agent.
                    "summary_method": "last_msg",
                }
            ],
        )

        self.player_black.register_nested_chats(
            trigger=self.player_white,
            chat_queue=[
                {
                    # The initial message is the one received by the player agent from
                    # the other player agent.
                    "sender": self.board_proxy,
                    "recipient": self.player_black,
                    # The final message is sent to the player agent.
                    "summary_method": "last_msg",
                }
            ],
        )

    @staticmethod
    def get_legal_moves(state) -> Annotated[str, "A list of legal moves in UCI format"]:
        return "Possible moves are: " + ",".join([str(move) for move in state.board.legal_moves])

    @staticmethod
    def make_move(
            state: ChessBoardState,
            move: Annotated[str, "A move in UCI format."]
    ) -> Annotated[str, "Result of the move."]:
        move = chess.Move.from_uci(move)
        state.board.push_uci(str(move))
        state.made_move = True

        board = chess.svg.board(
            state.board,
            arrows=[(move.from_square, move.to_square)],
            fill={move.from_square: "gray"},
            size=200
        )
        # center the SVG image
        centered_board = f"<div style=\"text-align:center;\">{board}</div>"
        st.write(centered_board, unsafe_allow_html=True)

        # Get the piece name.
        piece = state.board.piece_at(move.to_square)
        piece_symbol = piece.unicode_symbol()
        piece_name = (
            chess.piece_name(piece.piece_type).capitalize()
            if piece_symbol.isupper()
            else chess.piece_name(piece.piece_type)
        )
        msg_tmpl = "Moved {piece_name} ({piece_symbol}) from {from_square} to {to_square}"
        return msg_tmpl.format(
            piece_name=piece_name,
            piece_symbol=piece_symbol,
            from_square=chess.SQUARE_NAMES[move.from_square],
            to_square=chess.SQUARE_NAMES[move.to_square],
        )

    @staticmethod
    def check_made_move(state, msg):
        if state.made_move:
            state.made_move = False
            return True
        else:
            return False

    def initiate_play(self) -> ChatResult:
        return self.player_black.initiate_chat(
            self.player_white,
            message="Let's play chess! Your move.",
            max_turns=self.number_of_moves,
        )
