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
    return range(start, stop + 1)


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
    5C F5 5C F5 DR3 W5 45 F4 41 F4 DR1 W4 74 F7 DR3 W7 WC DR1 NEW DR2 W1
    W6 WS DR3 W4 WC 74-2 F7 61-2 F6 67 F6 61 F6 6S F6 1S W4 64 F6 6S W6 WD
    15-5 W1 W6 36 F3 W7 WH WD DR1 W1 31 F3 3S 4S WS 71-3 F7 W1 43-7 F4 4H
    W6 WH 5H 5C 2C F2 2D 7D F7 7D F7 7D F7 7H 5H 1H 3D 5C 1S 3C 5H 5S 3H
    5H DR1 W2 WC 3C 5C F5 5D F5 1D 1S 6D 1D 3H 6S 1C 3S 5H 6D 1H 2C 3D 6S
    """

    "DR# is a draw move that is done # number of times. "
    "ie) DR2 means draw twice, if draw count > 1 it is still DR2."
    if move_code.startswith("DR"):
        s = draw(state)  # draw once, local state variable
        remaining_draws = int(move_code[-1]) - 1  # subtract one draw
        for _ in range(remaining_draws):
            s = draw(s)
        return s

    "NEW is to represent the moving of cards from the"
    "Waste pile back to the stock pile. A New round."
    if move_code == "NEW":
        return replace_stock(state)

    "F# means to flip the card on tableau pile #."
    # I don't implement flipping cards, it happens automatically
    if move_code.startswith("F"):
        return state

    """XY means to move the top card from pile X to pile Y.
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


import unittest
import json


