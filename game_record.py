from typing import List, Dict
import json
import os
from datetime import datetime

class PlayerInitialState:
    def __init__(self, player_name: str, chips: int, hand: List[str]):
        self.player_name = player_name
        self.chips = chips
        self.hand = hand

class GameRecord:
    def __init__(self):
        self.records = []
        self.current_round = {}

    def start_game(self, player_names: List[str]):
        print("🎮 遊戲開始！玩家有：", ", ".join(player_names))

    def start_round(self, round_id: int, round_players: List[str], player_initial_states: List[PlayerInitialState]):
        self.current_round = {
            "round_id": round_id,
            "players": round_players,
            "initial_states": [vars(p) for p in player_initial_states],
            "actions": []
        }
        print(f"--- 第 {round_id} 輪開始 ---")

    def record_play(self, player_name: str, played_cards: List[str], remaining_cards: List[str], play_reason: str, behavior: str, next_player: str, play_thinking: str):
        self.current_round["actions"].append({
            "type": "play",
            "player": player_name,
            "cards": played_cards,
            "remaining": remaining_cards,
            "reason": play_reason,
            "behavior": behavior,
            "next_player": next_player,
            "thinking": play_thinking
        })

    def record_challenge(self, was_challenged: bool, reason: str, result, challenge_thinking: str):
        self.current_round["actions"].append({
            "type": "challenge",
            "challenged": was_challenged,
            "reason": reason,
            "result": result,
            "thinking": challenge_thinking
        })

    def record_shooting(self, shooter_name: str, bullet_hit: bool):
        self.current_round["actions"].append({
            "type": "penalty",
            "shooter": shooter_name,
            "hit": bullet_hit
        })

    def record_text_action(self, text: str):
        self.current_round["actions"].append({"type": "text", "text": text})

    def finish_game(self, winner_name: str):
        print(f"🏁 遊戲結束，勝者是 {winner_name}！")
        self.export_to_json()

    def export_to_json(self):
        os.makedirs("game_records", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"game_records/game_record_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.current_round, f, ensure_ascii=False, indent=2)
        print(f"📁 對戰記錄已儲存：{filename}")

    def get_latest_round_info(self) -> str:
        return f"第 {self.current_round.get('round_id')} 輪，玩家：{', '.join(self.current_round.get('players', []))}"

    def get_latest_round_actions(self, for_player: str, include_latest: bool = True) -> str:
        acts = self.current_round.get("actions", [])
        descriptions = []
        for act in acts:
            if act["type"] == "play":
                descriptions.append(f"{act['player']} 出牌，行為：{act['behavior']}")
            elif act["type"] == "challenge":
                result_str = "成功" if act["result"] else "失敗"
                descriptions.append(f"質疑行為：{act['reason']}（{result_str}）")
        return "\n".join(descriptions)

    def get_latest_play_behavior(self) -> str:
        for act in reversed(self.current_round.get("actions", [])):
            if act["type"] == "play":
                return act["behavior"]
        return ""

    def get_play_decision_info(self, current_player: str, next_player: str) -> str:
        return f"目前輪到你（{current_player}）對 {next_player} 出牌，請謹慎考慮行為與表現。"

    def get_challenge_decision_info(self, player_name: str, target_player: str) -> str:
        return f"你是下一位玩家（{player_name}），請判斷是否要質疑 {target_player} 的出牌行為。"

    def get_latest_round_result(self, player_name: str) -> str:
        return "上一輪已結束，你可依據觀察反思對手表現。"