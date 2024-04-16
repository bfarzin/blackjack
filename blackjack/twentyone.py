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
np.random.seed(20240414)


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

    def reset(self) -> None:
        self.held = []

    def __repr__(self) -> str:
        return ",".join(self.held)

    def __len__(self) -> int:
        return len(self.held)

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
        self.initial_bank = initial_bank
        self.total_wagered = 0
        self.bankroll = initial_bank
        self.total_hands = 0
        self.hand = Hand()  # make this a list of hands so we can split
        self.hand_wager = None

    def __repr__(self) -> str:
        return f"Player(id={self.id}, bankroll={self.bankroll}, total_hands={self.total_hands}, avg_loss/hand={self.avg_edge_loss} , hand={self.hand})"

    def wager(self) -> float:
        '''Determine wager as fraction of bankroll?'''
        # TODO: Check the table min/max?  Wager according to total count?
        amt = 10
        self.total_wagered += amt
        return amt

    @property
    def avg_edge_loss(self) -> float:
        '''compute the average loss per hand for this player so far'''
        # (start_bank - current_bank) = gain_loss
        # gain_loss / total_hands -> avg gain/loss per hand
        # TODO: what is wager is not uniform?
        return (self.initial_bank - self.bankroll) / self.total_hands if self.total_hands > 0 else 0

    def decision(self, dealer_cards: Hand, cards_shown: List) -> Actions:
        raise NotImplementedError()


class Player17Hit(Player):
    def decision(self, dealer_cards: Hand, cards_shown: List) -> Actions:
        '''basic strategy.  Abstract this away to experiment with other strategies'''
        '''After 100 hands, these seem to be between 0 and 25 bankroll remains.  With static betting'''
        # Return an action depending on the self.hand + dealer and other cards
        if self.hand.value < 17:
            return Actions.HIT
        else:
            return Actions.STAND


class PlayerBasic(Player):
    '''How much can the true basic strategy cut the edge of the house?'''
    def decision(self, dealer_cards: Hand, cards_shown: List) -> Actions:
        '''basic strategy.  Abstract this away to experiment with other strategies'''
        '''
        self.hand.value == 17 --> STAND
        dealers shown card value >= 7 (including A)  --> HIT
        dealers shown card value < 7 && self.hand.value >= 12 --> STAND
        '''
        # Return an action depending on the self.hand + dealer and other cards
        dealer_card_value_7 = (dealer_cards.held[0] == 'A') or (VALUE_MAP[dealer_cards.held[0]] >= 7)
        if self.hand.value >= 17:
            return Actions.STAND
        elif dealer_card_value_7:
            return Actions.HIT
        elif (not dealer_card_value_7) and self.hand.value >= 12:
            return Actions.STAND
        else:
            return Actions.HIT


class PlayerBasic1(Player):
    '''How much can the true basic strategy cut the edge of the house?'''
    def decision(self, dealer_cards: Hand, cards_shown: List) -> Actions:
        '''basic strategy.  Abstract this away to experiment with other strategies'''
        '''
        self.hand.value == 17 --> STAND
        dealers shown card value >= 7 (including A)  --> HIT
        dealers shown card value < 7 && self.hand.value >= 12 --> STAND
        '''
        # Return an action depending on the self.hand + dealer and other cards
        dealer_card_value_7 = (dealer_cards.held[0] == 'A') or (VALUE_MAP[dealer_cards.held[0]] >= 7)
        if self.hand.value >= 17:
            return Actions.STAND
        elif self.hand.value == 11:
            return Actions.DOUBLE
        elif dealer_card_value_7:
            return Actions.HIT
        elif (not dealer_card_value_7) and self.hand.value >= 12:
            return Actions.STAND
        else:
            return Actions.HIT


