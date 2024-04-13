from blackjack.twentyone import InfDeck, card_value
import pylab as plt


def test_inf_deck():
    deck = InfDeck()
    dealt_cards = []
    for _ in range(100):
        dealt_cards.append(card_value(deck.deal_card()))
    breakpoint()
    plt.histogram(dealt_cards)
