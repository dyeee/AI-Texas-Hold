import random
from typing import List, Optional, Dict
from player import Player
from game_record import GameRecord, PlayerInitialState
from treys import Card, Evaluator
import os

class Game:
    def __init__(self, player_configs: List[Dict[str, str]]):
        self.players = [Player(config["name"], config["model"]) for config in player_configs]
        self.deck: List[str] = []
        self.community_cards: List[str] = []
        self.pot: int = 0
        self.current_bet: int = 0
        self.dealer_index: int = 0
        self.small_blind: int = 10
        self.big_blind: int = 20
        self.evaluator = Evaluator()

        for player in self.players:
            player.reset_chips(1000)

        self.game_record = GameRecord()

        with open(os.path.join("prompt", "rule.txt"), encoding="utf-8") as f:
            self.rule_text = f.read()
        with open(os.path.join("prompt", "action_prompt_template.txt"), encoding="utf-8") as f:
            self.action_template = f.read()
        with open(os.path.join("prompt", "reflect_prompt_template.txt"), encoding="utf-8") as f:
            self.reflect_template = f.read()

    def _create_deck(self) -> List[str]:
        suits = ['H', 'D', 'C', 'S']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [r + s for s in suits for r in ranks]

    def deal_hole_cards(self):
        self.deck = self._create_deck()
        random.shuffle(self.deck)
        for player in self.players:
            if not player.alive:
                continue
            player.hand.clear()
            player.hand.append(self.deck.pop())
            player.hand.append(self.deck.pop())
            print(f"{player.name} 的手牌是 {player.hand}")

    def deal_community_cards(self, stage: str):
        if stage == 'flop':
            self.community_cards = [self.deck.pop(), self.deck.pop(), self.deck.pop()]
        elif stage == 'turn':
            self.community_cards.append(self.deck.pop())
        elif stage == 'river':
            self.community_cards.append(self.deck.pop())
        print(f"公共牌：{self.community_cards}")

    def betting_round(self):
        for player in self.players:
            if player.folded or not player.alive:
                continue

            action = player.decide_action(
                rule_text=self.rule_text,
                action_prompt_template=self.action_template,
                community_cards=self.community_cards,
                current_bet=self.current_bet,
                pot=self.pot
            )

            if action == 'fold':
                player.folded = True
                print(f"{player.name} 棄牌")
            elif action == 'check':
                print(f"{player.name} 過牌")
            elif action == 'call':
                call_amount = self.current_bet - player.current_bet
                player.chips -= call_amount
                player.current_bet += call_amount
                self.pot += call_amount
                print(f"{player.name} 跟注 {call_amount}")
            elif action.startswith('raise'):
                raise_amount = int(action.split()[1])
                self.current_bet += raise_amount
                player.chips -= self.current_bet
                player.current_bet = self.current_bet
                self.pot += self.current_bet
                print(f"{player.name} 加注至 {self.current_bet}")

    def evaluate_hand(self, hand: List[str], community: List[str]) -> int:
        full_hand = hand + community
        treys_hand = [Card.new(card.replace('H', 'h').replace('D', 'd').replace('C', 'c').replace('S', 's')) for card in full_hand]
        hole = treys_hand[:2]
        board = treys_hand[2:]
        return self.evaluator.evaluate(board, hole)

    def showdown(self):
        live_players = [p for p in self.players if not p.folded and p.alive]
        best_score = float('inf')
        winner = None

        print("\n-- 攤牌階段 --")
        for player in live_players:
            score = self.evaluate_hand(player.hand, self.community_cards)
            print(f"{player.name} 手牌：{player.hand}，評分：{score}")
            if score < best_score:
                best_score = score
                winner = player

        if winner:
            winner.chips += self.pot
            print(f"🏆 {winner.name} 贏得底池 {self.pot}！目前籌碼：{winner.chips}")
        else:
            print("平局，底池保留")

        self.pot = 0
        for player in self.players:
            player.reset_for_next_hand()

        print("\n-- 存活玩家狀態 --")
        for p in self.players:
            if p.chips <= 0:
                p.alive = False
            status = "✅ 存活" if p.alive else "☠️ 淘汰"
            print(f"{p.name}: {status}（籌碼: {p.chips}）")

        for player in live_players:
            player.reflect(
                alive_players=[p.name for p in live_players],
                round_base_info=self.game_record.get_latest_round_info(),
                round_action_info=self.game_record.get_latest_round_actions(player.name),
                round_result="攤牌完成，請根據對手行為與最終手牌進行反思。",
                reflect_template=self.reflect_template,
                rule_text=self.rule_text
            )

        self.check_victory()

    def check_victory(self) -> bool:
        alive_players = [p for p in self.players if p.alive]
        if len(alive_players) == 1:
            winner = alive_players[0]
            print(f"\n🎉 遊戲結束！勝者是 {winner.name}！")
            self.game_record.finish_game(winner.name)
            return True
        return False

    def start_game(self):
        for player in self.players:
            player.init_opinions(self.players)

        self.deal_hole_cards()
        self.deal_community_cards("flop")
        self.betting_round()
        self.deal_community_cards("turn")
        self.betting_round()
        self.deal_community_cards("river")
        self.betting_round()
        self.showdown()

if __name__ == '__main__':
    player_configs = [
        {"name": "DeepSeek", "model": "deepseek-r1:7b"},
        {"name": "llama3", "model": "llama3"}
    ]

    print("遊戲開始！玩家配置如下：")
    for config in player_configs:
        print(f"玩家：{config['name']}, 模型：{config['model']}")
    print("-" * 50)

    game = Game(player_configs)
    game.start_game()