class TestState(unittest.TestCase):
    def test_init_from_solvitaire(self):
        with open("./fixtures/sm-seed12.json") as f:
            game1 = json.load(f)
        state1 = init_from_solvitaire(game1)
        self.assertEqual(state1.waste, ())
        self.assertEqual(state1.tableau1, ("8H",))

        with open("./fixtures/game1.json") as f:
            game = json.load(f)
        state = init_from_solvitaire(game)

        initial_stock = (
            "TH,8D,7H,KC,3D,TD,5H,8C,QS,JS,9H,7C,6D,8S,QD,QH,AC,9C,5S,KH,QC,2S,TC,9D"
        )
        self.assertEqual(state.stock, tuple(initial_stock.split(",")))
        self.assertEqual(state.waste, ())

        expected = (
            ("4D",),
            ("3c", "4C"),
            ("9s", "7d", "6H"),
            ("ah", "7s", "2c", "JD"),
            ("ad", "6s", "2h", "ts", "AS"),
            ("4h", "8h", "2d", "ks", "jc", "5C"),
            ("3h", "4s", "3s", "5d", "jh", "6c", "KD"),
        )
        actual = (
            state.tableau1,
            state.tableau2,
            state.tableau3,
            state.tableau4,
            state.tableau5,
            state.tableau6,
            state.tableau7,
        )

        for actual_pile, expected_pile in zip(actual, expected):
            self.assertEqual(actual_pile, expected_pile)

        self.assertEqual(state.foundation1, ())
        self.assertEqual(state.foundation2, ())
        self.assertEqual(state.foundation3, ())
        self.assertEqual(state.foundation4, ())

    def setUp(self):
        initial_stock = (
            "KC,9C,QC,8C,3C,7S,7H,TC,4C,7D,KS,AD,QS,KH,QD,TH,8S,AH,6H,4H,AS,2D,TD,3H"
        )
        self.state = KlonState(
            stock=tuple(initial_stock.split(",")),
            waste=(),
            tableau1=("8H",),
            tableau2=("3d", "6C"),
            tableau3=("5s", "jd", "JS"),
            tableau4=("2h", "kd", "7c", "9S"),
            tableau5=("qh", "8d", "jc", "2c", "AC"),
            tableau6=("4s", "6s", "2s", "3s", "9d", "5C"),
            tableau7=("5h", "6d", "5d", "4d", "ts", "9h", "JH"),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )

    def test_move_tableau_to_foundation(self):
        self.assertEqual(self.state[TABLEAU5], ("qh", "8d", "jc", "2c", "AC"))
        self.assertEqual(self.state[FOUNDATION_C], ())
        state2 = move(self.state, TABLEAU5, FOUNDATION_C)
        # nothing changed in self.state
        self.assertEqual(self.state[TABLEAU5], ("qh", "8d", "jc", "2c", "AC"))
        self.assertEqual(self.state[FOUNDATION_C], ())
        self.assertEqual(state2[TABLEAU5], ("qh", "8d", "jc", "2C"))
        self.assertEqual(state2[FOUNDATION_C], ("AC",))

    def test_move_last_card_in_tableau_to_tableau(self):
        self.assertEqual(self.state[TABLEAU1], ("8H",))
        self.assertEqual(self.state[TABLEAU4], ("2h", "kd", "7c", "9S"))
        state2 = move(self.state, TABLEAU1, TABLEAU4)
        # nothing changed in self.state
        self.assertEqual(self.state[TABLEAU1], ("8H",))
        self.assertEqual(self.state[TABLEAU4], ("2h", "kd", "7c", "9S"))
        self.assertEqual(state2[TABLEAU1], ())
        self.assertEqual(state2[TABLEAU4], ("2h", "kd", "7c", "9S", "8H"))

    def test_draw_cards(self):
        self.assertEqual(self.state[WASTE], ())
        st1 = "KC,9C,QC,8C,3C,7S,7H,TC,4C,7D,KS,AD,QS,KH,QD,TH,8S,AH,6H,4H,AS,2D,TD,3H"
        self.assertEqual(",".join(self.state[STOCK]), st1)

        state2 = draw(self.state)

        self.assertEqual(state2[WASTE], ("3H", "TD", "2D"))
        st2 = "KC,9C,QC,8C,3C,7S,7H,TC,4C,7D,KS,AD,QS,KH,QD,TH,8S,AH,6H,4H,AS"
        self.assertEqual(",".join(state2[STOCK]), st2)

    def test_deplete_stock(self):
        self.assertEqual(self.state[WASTE], ())
        st1 = "KC,9C,QC,8C,3C,7S,7H,TC,4C,7D,KS,AD,QS,KH,QD,TH,8S,AH,6H,4H,AS,2D,TD,3H"
        self.assertEqual(",".join(self.state[STOCK]), st1)

        state2 = draw(self.state)
        state2 = draw(state2)
        state2 = draw(state2)
        state2 = draw(state2)
        state2 = draw(state2)
        state2 = draw(state2)
        state2 = draw(state2)
        state2 = draw(state2)

        w2 = "3H,TD,2D,AS,4H,6H,AH,8S,TH,QD,KH,QS,AD,KS,7D,4C,TC,7H,7S,3C,8C,QC,9C,KC"
        self.assertEqual(",".join(state2[WASTE]), w2)
        self.assertEqual(state2[STOCK], ())

    def test_replace_stock(self):
        state = draw(self.state)
        while len(state[STOCK]) > 0:
            state = draw(state)
        w2 = "3H,TD,2D,AS,4H,6H,AH,8S,TH,QD,KH,QS,AD,KS,7D,4C,TC,7H,7S,3C,8C,QC,9C,KC"
        self.assertEqual(",".join(state[WASTE]), w2)
        self.assertEqual(state[STOCK], ())

        state2 = replace_stock(state)
        s2 = "KC,9C,QC,8C,3C,7S,7H,TC,4C,7D,KS,AD,QS,KH,QD,TH,8S,AH,6H,4H,AS,2D,TD,3H"
        self.assertEqual(",".join(state2[STOCK]), s2)
        self.assertEqual(state2[WASTE], ())

        state3 = draw(state2)
        self.assertEqual(state3[WASTE], ("3H", "TD", "2D"))
        s3 = "KC,9C,QC,8C,3C,7S,7H,TC,4C,7D,KS,AD,QS,KH,QD,TH,8S,AH,6H,4H,AS"
        self.assertEqual(",".join(state3[STOCK]), s3)

    def test_move_waste_to_tableau(self):
        state = draw(self.state)
        state = draw(state)
        state = draw(state)
        self.assertEqual(state[WASTE][-1], "TH")
        state2 = move(state, WASTE, TABLEAU3)
        self.assertEqual(state2[WASTE][-1], "8S")
        self.assertEqual(state2[TABLEAU3], ("5s", "jd", "JS", "TH"))

    def test_bunch_of_moves_and_move_two_cards(self):
        state = draw(self.state)
        state = draw(state)
        state = draw(state)
        state = move(state, WASTE, TABLEAU3)
        self.assertEqual(state[WASTE][-1], "8S")
        self.assertEqual(state[TABLEAU3], ("5s", "jd", "JS", "TH"))
        state2 = move(state, TABLEAU4, TABLEAU3)
        self.assertEqual(state2[TABLEAU3], ("5s", "jd", "JS", "TH", "9S"))
        self.assertEqual(state2[TABLEAU4], ("2h", "kd", "7C"))
        state3 = move(state2, TABLEAU4, TABLEAU1)
        self.assertEqual(state3[TABLEAU4], ("2h", "KD"))
        self.assertEqual(state3[TABLEAU1], ("8H", "7C"))
        state4 = move(state3, TABLEAU1, TABLEAU3, cards=2)
        self.assertEqual(state4[TABLEAU1], ())
        self.assertEqual(state4[TABLEAU3], ("5s", "jd", "JS", "TH", "9S", "8H", "7C"))

    def test_draw_with_two_in_stock(self):
        state = draw(self.state)
        state = draw(state)
        state = draw(state)
        # make a legal move which moves card from waste to tableau
        state = move(state, WASTE, TABLEAU3)
        # deplete the stock
        while len(state[STOCK]) > 0:
            state = draw(state)
        # replace stock: length of stock mod 3 = 2
        state = replace_stock(state)
        while len(state[STOCK]) >= 3:
            state = draw(state)
        self.assertEqual(state[STOCK], ("KC", "9C"))
        # draw with only two cards left in the stock
        state2 = draw(state)
        # after draw, two cards should be empty
        self.assertEqual(state2[STOCK], ())
        self.assertEqual(state2[WASTE][-2:], ("9C", "KC"))

    def test_entire_game(self):
        verbose = False
        W = 160
        state = self.state
        soln = (
            "5C F5 5C F5 DR3 W5 45 F4 41 F4 DR1 W4 74 F7 DR3 W7 WC DR1 NEW DR2 W1 "
            "W6 WS DR3 W4 WC 74-2 F7 61-2 F6 67 F6 61 F6 6S F6 1S W4 64 F6 6S W6 WD "
            "15-5 W1 W6 36 F3 W7 WH WD DR1 W1 31 F3 3S 4S WS 71-3 F7 W1 43-7 F4 4H "
            "W6 WH 5H 5C 2C F2 2D 7D F7 7D F7 7D F7 7H 5H 1H 3D 5C 1S 3C 5H 5S 3H "
            "5H DR1 W2 WC 3C 5C F5 5D F5 1D 1S 6D 1D 3H 6S 1C 3S 5H 6D 1H 2C 3D 6S"
        ).split(" ")

        if verbose:
            pprint(to_dict(state), width=W)
            print()

        while len(soln) > 0:
            move_code = soln.pop(0)
            state = play_move(state, move_code)
            if verbose and not move_code.startswith("F"):
                print("move code", move_code)
                pprint(to_dict(state), width=W)
                print()

        foundation_suits = "CDSH"
        foundations = [FOUNDATION_C, FOUNDATION_D, FOUNDATION_S, FOUNDATION_H]
        for foundation in foundations:
            self.assertEqual(len(state[foundation]), 13)

        cards = "A23456789TJQK"
        for suit, fnd in zip(foundation_suits, foundations):
            for card_value, actual_card in zip(cards, state[fnd]):
                expected_card = card_value + suit
                self.assertEqual(actual_card, expected_card)

        tableau = irange(TABLEAU1, TABLEAU7)
        for tab in tableau:
            self.assertEqual(state[tab], ())

        self.assertEqual(state.stock, ())
        self.assertEqual(state.waste, ())

    def test_get_legal_moves_1(self):
        # pprint(to_dict(self.state))
        actual = get_legal_moves(self.state)
        expected = set(["5C", "14"])  # move AC to foundation, move 8H onto 9S
        # can draw 1-8 until you start looping
        for i in irange(1, 8):
            expected.add(f"DR{i}")
        self.assertEqual(expected, actual)

    def test_get_legal_moves_2(self):
        state = move(self.state, TABLEAU1, TABLEAU4)
        # pprint_st(state)
        actual = get_legal_moves(state)
        expected = set(["5C"])  # move AC to foundation
        # can draw 1-8 until you start looping
        for i in irange(1, 8):
            expected.add(f"DR{i}")
        self.assertEqual(expected, actual)

    def test_kplus_state_1(self):
        state = copy(self.state)
        for _ in range(3):
            state = draw(state)
        self.assertEqual(state.waste[-1], "TH")
        state = move(state, WASTE, TABLEAU3)
        self.assertEqual(state.tableau3[-1], "TH")
        # count moves for this state
        actual = get_legal_moves(state)
        expected = set()
        expected.add("5C")  # move AC to foundation
        expected.add("43")  # move 9S onto TH
        expected.add("14")  # move 8H onto 9S
        # I counted 12 moves until it started looping
        for i in irange(1, 12):
            expected.add(f"DR{i}")
        self.assertEqual(expected, actual)

    def test_waste_king_to_empty_tableau(self):
        state = copy(self.state)
        for _ in range(8):
            state = draw(state)
        self.assertEqual(state.waste[-1], "KC")
        state = move(state, TABLEAU1, TABLEAU4)  # move 8H onto 9S
        actual = get_legal_moves(state)
        expected = set()
        expected.add("5C")  # move AC onto foundation
        expected.add("W1")  # move KC onto tableau 1
        for i in irange(1, 7):  # 7 moves until starts looping (Q9K)
            expected.add(f"DR{i}")
        self.assertEqual(expected, actual)

    def test_waste_to_tableau_pile(self):
        state = copy(self.state)
        for _ in range(3):
            state = draw(state)
        actual = get_legal_moves(state)
        expected = set()
        expected.add("5C")  # move AC to foundation
        expected.add("14")  # move 8H onto 9S
        expected.add("W3")  # move waste TH onto JS
        for i in irange(1, 7):
            expected.add(f"DR{i}")
        self.assertEqual(expected, actual)

    def test_foundation_to_tableau(self):
        game = {
            "foundation": [["AC", "2C", "3C"], [], ["AS", "2S", "3S"], []],
            "waste": "3H,10D,2D,AH,8S,QD,KH,AD,KS,7D,4C,7H,7S".split(","),
            "stock": ["kc", "9c", "qc"],
            "tableau": [
                ["KD", "QS", "JH", "10C", "9H", "8C"],
                ["3d", "6C"],
                ["5s", "jd", "JS", "10H", "9S", "8H", "7C", "6H", "5C", "4H"],
                ["2H"],
                ["qh", "8d", "JC"],
                ["4s", "6S"],
                ["5h", "6d", "5d", "4d", "10S", "9D"],
            ],
        }
        state = init_from_ui_state(game)
        actual = get_legal_moves(state)
        expected = set()
        expected.add("C3")  # move 3C from foundation onto 4H
        expected.add("S3")  # move 3S from foundation onto 4H
        expected.add("17")  # move 8C to 9D (useless move)
        expected.add("35-7")  # move 10H+7 onto JC (useless move)
        for i in irange(1, 6):
            expected.add(f"DR{i}")
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
