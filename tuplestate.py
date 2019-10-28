from collections import namedtuple
from pprint import pprint
from timebudget import timebudget


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
FND_SUITS = "CDSH"

VALUE = 0  # the 0th index of a card string
SUIT = 1  # the 1st index of a card string
FNDS = [FOUNDATION_C, FOUNDATION_D, FOUNDATION_S, FOUNDATION_H]
TABLEAUS = [TABLEAU1, TABLEAU2, TABLEAU3, TABLEAU4, TABLEAU5, TABLEAU6, TABLEAU7]
VALUE_ORDER = set(
    [
        ("A", "2"),
        ("2", "3"),
        ("3", "4"),
        ("4", "5"),
        ("5", "6"),
        ("6", "7"),
        ("7", "8"),
        ("8", "9"),
        ("9", "T"),
        ("T", "J"),
        ("J", "Q"),
        ("Q", "K"),
    ]
)


def irange(start, stop):
    """ inclusive range """
    if start <= stop:
        return range(start, stop + 1)
    elif start > stop:
        return range(start, stop - 1, -1)


def init_from_ui_state(game_dict):
    def card(c):
        """ fixes up card definitions for UI format compat """
        if c.startswith("10"):
            t = "t" if c[-1] in "cdsh" else "T"
            return c.replace("10", t)
        return c

    def mapcards(it):
        return tuple(map(card, it))

    foundation = tuple(mapcards(f) for f in game_dict["foundation"])
    stock = tuple(card(c).upper() for c in game_dict["stock"])
    waste = tuple(mapcards(game_dict["waste"]))
    tableau = [mapcards(t) for t in game_dict["tableau"]]
    return KlonState(
        stock=stock,
        waste=waste,
        tableau1=tableau[0],
        tableau2=tableau[1],
        tableau3=tableau[2],
        tableau4=tableau[3],
        tableau5=tableau[4],
        tableau6=tableau[5],
        tableau7=tableau[6],
        foundation1=foundation[0],
        foundation2=foundation[1],
        foundation3=foundation[2],
        foundation4=foundation[3],
    )


def init_from_solvitaire(game_dict):
    def card(c):
        """ fixes up card definitions for Solvitaire format compat """
        if c.startswith("10"):
            t = "t" if c[-1] in "cdsh" else "T"
            return c.replace("10", t)
        return c

    stock = tuple(map(card, game_dict["stock"]))
    tableau = tuple(tuple(map(card, t)) for t in game_dict["tableau piles"])
    waste = tuple(game_dict.get("waste", ()))
    foundation = tuple(game_dict.get("foundations", [tuple()] * 4))
    return KlonState(
        stock=stock,
        waste=waste,
        tableau1=tableau[0],
        tableau2=tableau[1],
        tableau3=tableau[2],
        tableau4=tableau[3],
        tableau5=tableau[4],
        tableau6=tableau[5],
        tableau7=tableau[6],
        foundation1=foundation[0],
        foundation2=foundation[1],
        foundation3=foundation[2],
        foundation4=foundation[3],
    )


@timebudget
def last_face_up(pile):
    if len(pile) == 0:
        return pile
    return pile[:-1] + (pile[-1].upper(),)


@timebudget
def move(state, src_pile, dest_pile, cards=1):
    new_src = last_face_up(state[src_pile][:-cards])
    new_dest = state[dest_pile] + state[src_pile][-cards:]
    new_state = list(state)
    new_state[src_pile] = new_src
    new_state[dest_pile] = new_dest
    return KlonState(*new_state)


@timebudget
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


def copy(state):
    return KlonState(*state)


@timebudget
def replace_stock(state):
    new_waste = ()
    new_stock = tuple(reversed(state[WASTE]))  # reverse the waste pile
    new_state = list(state)
    new_state[STOCK] = new_stock
    new_state[WASTE] = new_waste
    return KlonState(*new_state)


