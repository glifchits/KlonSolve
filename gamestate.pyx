# cython: language_level=3, c_string_type=bytes, c_string_encoding=ascii
cimport cython
import numpy as np
from collections import namedtuple


KlonState = namedtuple(
    "KlonState",
    [
        "stock",
        "tableau1",
        "tableau2",
        "tableau3",
        "tableau4",
        "tableau5",
        "tableau6",
        "tableau7",
        "waste",
        "foundation1",
        "foundation2",
        "foundation3",
        "foundation4",
    ],
)

DEF STOCK = 0
DEF TABLEAU1 = 1
DEF TABLEAU2 = 2
DEF TABLEAU3 = 3
DEF TABLEAU4 = 4
DEF TABLEAU5 = 5
DEF TABLEAU6 = 6
DEF TABLEAU7 = 7
DEF WASTE = 8
DEF FOUNDATION_C = 9
DEF FOUNDATION_D = 10
DEF FOUNDATION_S = 11
DEF FOUNDATION_H = 12

DEF RED = "DH"
DEF BLACK = "CS"
DEF FND_SUITS = "CDSH"
DEF VALUE = 0
DEF SUIT = 1

cdef FNDS = [FOUNDATION_C, FOUNDATION_D, FOUNDATION_S, FOUNDATION_H]


def irange(start, stop):
    """ inclusive range """
    if start <= stop:
        return range(start, stop + 1)
    elif start > stop:
        return range(start, stop - 1, -1)


cdef int can_stack(char* card, char* onto):
    """ `card` is the card to move, `onto` is the card to stack onto """
    cdef int cs = card[SUIT]
    cdef int os = onto[SUIT]
    cdef int C = 67
    cdef int D = 68
    cdef int S = 83
    cdef int H = 72
    if (cs == D or cs == H) and (os == D or os == H):
        return 0
    if (cs == C or cs == S) and (os == C or os == S):
        return 0
    return cards_in_value_order(card, onto)


cdef int cards_in_value_order(char* card, char* onto):
    cdef int cv = card[0]
    cdef int ov = onto[0]
    return 1 if (
        ((cv == 65 or cv == 97) and (ov == 50)) or               # Aa to 2
        ((cv == 50) and (ov == 51)) or                           # 2 to 3
        ((cv == 51) and (ov == 52)) or                           # 3 to 4
        ((cv == 52) and (ov == 53)) or                           # 4 to 5
        ((cv == 53) and (ov == 54)) or                           # 5 to 6
        ((cv == 54) and (ov == 55)) or                           # 6 to 7
        ((cv == 55) and (ov == 56)) or                           # 7 to 8
        ((cv == 56) and (ov == 57)) or                           # 8 to 9
        ((cv == 57) and (ov == 84 or ov == 116)) or              # 9 to Tt
        ((cv == 84 or cv == 116) and (ov == 74 or ov == 106)) or # Tt to Jj
        ((cv == 74 or cv == 106) and (ov == 81 or ov == 113)) or # Jj to Qq
        ((cv == 81 or cv == 113) and (ov == 75 or ov == 107))    # Qq to Kk
    ) else 0


cdef int card_is_ace(char* card):
    cdef int ACE = 65
    cdef int cv = card[0]
    return cv == ACE


cdef int card_is_king(char* card):
    cdef int KING = 75
    cdef int cv = card[0]
    return cv == KING


@cython.boundscheck(False)
def get_draw_moves(state):
    if len(state.stock) == 0 and len(state.waste) == 0:
        return set()
    st = copy(state)
    draw_moves = set()
    seen_top_cards = set()
    if len(st[WASTE]) > 0:
        seen_top_cards.add(st[WASTE][-3:])  # current waste is available
    for draw_count in range(100):  # should be way more than enough
        if len(st[STOCK]) == 0:
            st = replace_stock(st)
        st = draw(st)
        new_move = f"DR{draw_count+1}"
        top_waste = st[WASTE][-3:]
        if top_waste in seen_top_cards: # cycled through
            return draw_moves
        seen_top_cards.add(top_waste)
        draw_moves.add(new_move)
    return draw_moves


