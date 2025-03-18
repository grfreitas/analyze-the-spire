from scipy.stats import hypergeom

import random
from itertools import chain, combinations


class Card:
    def __init__(self, name, energy, damage=0, block=0, vulnerable=0, card_type=None):
        self.name = name
        self.energy = energy
        self.damage = damage
        self.block = block
        self.vulnerable = vulnerable
        self.type = card_type

    @classmethod
    def Strike(cls):
        return cls("Strike", energy=1, damage=6, card_type='Attack')

    @classmethod
    def Defend(cls):
        return cls("Defend", energy=1, block=5, card_type='Skill')

    @classmethod
    def Bash(cls):
        return cls("Bash", energy=2, damage=8, vulnerable=2, card_type='Attack')

    def __repr__(self):
        return self.name


class Deck:
    def __init__(self, strikes=5, defends=4, bashes=1):
        self.cards = (
            [Card.Strike() for _ in range(strikes)] +
            [Card.Defend() for _ in range(defends)] +
            [Card.Bash() for _ in range(bashes)]
        )
    

class DrawPile:
    def __init__(self, cards):
        self.cards = cards.copy()
        random.shuffle(self.cards)

    def __repr__(self):
        return str(self.cards)

    def pop_all(self):
        result, self.cards = self.cards, []
        return result

    def reshuffle(self, discard_pile):
        self.cards.extend(discard_pile.cards)
        random.shuffle(self.cards)
        discard_pile.cards = []


class DiscardPile:
    def __init__(self):
        self.cards = []

    def __repr__(self):
        return str(self.cards)


class Hand:
    def __init__(self, draw_pile, discard_pile):
        self.cards = []
        self.cards_played = []
        self.draw_pile = draw_pile
        self.discard_pile = discard_pile

    def __repr__(self):
        return str(self.cards)

    def draw(self, n=5):
        if len(self.draw_pile.cards) < n:
            self.cards.extend(self.draw_pile.pop_all())
            self.draw_pile.reshuffle(self.discard_pile)
    
        for i in range(n - len(self.cards)):
            self.cards.append(self.draw_pile.cards.pop())

    def play(self, card):
        self.cards.remove(card)
        self.discard_pile.cards.append(card)        
    
        self.cards_played.append(card)

    def end_turn(self):
        self.cards_played = []
        self.discard_pile.cards.extend(self.cards)
        self.cards = []


class GameState:
    def __init__(self, deck):
        self.deck = deck
        self.draw_pile = DrawPile(deck.cards)
        self.discard_pile = DiscardPile()
        self.hand = Hand(self.draw_pile, self.discard_pile)
        self.energy = 3
        self.vulnerable_turns = 0
        self.turn_count = 0

    def reset(self):
        self.__init__(self.deck)

    def simulate_turn(self):
        self.turn_count += 1
        self.energy = 3
        self.hand.draw()
        
        current_vulnerable = self.vulnerable_turns > 0
        damage_dealt = self.play_optimal_attacks(current_vulnerable)
        
        if self.vulnerable_turns > 0:
            self.vulnerable_turns -= 1
        
        self.hand.end_turn()
        return damage_dealt

    def play_optimal_attacks(self, current_vulnerable):
        attacks = [card for card in self.hand.cards if card.type == 'Attack']
        best_damage = 0
        best_combo = []

        for combo in chain(*[combinations(attacks, r) for r in range(1, len(attacks)+1)]):
            cost = sum(c.energy for c in combo)
            if cost > self.energy:
                continue

            # Calculate damage with vulnerability effects
            total_damage = 0
            vulnerable_applied = False
            temp_vulnerable = self.vulnerable_turns
            
            for card in combo:
                # Apply damage multiplier if vulnerability was active before playing this card
                multiplier = 1.5 if (current_vulnerable or vulnerable_applied) else 1.0
                total_damage += card.damage * multiplier
                
                # Update vulnerability status
                if card.vulnerable > 0:
                    temp_vulnerable += card.vulnerable
                    vulnerable_applied = True

            # Consider future turns' vulnerability
            future_bonus = 0
            if temp_vulnerable > self.vulnerable_turns:
                future_bonus = (temp_vulnerable - self.vulnerable_turns) * 0.2  # Empirical bonus

            if (total_damage + future_bonus) > best_damage:
                best_damage = total_damage
                best_combo = combo

        # Play the best combination
        for card in best_combo:
            if card in self.hand.cards:
                self.hand.play(card)
                self.energy -= card.energy
                # Update actual vulnerability
                if card.vulnerable > 0:
                    self.vulnerable_turns += card.vulnerable

        return best_damage

    def simulate_battle(self, num_turns=10):
        total_damage = []
        for _ in range(num_turns):
            # Reset vulnerable status at start of turn (if not permanent)
            # self.vulnerable_turns = max(0, self.vulnerable_turns - 1)
            
            # Always simulate full number of turns
            damage = self.simulate_turn()
            total_damage.append(damage)
            
            # For debugging deck cycling:
            # print(f"Turn {_+1}: Draw={len(self.draw_pile.cards)}, Discard={len(self.discard_pile.cards)}")
            
        return total_damage