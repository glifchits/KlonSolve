from collections import namedtuple
from pprint import pprint


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


def last_face_up(pile):
    if len(pile) == 0:
        return pile
    return pile[:-1] + (pile[-1].upper(),)


def move(state, src_pile, dest_pile, cards=1):
    new_src = last_face_up(state[src_pile][:-cards])
    new_dest = state[dest_pile] + state[src_pile][-cards:]
    new_state = list(state)
    new_state[src_pile] = new_src
    new_state[dest_pile] = new_dest
    return KlonState(*new_state)


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


def can_stack(card, onto):
    """ `card` is the card to move, `onto` is the card to stack onto """
    RED = "DH"
    BLACK = "CS"
    if card[SUIT] in RED and onto[SUIT] in RED:
        return False
    if card[SUIT] in BLACK and onto[SUIT] in BLACK:
        return False
    return (card[VALUE], onto[VALUE]) in VALUE_ORDER


def get_draw_moves(state):
    st = copy(state)
    draw_moves = set()
    top_cards = set()
    if len(st.waste) > 0:
        top_cards.add(st.waste[-3:])  # current waste is available
    for draw_count in range(200):  # should be way more than enough
        if len(st.stock) == 0:
            st = replace_stock(st)
        st = draw(st)
        new_move = f"DR{draw_count+1}"
        top_waste = st[WASTE][-3:]
        if top_waste in top_cards:
            return draw_moves
        top_cards.add(top_waste)
        draw_moves.add(new_move)
    return draw_moves


def get_legal_moves(state):
    """ returns a set of legal moves given the state """
    moves = set()
    TABLEAUS = irange(TABLEAU1, TABLEAU7)
    FACEUP = {}
    for tab in TABLEAUS:
        pile = state[tab]
        fu = count_face_up(pile)
        FACEUP[tab] = pile[-fu:]
    # tab to tab
    for src in TABLEAUS:
        for dest in TABLEAUS:
            if src == dest:
                continue
            for i, src_card in enumerate(reversed(FACEUP[src])):
                move = f"{src}{dest}"
                if i > 0:
                    move += f"-{i+1}"

                if len(state[dest]) == 0:  # tableau empty
                    if src_card[VALUE] == "K":
                        moves.add(move)
                elif can_stack(src_card, state[dest][-1]):
                    moves.add(move)
    # tab to foundation
    for src in TABLEAUS:
        if len(state[src]) == 0:
            continue  # can't move empty to foundation
        src_top = state[src][-1]
        for fnd, fnd_suit in zip(FNDS, FND_SUITS):
            move = f"{src}{fnd_suit}"
            if len(state[fnd]) == 0:
                if src_top[VALUE] == "A" and src_top[SUIT] == fnd_suit:
                    moves.add(move)
            else:
                fnd_top = state[fnd][-1]
                if src_top[SUIT] == fnd_top[SUIT]:
                    ord = (src_top[VALUE], fnd_top[VALUE])
                    if ord in VALUE_ORDER:
                        moves.add(move)
    # waste to tableau
    if len(state.waste) > 0:
        waste_top = state.waste[-1]
        for dest in TABLEAUS:
            move = f"W{dest}"
            if len(state[dest]) == 0:
                # empty tableau, can move a king
                if waste_top[VALUE] == "K":
                    moves.add(move)
            else:
                # non-empty tableau pile, can stack normally
                dest_top = state[dest][-1]
                if can_stack(waste_top, dest_top):
                    moves.add(move)
    # waste to foundation
    if len(state.waste) > 0:
        waste_top = state.waste[-1]
        for fnd, fnd_suit in zip(FNDS, FND_SUITS):
            if waste_top[SUIT] != fnd_suit:
                continue  # only bother looking at the correct foundation
            move = f"W{fnd_suit}"
            if len(state[fnd]) == 0:
                if waste_top[VALUE] == "A":
                    moves.add(move)
            else:
                fnd_top = state[fnd][-1]
                order = (fnd_top[VALUE], waste_top[VALUE])
                if order in VALUE_ORDER:
                    moves.add(move)
    # foundation to tableau
    for fnd, fnd_suit in zip(FNDS, FND_SUITS):
        if len(state[fnd]) == 0:
            continue  # can't move any cards from an empty foundation
        fnd_top = state[fnd][-1]
        for tab in TABLEAUS:
            if len(state[tab]) == 0:
                continue  # not gonna move a king onto empty tableau
            tab_top = state[tab][-1]
            if can_stack(fnd_top, tab_top):
                move = f"{fnd_suit}{tab}"
                moves.add(move)
    # draw moves
    moves = moves.union(get_draw_moves(state))
    return moves


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