@cython.boundscheck(False)
cdef tableau_to_tableau(state):
    # TABLEAU1 = 1 and TABLEAU7 = 7
    # range(1, 8) is all tableau indices
    FACEUP = {}
    moves = set()
    for tab in range(1, 8):
        pile = state[tab]
        fu = count_face_up(pile)
        FACEUP[tab] = pile[-fu:]

    cdef Py_ssize_t idx
    for src in range(1, 8):
        for dest in range(1, 8):
            if src == dest:
                continue
            num_to_move = 1
            faceup = FACEUP[src]
            idx = len(faceup) - 1
            while idx >= 0:
                state_dest = state[dest]
                src_card = faceup[idx]
                if len(state_dest) == 0:  # tableau empty
                    # only move a king to empty tableau if not the entire stack
                    # this would be a useless move
                    if card_is_king(src_card) and len(state[src]) > num_to_move:
                        move = f"{src}{dest}"
                        if num_to_move > 1:
                            move += f"-{num_to_move}"
                        moves.add(move)
                elif can_stack(src_card, state_dest[-1]):
                    move = f"{src}{dest}"
                    if num_to_move > 1:
                        move += f"-{num_to_move}"
                    moves.add(move)
                num_to_move += 1
                idx -= 1
    return moves


@cython.boundscheck(False)
cdef tableau_to_foundation(state):
    moves = set()
    for src in range(1, 8):
        if len(state[src]) == 0:
            continue  # can't move empty to foundation
        src_top = state[src][-1]
        # for fnd, fnd_suit in zip(FNDS, FND_SUITS):
        for fnd_i in range(0, 4):
            fnd = FNDS[fnd_i]
            fnd_suit = FND_SUITS[fnd_i]
            if len(state[fnd]) == 0:
                if card_is_ace(src_top) and src_top[SUIT] == fnd_suit:
                    move = f"{src}{fnd_suit}"
                    moves.add(move)
            else:
                fnd_top = state[fnd][-1]
                if src_top[SUIT] == fnd_top[SUIT]:
                    if cards_in_value_order(fnd_top, src_top):
                        move = f"{src}{fnd_suit}"
                        moves.add(move)
    return moves


@cython.boundscheck(False)
cdef waste_to_tableau(state):
    moves = set()
    if len(state.waste) > 0:
        waste_top = state.waste[-1]
        for dest in range(1, 8):
            if len(state[dest]) == 0:
                # empty tableau, can move a king
                if card_is_king(waste_top):
                    move = f"W{dest}"
                    moves.add(move)
            else:
                # non-empty tableau pile, can stack normally
                dest_top = state[dest][-1]
                if can_stack(waste_top, dest_top):
                    move = f"W{dest}"
                    moves.add(move)
    return moves


@cython.boundscheck(False)
cdef waste_to_foundation(state):
    moves = set()
    if len(state.waste) > 0:
        waste_top = state.waste[-1]
        for fnd_i in range(0, 4):
            fnd = FNDS[fnd_i]
            fnd_suit = FND_SUITS[fnd_i]
            if waste_top[SUIT] != fnd_suit:
                continue  # only bother looking at the correct foundation
            if len(state[fnd]) == 0:
                if card_is_ace(waste_top):
                    move = f"W{fnd_suit}"
                    moves.add(move)
            else:
                fnd_top = state[fnd][-1]
                if cards_in_value_order(fnd_top, waste_top):
                    move = f"W{fnd_suit}"
                    moves.add(move)
    return moves

@cython.boundscheck(False)
cdef foundation_to_tableau(state):
    moves = set()
    for fnd_i in range(0, 4):
        fnd = FNDS[fnd_i]
        fnd_suit = FND_SUITS[fnd_i]
        if len(state[fnd]) == 0:
            continue  # can't move any cards from an empty foundation
        fnd_top = state[fnd][-1]
        for tab in range(1, 8):
            if len(state[tab]) == 0:
                continue  # not gonna move a king onto empty tableau
            tab_top = state[tab][-1]
            if can_stack(fnd_top, tab_top):
                move = f"{fnd_suit}{tab}"
                moves.add(move)
    return moves


