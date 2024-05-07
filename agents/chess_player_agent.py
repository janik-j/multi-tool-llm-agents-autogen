import autogen
import chess.svg
from typing import Dict, List, Optional, Tuple, Union

from agents import BoardAgent


# This agent is an adapted version of the one implemented in
# https://github.com/qingyun-wu/autogen-eval/blob/main/application/A6-conversational-chess/agentchat_chess.ipynb
# TODO: print intermediate discussion
class ChessPlayerAgent(autogen.AssistantAgent):
    sys_msg_tmpl = """Your name is {name} and you are a chess player. 
    You are playing against {opponent_name}. 
    You are playing as {color}. 
    You communicate your move using universal chess interface language.
    You also chit-chat with your opponent when you communicate a move to light up the mood.
    You should make sure both you and the opponent are making legal moves.
    Do not apologize for making illegal moves."""

    def __init__(
        self,
        color: str,
        board_agent: BoardAgent,
        max_turns: int,
        **kwargs,
    ) -> None:
        if color not in ["white", "black"]:
            raise ValueError(f"color must be either white or black, but got {color}")
        opponent_color = "black" if color == "white" else "white"
        name = f"Player {color}"
        opponent_name = f"Player {opponent_color}"
        sys_msg = self.sys_msg_tmpl.format(
            name=name,
            opponent_name=opponent_name,
            color=color,
        )
        super().__init__(
            name=name,
            system_message=sys_msg,
            max_consecutive_auto_reply=max_turns,
            **kwargs,
        )
        self.register_reply(BoardAgent, ChessPlayerAgent._generate_reply_for_board, config=board_agent.board)
        self.register_reply(ChessPlayerAgent, ChessPlayerAgent._generate_reply_for_player, config=board_agent)
        self.update_max_consecutive_auto_reply(board_agent.max_consecutive_auto_reply(), board_agent)

    def _generate_reply_for_board(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[autogen.Agent] = None,
        config: Optional[chess.Board] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        board = config
        # add a system message about the current state of the board.
        board_state_msg = [{"role": "system", "content": f"Current board:\n{board}"}]
        last_message = messages[-1]
        if last_message["content"].startswith("Error"):
            # try again
            last_message["role"] = "system"
            return True, self.generate_reply(
                messages + board_state_msg,
                sender,
                exclude=[ChessPlayerAgent._generate_reply_for_board]
            )
        else:
            return True, None

    def _generate_reply_for_player(
        self,
        messages: Optional[List[Dict]] = None,
        sender: Optional[autogen.Agent] = None,
        config: Optional[BoardAgent] = None,
    ) -> Tuple[bool, Union[str, Dict, None]]:
        board_agent = config
        # add a system message about the current state of the board.
        board_state_msg = [{"role": "system", "content": f"Current board:\n{board_agent.board}"}]
        # propose a reply which will be sent to the board agent for verification.
        message = self.generate_reply(
            messages + board_state_msg,
            sender,
            exclude=[ChessPlayerAgent._generate_reply_for_player]
        )
        if message is None:
            return True, None
        # converse with the board until a legal move is made or max allowed retries.
        # change silent to `False` to see that conversation.
        self.initiate_chat(board_agent, clear_history=False, message=message, silent=self.human_input_mode == "NEVER")
        # last message sent by the board agent
        last_message = self._oai_messages[board_agent][-1]
        if last_message["role"] == "assistant":
            # didn't make a legal move after a limit times of retries.
            print(f"{self.name}: I yield.")
            return True, None
        return True, self._oai_messages[board_agent][-2]