class Twentyone():
    '''class at the top of the game.  Get players, dealer, hands, payouts'''
    def __init__(self, player: Player, number_players: int = 1):
        self.dealer = player(id=0)
        self.players = [player(id=n + 1) for n in range(number_players)]
        self.deck = InfDeck()

    def inital_deal(self):
        # all players get two cards to start.
        for player in self.players:
            for _ in range(2):
                card = self.deck.deal_card()
                player.hand.hit(card)

        card = self.deck.deal_card()
        self.dealer.hand.hit(card)

    def play(self, n_rounds: int = 1, verbose: bool = False):
        '''
        Outline game play, sequence, totals and payouts.
        Put the parts together and then segment out the objects as needed
        Then build the parts going down to the objects needed.

        0. Player makes initial bet (maybe according to count?)
        1. Inintal deal to each player, two cards each and one card to dealer.
          --> All these cards are seen by all players.
        2. Starting with first player, decision made to Hit, Stand, Double, Split (enum?) list of actions.
        3. Dealer plays with Hit/St and according to standard strategy.
        4. payout determined as 1:1 or 3:2 for player blackjack.
        '''

        for _ in range(n_rounds):

            for player in self.players:
                player.hand_wager = player.wager()

            self.inital_deal()

            # All players act in turn
            for player in self.players:
                # player implements strategy here. Player knows own cards
                cards_shown = []  # TODO: Tabulate all non-dealer cards
                dealer_cards = self.dealer.hand
                while player.hand.value < 21:
                    action = player.decision(dealer_cards, cards_shown)
                    if action is Actions.DOUBLE:
                        # Double wager, single card, stop regardless of total
                        player.hand_wager *= 2
                        card = self.deck.deal_card()
                        player.hand.hit(card)
                        break
                    elif action is Actions.STAND:
                        break
                    elif action is Actions.HIT:
                        card = self.deck.deal_card()
                        player.hand.hit(card)
                    elif action in Actions.SPLIT:
                        # somehow split into two hands for the same player?
                        raise NotImplementedError("Have not done SPLIT of hand yet")
                    else:
                        raise ValueError(f"Action {action} is not valid")

                    if verbose:
                        print(f"Player {player.id} has Total {player.hand.value} from hand {player.hand} AFTER action: {action}")
                    if action is Actions.DOUBLE:
                        breakpoint()

                if verbose and player.hand.value > 21:
                    print(f"bust for player {player.id}")

            # TODO: If all players bust, then dealer does nothing?
            all_player_bust = all([p.hand.value > 21 for p in self.players])
            # Dealer play is simple.  Hit till 17 or more
            if all_player_bust:
                # single card, does not matter, players all busted
                card = self.deck.deal_card()
                self.dealer.hand.hit(card)
            else:
                while self.dealer.hand.value < 17:
                    card = self.deck.deal_card()
                    self.dealer.hand.hit(card)

            # Compare hands, payout to bankroll as needed
            dealer_total = self.dealer.hand.value
            for player in self.players:
                player.total_hands += 1
                if player.hand.value > 21:
                    # player bust, does not matter what dealer got
                    player.bankroll -= player.hand_wager

                elif player.hand.value == dealer_total:
                    # If tie is 21, the natural wins:
                    if player.hand.value == 21:
                        if len(player.hand) == 2 and len(self.dealer.hand) == 2:
                            # both natural, then we just push
                            pass
                        elif len(player.hand) == 2 and len(self.dealer.hand) > 2:
                            # Player natural
                            player.bankroll += player.hand_wager
                        elif len(player.hand) > 2 and len(self.dealer.hand) == 2:
                            # Dealer natural
                            player.bankroll -= player.hand_wager
                        else:
                            # Both 21, neither natural
                            pass
                    # Any other tie, we push
                    pass
                elif dealer_total > 21:
                    # Dealer bust
                    player.bankroll += player.hand_wager
                elif player.hand.value > dealer_total:
                    # Win
                    if player.hand.value == 21 and len(player.hand) == 2:
                        # Natural 21 pays 1.5x
                        player.bankroll += (1.5 * player.hand_wager)
                    else:  # > dealer total
                        player.bankroll += player.hand_wager
                else:  # player.hand.value < dealer_total
                    # Loss
                    player.bankroll -= player.hand_wager
            if verbose:
                for player in self.players:
                    print(f"Player {player.id} has Total {player.hand.value} from hand {player.hand}. Bankroll: {player.bankroll}")
                print(f"Dealer Total {self.dealer.hand.value} from hand {self.dealer.hand}")

            self.dealer.hand = Hand()
            for player in self.players:
                player.hand = Hand()
        print(self.players)


def test_double():
    deck = InfDeck()
    player = PlayerBasic1(id=0)
    player.hand_wager = player.wager()
    player.hand.hit('8')
    player.hand.hit('3')
    dealer_cards = Hand()
    dealer_cards.held = ['4']
    action = player.decision(dealer_cards=dealer_cards, cards_shown=[])
    if action is Actions.DOUBLE:
        player.hand_wager *= 2
        card = deck.deal_card()
        player.hand.hit(card)
    breakpoint()


if __name__ == "__main__":
    # test_double()
    game = Twentyone(player=PlayerBasic1, number_players=5)
    game.play(n_rounds=50000, verbose=False)
    '''Still not qutie right.  After 1000 plays, it is positive for player.  After 5000 even more so.  Missing some condition.'''