def count_face_up(pile):
    """ number of faceup cards in a given TABLEAU pile """
    if len(pile) == 0:
        return 0
    if len(pile) == 1:
        return 1
    for i, card in enumerate(reversed(pile)):
        if card[1] in "cdsh":  # the i'th card is face-down
            # therefore the (i-1)th card is face-up
            # we want a count so we want (i-1)+1 = i
            return i
    return len(pile)  # (== i+1) all cards are face up


@timebudget
def can_stack(card, onto):
    """ `card` is the card to move, `onto` is the card to stack onto """
    RED = "DH"
    BLACK = "CS"
    if card[SUIT] in RED and onto[SUIT] in RED:
        return False
    if card[SUIT] in BLACK and onto[SUIT] in BLACK:
        return False
    return (card[VALUE], onto[VALUE]) in VALUE_ORDER


def to_dict(state):
    TABLEAU = [TABLEAU1, TABLEAU2, TABLEAU3, TABLEAU4, TABLEAU5, TABLEAU6, TABLEAU7]
    FND = [FOUNDATION_C, FOUNDATION_D, FOUNDATION_S, FOUNDATION_H]
    return {
        "stock": state.stock,
        "waste": state.waste,
        "tableau": list(map(lambda t: state[t], TABLEAU)),
        "foundations": list(map(lambda f: state[f], FND)),
    }


def pprint_st(state):
    pprint(to_dict(state))


def init_from_dict(game):
    tableau = game["tableau"]
    foundation = game["foundations"]
    return KlonState(
        stock=game["stock"],
        waste=game["waste"],
        tableau1=tableau[0],
        tableau2=tableau[1],
        tableau3=tableau[2],
        tableau4=tableau[3],
        tableau5=tableau[4],
        tableau6=tableau[5],
        tableau7=tableau[6],
        foundation1=foundation[0],
        foundation2=foundation[1],
        foundation3=foundation[2],
        foundation4=foundation[3],
    )


@timebudget
def state_is_win(state):
    cards = "A23456789TJQK"
    if len(state.stock) != 0:
        return False
    if len(state.waste) != 0:
        return False
    for fnd in FNDS:
        if len(state[fnd]) != 13:
            return False
    for tab in irange(TABLEAU1, TABLEAU7):
        if len(state[tab]) != 0:
            return False
    for fnd, fnd_suit in zip(FNDS, FND_SUITS):
        fnd_pile = state[fnd]
        for card, expected_value in zip(fnd_pile, cards):
            if card[SUIT] != fnd_suit:
                return False
            if card[VALUE] != expected_value:
                return False
    return True


def play_move(state, move_code):
    """
    Given a move code, perform that move and return the new state
    Follows ShootMe/Klondike-Solver move codex convention
    """
    """
    DR# is a draw move that is done # number of times.
    ie) DR2 means draw twice, if draw count > 1 it is still DR2.
    """
    if move_code.startswith("DR"):
        st = copy(state)
        draws = int(move_code[2:])
        for draws_remaining in irange(draws, 1):
            if len(st.stock) == 0 and draws_remaining > 0:
                st = replace_stock(st)
            st = draw(st)
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
    TABLEAU = {
        "1": TABLEAU1,
        "2": TABLEAU2,
        "3": TABLEAU3,
        "4": TABLEAU4,
        "5": TABLEAU5,
        "6": TABLEAU6,
        "7": TABLEAU7,
    }
    FOUNDATION = {
        "C": FOUNDATION_C,
        "D": FOUNDATION_D,
        "S": FOUNDATION_S,
        "H": FOUNDATION_H,
    }
    SRC_MOVES = {**TABLEAU, **FOUNDATION, "W": WASTE}
    DEST_MOVES = {**TABLEAU, **FOUNDATION}
    if "-" in move_code:
        xy, num = move_code.split("-")
        x, y = xy
        src = TABLEAU[x]
        dest = TABLEAU[y]
        cards = int(num)
    else:
        x, y = move_code
        src = SRC_MOVES[x]
        dest = DEST_MOVES[y]
        cards = 1
    return move(state, src, dest, cards=cards)
