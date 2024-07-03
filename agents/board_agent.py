import autogen
import chess
import chess.svg
import streamlit as st
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple, Union


# This agent is an adapted version of the one implemented in
# https://github.com/qingyun-wu/autogen-eval/blob/main/application/A6-conversational-chess/agentchat_chess.ipynb
# TODO: print intermediate discussion
class BoardAgent(autogen.AssistantAgent):
    sys_msg = """You are an AI-powered chess board agent.
    You translate user's natural language input into legal UCI moves.
    You should only reply with a UCI move string extracted from user's input."""

    board: chess.Board
    correct_move_messages: Dict[autogen.Agent, List[Dict]]

    def __init__(self, board: chess.Board, config_list: List[Dict], display_as_streamlit: bool = True) -> None:
        super().__init__(
            name="BoardAgent",
            system_message=self.sys_msg,
            llm_config={"temperature": 0.0, "config_list": config_list},
            max_consecutive_auto_reply=10,
        )
        self.register_reply(autogen.ConversableAgent, BoardAgent._generate_board_reply)
        self.board = board
        self.correct_move_messages = defaultdict(list)
        self.display_as_streamlit = display_as_streamlit

    def _generate_board_reply(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[autogen.Agent] = None,
        config: Optional[Any] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        message = messages[-1]
        # extract a UCI move from player's message
        reply = self.generate_reply(
            self.correct_move_messages[sender] + [message],
            sender,
            exclude=[BoardAgent._generate_board_reply]
        )
        uci_move = reply if isinstance(reply, str) else str(reply["content"])
        try:
            self.board.push_uci(uci_move)
        except ValueError as e:
            # invalid move
            return True, f"Error: {e}"
        else:
            # valid move
            m = chess.Move.from_uci(uci_move)
            board = chess.svg.board(
                self.board,
                arrows=[(m.from_square, m.to_square)],
                fill={m.from_square: "gray"},
                size=200
            )
            if self.display_as_streamlit is True:
                # center the SVG image
                centered_board = f"<div style=\"text-align:center;\">{board}</div>"
                st.write(centered_board, unsafe_allow_html=True)
            else:
                from IPython.display import display
                display(
                    chess.svg.board(
                        self.board,
                        arrows=[(m.from_square, m.to_square)],
                        fill={m.from_square: "gray"},
                        size=200,
                    )
                )
            self.correct_move_messages[sender].extend([message, self._message_to_dict(uci_move)])
            self.correct_move_messages[sender][-1]["role"] = "assistant"
            return True, uci_move
