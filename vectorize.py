import numpy as np
from gamestate import KlonState, get_legal_moves

STOCK = 0
TABLEAU1 = 1
TABLEAU2 = 2
TABLEAU3 = 3
TABLEAU4 = 4
TABLEAU5 = 5
TABLEAU6 = 6
TABLEAU7 = 7
WASTE = 8
FOUNDATION_C = 9
FOUNDATION_D = 10
FOUNDATION_S = 11
FOUNDATION_H = 12
RED = "DH"
BLACK = "CS"
FND_SUITS = "CDSH"
VALUE = 0
SUIT = 1

FNDS = [FOUNDATION_C, FOUNDATION_D, FOUNDATION_S, FOUNDATION_H]

### GENERATING STATE VECTORS

suits = {"C": 1, "D": 2, "S": 3, "H": 4, "c": 5, "d": 6, "s": 7, "h": 8}
intsuits = {v: k for k, v in suits.items()}

values = {
    "A": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
}
intvalues = {v: k for k, v in values.items()}


# padding
PAD = {}
PAD[STOCK] = 24
PAD[WASTE] = 24
PAD[FOUNDATION_C] = 13
PAD[FOUNDATION_D] = 13
PAD[FOUNDATION_S] = 13
PAD[FOUNDATION_H] = 13
PAD[TABLEAU1] = 19
PAD[TABLEAU2] = 19
PAD[TABLEAU3] = 19
PAD[TABLEAU4] = 19
PAD[TABLEAU5] = 19
PAD[TABLEAU6] = 19
PAD[TABLEAU7] = 19


def generate_all_possible_cards():
    cards = []
    for faceup in [True, False]:
        for suit in "CDSH":
            for val in "A23456789TJQK":
                card = f"{val}{suit}"
                if not faceup:
                    card = card.lower()
                cards.append(card)

    cards = np.array(cards)
    return cards


all_cards = generate_all_possible_cards()


def card_to_vec(card):
    ret = (all_cards == card).astype(np.float32)
    assert ret.max() == 1, "invalid card provided"
    return ret


def pile_to_vec(klonstate, pile_idx):
    pile = klonstate[pile_idx]
    z = np.zeros((PAD[pile_idx], len(all_cards)))
    if len(pile) > 0:
        a = np.stack([card_to_vec(c) for c in pile])
        z[: a.shape[0]] = a
    return z


def state_to_vec(klonstate):
    piles = range(STOCK, FOUNDATION_H + 1)
    pilevecs = [pile_to_vec(klonstate, p) for p in piles]
    return np.concatenate(pilevecs)


def vec_to_state(statevec):
    piles = range(STOCK, FOUNDATION_H + 1)
    klonpiles = []
    start = 0
    for pile_idx in piles:
        end = start + PAD[pile_idx]
        pilevec = statevec[start:end]
        cardmsk = pilevec.max(axis=1) == 1
        if not cardmsk.any():
            klonpiles.append(())
        else:
            pile_cards = all_cards[np.argmax(pilevec[cardmsk], axis=1)]
            klonpiles.append(tuple(pile_cards))
        start = end
    return KlonState(*klonpiles)


# first generate all possible moves
def generate_all_possible_moves():
    # Tableau to tableau
    moves = set()
    TABLEAUS = [TABLEAU1, TABLEAU2, TABLEAU3, TABLEAU4, TABLEAU5, TABLEAU6, TABLEAU7]
    for src in TABLEAUS:
        for dest in TABLEAUS:
            if src == dest:
                continue
            # for a given tableau, we can move 13 cards at most
            # this is the max possible number of faceup cards
            for num_to_move in range(1, 14):
                move = f"{src}{dest}"
                if num_to_move > 1:
                    move += f"-{num_to_move}"
                moves.add(move)
    tableau_moves = list(sorted(moves))

    # Tableau to foundation
    tab_to_fnd_moves = []
    for src in TABLEAUS:
        for fnd, fnd_suit in zip(FNDS, FND_SUITS):
            move = f"{src}{fnd_suit}"
            tab_to_fnd_moves.append(move)

    # Waste to tableau
    waste_to_tab_moves = []
    for dest in TABLEAUS:
        move = f"W{dest}"
        waste_to_tab_moves.append(move)

    # Waste to foundation
    waste_to_fnd_moves = []
    for fnd, fnd_suit in zip(FNDS, FND_SUITS):
        move = f"W{fnd_suit}"
        waste_to_fnd_moves.append(move)

    # Foundation to tableau
    fnd_to_tab_moves = []
    for fnd, fnd_suit in zip(FNDS, FND_SUITS):
        for tab in TABLEAUS:
            move = f"{fnd_suit}{tab}"
            fnd_to_tab_moves.append(move)

    # Draw moves
    draw_moves = []
    for draw_count in range(10):  # I think it should be 8 but why not 10
        new_move = f"DR{draw_count+1}"
        draw_moves.append(new_move)

    all_moves = (
        tableau_moves
        + tab_to_fnd_moves
        + waste_to_tab_moves
        + waste_to_fnd_moves
        + fnd_to_tab_moves
        + draw_moves
    )
    return all_moves


all_moves = generate_all_possible_moves()
np_all_moves = np.array(all_moves)


def vector_legal_moves(state):
    moves = list(get_legal_moves(state))
    return np.isin(np_all_moves, moves).astype(np.uint8)
