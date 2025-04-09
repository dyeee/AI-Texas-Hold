import random
import json
import re
from typing import List, Dict
from llm_client import LLMClient

RULE_BASE_PATH = "prompt/rule.txt"
CHALLENGE_PROMPT_TEMPLATE_PATH = "prompt/action_prompt_template.txt"
REFLECT_PROMPT_TEMPLATE_PATH = "prompt/reflect_prompt_template.txt"

class Player:
    def __init__(self, name: str, model: str):
        self.name = name
        self.model = model
        self.hand: List[str] = []
        self.chips: int = 0
        self.folded: bool = False
        self.current_bet: int = 0
        self.alive: bool = True
        self.opinions: Dict[str, str] = {}
        self.llm = LLMClient(model)
        self._has_shown_prompt = False
        self._has_shown_reflection_prompt = False

    def reset_chips(self, amount: int):
        self.chips = amount

    def reset_for_next_hand(self):
        self.hand.clear()
        self.folded = False
        self.current_bet = 0
        if self.chips <= 0:
            self.alive = False

    def init_opinions(self, all_players: List['Player']):
        for p in all_players:
            if p.name != self.name:
                self.opinions[p.name] = "（無觀察紀錄）"

    def print_status(self):
        status = "✅ 存活" if self.alive else "☠️ 淘汰"
        print(f"{self.name}｜籌碼: {self.chips}｜手牌: {self.hand}｜{status}")

    def decide_action(self, rule_text: str, action_prompt_template: str, community_cards: List[str], current_bet: int, pot: int) -> str:
        call_amount = current_bet - self.current_bet

        prompt = action_prompt_template.format(
            rules=rule_text,
            hand=self.hand,
            community_cards=community_cards,
            current_bet=current_bet,
            pot=pot,
            call_amount=call_amount
        )

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            action_data = response[0] if isinstance(response, list) else response
            print(f"{self.name} 的回應: {action_data}")

            if 'fold' in action_data:
                return 'fold'
            elif 'check' in action_data:
                return 'check'
            elif 'call' in action_data:
                return 'call'
            elif 'raise' in action_data:
                match = re.search(r'raise\s*(\d+)', action_data)
                if match:
                    return f"raise {match.group(1)}"
                else:
                    return 'raise 50'
            else:
                return 'check'
        except Exception as e:
            print(f"⚠️ {self.name} 決策失敗: {e}")
            return 'check'

    def reflect(self, alive_players: List[str], round_base_info: str, round_action_info: str, round_result: str, reflect_template: str, rule_text: str):
        for other in alive_players:
            if other == self.name:
                continue
            previous_opinion = self.opinions.get(other, "（無先前紀錄）")
            prompt = reflect_template.format(
                rules=rule_text,
                self_name=self.name,
                round_base_info=round_base_info,
                round_action_info=round_action_info,
                round_result=round_result,
                player=other,
                previous_opinion=previous_opinion
            )

            if not self._has_shown_reflection_prompt:
                self._has_shown_reflection_prompt = True

            try:
                response = self.llm.chat([{"role": "user", "content": prompt}])
                updated_opinion = response[0] if isinstance(response, list) else response
                print(f"{self.name} 對 {other} 的新觀察：{updated_opinion}")
                self.opinions[other] = updated_opinion
            except Exception as e:
                print(f"⚠️ {self.name} 反思 {other} 失敗: {e}")