@cython.boundscheck(False)
def get_legal_moves(state):
    """ returns a set of legal moves given the state """
    moves = set()
    # tab to tab
    moves = moves.union(tableau_to_tableau(state))
    # tab to foundation
    moves = moves.union(tableau_to_foundation(state))
    # waste to tableau
    moves = moves.union(waste_to_tableau(state))
    # waste to foundation
    moves = moves.union(waste_to_foundation(state))
    # foundation to tableau
    moves = moves.union(foundation_to_tableau(state))
    # draw moves
    moves = moves.union(get_draw_moves(state))
    return moves


def copy(state):
    return KlonState(*state)


def replace_stock(state):
    new_waste = ()
    new_stock = tuple(reversed(state[WASTE]))  # reverse the waste pile
    new_state = list(state)
    new_state[STOCK] = new_stock
    new_state[WASTE] = new_waste
    return KlonState(*new_state)


@cython.boundscheck(False)
def count_face_up(pile):
    """ number of faceup cards in a given TABLEAU pile """
    cdef Py_ssize_t lenpile = len(pile)
    cdef int i
    if lenpile <= 1:
        return lenpile
    for i in range(lenpile):
        card_idx = lenpile - 1 - i
        card = pile[card_idx]
        if card_is_face_down(card):  # the i'th card is face-down
            # therefore the (i-1)th card is face-up
            # we want a count so we want (i-1)+1 = i
            return i
    return lenpile  # (== i+1) all cards are face up


cdef int card_is_face_down(char* card):
    # c=99, d=100, s=115, h=104
    cdef char sv = card[1]
    return sv == 99 or sv == 100 or sv == 115 or sv == 104


@cython.boundscheck(False)
def last_face_up(pile):
    if len(pile) == 0:
        return pile
    return pile[:-1] + (pile[-1].upper(),)


@cython.boundscheck(False)
def move(state, src_pile, dest_pile, cards=1):
    new_src = last_face_up(state[src_pile][:-cards])
    new_dest = state[dest_pile] + state[src_pile][-cards:]
    new_state = list(state)
    new_state[src_pile] = new_src
    new_state[dest_pile] = new_dest
    return KlonState(*new_state)


@cython.boundscheck(False)
def draw(state):
    new_waste = state[WASTE]
    new_stock = state[STOCK]
    draw_count = min(3, len(state[STOCK]))
    for _ in range(draw_count):
        new_waste = new_waste + (new_stock[-1],)
        new_stock = new_stock[:-1]
    new_state = list(state)
    new_state[STOCK] = new_stock
    new_state[WASTE] = new_waste
    return KlonState(*new_state)


@cython.boundscheck(False)
def play_move(state, move_code):
    """
    Given a move code, perform that move and return the new state
    Follows ShootMe/Klondike-Solver move codex convention
    """
    """
    DR# is a draw move that is done # number of times.
    ie) DR2 means draw twice, if draw count > 1 it is still DR2.
    """
    cdef int draws_remaining
    if move_code.startswith("DR"):
        st = copy(state)
        draws_remaining = int(move_code[2:])
        while draws_remaining >= 1:
            if len(st.stock) == 0:
                st = replace_stock(st)
            st = draw(st)
            draws_remaining -= 1
        return st

    """
    NEW is to represent the moving of cards from the
    Waste pile back to the stock pile. A New round.
    """
    if move_code == "NEW":
        return replace_stock(state)

    "F# means to flip the card on tableau pile #."
    # I don't implement flipping cards, it happens automatically
    if move_code.startswith("F"):
        return state

    """
    XY means to move the top card from pile X to pile Y.
		X will be 1 through 7, W for Waste, or a foundation suit character.
                'C'lubs, 'D'iamonds, 'S'pades, 'H'earts
		Y will be 1 through 7 or the foundation suit character.
    	XY-# is the same as above except you are moving # number of cards from X to Y.
    """
    if "-" in move_code:
        xy, num = move_code.split("-")
        x, y = xy
        src = pile_lookup(x)
        dest = pile_lookup(y)
        cards = int(num)
    else:
        x, y = move_code
        src = pile_lookup(x)
        dest = pile_lookup(y)
        cards = 1
    return move(state, src, dest, cards=cards)


