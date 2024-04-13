'''
* Setup an enviornment with a Deck object (can be finite or infite cards)
* deal/call the cards from that deck
* another game player envirionment that will allows actions
* dealer automatic play - hit on cards, etc.  
* payout module.  produce the payouts for differen end states of the game
'''
import numpy as np
from enum import Enum
from typing import List


CARDS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUE_MAP = {'2': 2, '3': 3, '4': 4, '5': 5,
             '6': 6, '7': 7, '8': 8, '9': 9,
             '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 1}


class Actions(Enum):
    HIT = 1
    STAND = 2
    SPLIT = 3
    DOUBLE = 4


def card_value(card: str) -> float:
    '''compute the value of a card'''
    return VALUE_MAP[card]


class Deck():
    '''implements a deck of cards'''
    def __init__(self):
        pass

    def deal_card(self):
        raise NotImplementedError()


class InfDeck(Deck):
    '''infinite deck of cards.  All cards can come with equal prob'''
    def __init__(self, possible_cards=CARDS):
        self.cards = possible_cards

    def deal_card(self):
        '''deal a single card from the infinite deck'''
        return np.random.choice(self.cards)


class NumDecks(Deck):
    '''shoe of number of deck of cards'''
    # TODO: implement re-shuffle at low number cards
    # TODO: implement memory of the cards in the deck. only deal what remain
    #       this is important if we want to count the cards.
    def __init__(self, num_decks=1):
        self.num_decks = num_decks


class Hand():
    '''represent a hand in blackjack, compute the value of the hand'''
    # TODO: should I care about cards that are hidden/shown?
    def __init__(self):
        self.reset()

    def __repr__(self) -> str:
        return ",".join(self.held)

    def reset(self) -> None:
        self.held = []

    def hit(self, card: str) -> None:
        self.held.append(card)

    @property
    def value(self) -> int:
        # all non-ace values are static
        value = sum([card_value(card) for card in self.held if card != "A"])
        if "A" in self.held:
            for card in self.held:
                if card == "A":
                    value += (1 if value+11 > 21 else 11)

        return value


class Player():
    '''player with a bankroll that can win/lose hands'''
    def __init__(self, id: int = None, initial_bank: float = 1000):
        self.id = id
        self.bankroll = initial_bank
        self.hand = Hand()
        self.hand_wager = None

    def __repr__(self) -> str:
        return f"Player(id={self.id}, bankroll={self.bankroll}, hand={self.hand})"

    def wager(self) -> float:
        '''Determine wager as fraction of bankroll?'''
        # TODO: Check the table min/max?  Wager according to total count?
        return 10

    def decision(self, dealer_cards: Hand, cards_shown: List) -> Actions:
        '''basic strategy.  Abstract this away to experiment with other strategies'''
        # Return an action depending on the self.hand + dealer and other cards
        if self.hand.value >= 20:
            return Actions.STAND
        elif self.hand.value < 17:
            return Actions.HIT
        else:
            return Actions.STAND


class Twentyone():
    '''class at the top of the game.  Get players, dealer, hands, payouts'''
    def __init__(self, number_players=1):
        self.dealer = Player(id=0)
        self.players = [Player(id=n + 1) for n in range(number_players)]
        self.deck = InfDeck()

    def inital_deal(self):
        # all players get two cards to start.
        for player in self.players:
            for _ in range(2):
                card = self.deck.deal_card()
                player.hand.hit(card)

        card = self.deck.deal_card()
        self.dealer.hand.hit(card)

    def play(self):
        '''
        Outline game play, sequence, totals and payouts.
        Put the parts together and then segment out the objects as needed
        Then build the parts going down to the objects needed.

        0. Player makes initial bet (maybe according to count?)
        1. Inintal deal to each player, two cards each and one card to dealer.
          --> All these cards are seen by all players.
        2. Starting with first player, decision made to Hit, Stand, Double, Split (enum?) list of actions.
        3. Dealer plays with Hit/Stand according to standard strategy.
        4. payout determined as 1:1 or 3:2 for player blackjack.
        '''

        for player in self.players:
            player.hand_wager = player.wager()

        self.inital_deal()

        # All players act in turn
        for player in self.players:
            # player implements strategy here. Player knows own cards
            cards_shown = []  # TODO: Tabulate all non-dealer cards
            dealer_cards = self.dealer.hand
            while player.hand.value <= 21:
                action = player.decision(dealer_cards, cards_shown)
                print(f"Player {player.id} has Total {player.hand.value} from hand {player.hand} action: {action}")

                if action is Actions.STAND:
                    break
                elif action is Actions.HIT:
                    card = self.deck.deal_card()
                    player.hand.hit(card)
                elif action in Actions.DOUBLE:
                    pass
                elif action in Actions.SPLIT:
                    # somehow split into two hands for the same player?
                    pass
                else:
                    raise ValueError(f"Action {action} is not valid")

            if player.hand.value > 21:
                print(f"bust for player {player.id}")

        print(self.players)
        # Dealer play is simple.
        while self.dealer.hand.value < 17:
            card = self.deck.deal_card()
            self.dealer.hand.hit(card)

        # Compare hands, payout to bankroll as needed
        ''' what are blackjack payouts?'''
        dealer_total = self.dealer.hand.value
        for player in self.players:
            if player.hand.value == dealer_total:
                # Push, there is no payout.
                pass
            elif player.hand.value > dealer_total:
                # Win
                if player.hand.value == 21:  # blackjack
                    player.bankroll += (1.5 * player.hand_wager)
                if player.hand.value > 21:  # bust
                    player.bankroll -= player.hand_wager
                else:  # > dealer total
                    player.bankroll += player.hand_wager
            else:  # player.hand.value < dealer_total
                # Loss
                player.bankroll -= player.hand_wager
        print(f"Dealer Total {self.dealer.hand.value} from hand {self.dealer.hand}")
        for player in self.players:
            print(f"Player {player.id} has Total {player.hand.value} from hand {player.hand}. Bankroll: {player.bankroll}")
        breakpoint()


def test_decision():
    '''
    Player 2 has Total 13 from hand 5,8 action: Actions.HIT
    Player 2 has Total 20 from hand 5,8,7 action: Actions.HIT
    Player 2 has Total 21 from hand 5,8,7,A action: Actions.HIT
    bust for player 2
    '''
    player = Player()
    player.hand.hit('5')
    player.hand.hit('8')
    action = player.decision([], [])
    print(f"Player {player.id} has Total {player.hand.value} from hand {player.hand} action: {action}")
    player.hand.hit('7')
    action = player.decision([], [])
    print(f"Player {player.id} has Total {player.hand.value} from hand {player.hand} action: {action}")
    player.hand.hit('A')
    action = player.decision([], [])
    print(f"Player {player.id} has Total {player.hand.value} from hand {player.hand} action: {action}")
    breakpoint()


if __name__ == "__main__":
    # test_decision()
    game = Twentyone(number_players=3)
    game.play()