cdef int pile_lookup(char* pilestr):
    cdef char p = pilestr[0]
    if p == 49: return TABLEAU1      # 1
    if p == 50: return TABLEAU2      # 2
    if p == 51: return TABLEAU3      # 3
    if p == 52: return TABLEAU4      # 4
    if p == 53: return TABLEAU5      # 5
    if p == 54: return TABLEAU6      # 6
    if p == 55: return TABLEAU7      # 7
    if p == 67: return FOUNDATION_C  # C
    if p == 68: return FOUNDATION_D  # D
    if p == 83: return FOUNDATION_S  # S
    if p == 72: return FOUNDATION_H  # H
    if p == 87: return WASTE         # W


def state_is_win(state):
    cards = "A23456789TJQK"
    if len(state.stock) != 0:
        return False
    if len(state.waste) != 0:
        return False
    for fnd_i in range(0, 4):
        fnd = fnd_i + 9
        if len(state[fnd]) != 13:
            return False
    for tab in range(TABLEAU1, TABLEAU7+1):
        if len(state[tab]) != 0:
            return False
    for fnd_i in range(0, 4):
        fnd_pile_idx = fnd_i + 9
        fnd_pile = state[fnd_pile_idx]
        fnd_suit = "CDSH"[fnd_i]
        # for card, expected_value in zip(fnd_pile, cards):
        for i in range(13):
            card = fnd_pile[i]
            expected_value = cards[i]
            if card[SUIT] != fnd_suit:
                return False
            if card[VALUE] != expected_value:
                return False
    return True


def to_pretty_string(state):
    s = ""
    s += "Stock: " + " ".join(state.stock)
    s += "\nWaste: " + " ".join(state.waste)
    for fsuit, fnd_idx in zip(FND_SUITS, FNDS):
        s += f"\nFnd {fsuit}: " + " ".join(state[fnd_idx])
    for tab in range(TABLEAU1, TABLEAU7+1):
        s += f"\nTab {tab}: " + " ".join(state[tab])
    return s


### LEGAL MOVES VECTORIZING

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


def card_to_int(card):
    val, suit = card
    s = suits[suit]
    v = values[val.upper()]
    cardint = (s << 4) + v
    return cardint


def int_to_card(cardint):
    if cardint == 0:
        return None
    sv = cardint >> 4
    cv = cardint & 0b1111
    card = intvalues[cv] + intsuits[sv]
    if sv >= 5:  # facedown
        return card.lower()
    return card


def cardint(state_tuple, pad):
    a = np.fromiter(map(card_to_int, state_tuple), dtype=np.uint8)
    # do left padding
    z = np.zeros(pad)
    z[: a.shape[0]] = a
    return z


def state_to_vec(state):
    state_arr = np.array([])
    for pile_idx in range(STOCK, FOUNDATION_H + 1):
        a = cardint(state[pile_idx], PAD[pile_idx])
        state_arr = np.concatenate((state_arr, a))
    return state_arr


def vec_to_state(sv):
    start = 0
    new_state = []
    for pile_idx in range(STOCK, FOUNDATION_H + 1):
        end = start + PAD[pile_idx]
        x = sv[start:end]
        a = list(map(int, x.tolist()))
        y = tuple(filter(bool, map(int_to_card, a)))
        new_state.append(y)
        start = end
    return KlonState(*new_state)


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

np_all_moves = np.array(generate_all_possible_moves())


def vector_legal_moves(state):
    moves = list(get_legal_moves(state))
    return np.isin(np_all_moves, moves).astype(np.uint8)
