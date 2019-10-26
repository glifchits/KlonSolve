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


def can_stack_tableau(src, dest):
    RED = "DH"
    BLACK = "CS"
    if src[SUIT] in RED and dest[SUIT] in RED:
        return False
    if src[SUIT] in BLACK and dest[SUIT] in BLACK:
        return False
    return (src[VALUE], dest[VALUE]) in VALUE_ORDER


def get_legal_moves(state):
    """ returns a set of legal moves given the state """
    moves = set()
    TABLEAUS = range(TABLEAU1, TABLEAU7 + 1)
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
            for i, src_card in enumerate(FACEUP[src]):
                move = f"{src}{dest}"
                if i > 0:
                    move += f"-{i+1}"

                if len(state[dest]) == 0:  # tableau empty
                    if src_card[VALUE] == "K":
                        moves.add(move)
                elif can_stack_tableau(src_card, state[dest][-1]):
                    moves.add(move)
    # tab to foundation
    for src in TABLEAUS:
        if len(state[src]) == 0:
            continue  # can't move empty to foundation
        src_top = state[src][-1]
        for fnd, fnd_suit in zip(FNDS, "CDSH"):
            move = f"{src}{fnd_suit}"
            if len(state[fnd]) == 0:
                if src_top[VALUE] == "A" and src_top[SUIT] == fnd_suit:
                    moves.add(move)
            else:
                fnd_top = fnd_pile[-1]
                if src_top[SUIT] == fnd_top[SUIT]:
                    ord = (src_top[VALUE], dest_top[VALUE])
                    if ord in VALUE_ORDER:
                        moves.add(move)
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

        tableau = [TABLEAU1, TABLEAU2, TABLEAU3, TABLEAU4, TABLEAU5, TABLEAU6, TABLEAU7]
        for tab in tableau:
            self.assertEqual(state[tab], ())

        self.assertEqual(state.stock, ())
        self.assertEqual(state.waste, ())

    def test_get_legal_moves_1(self):
        # pprint(to_dict(self.state))
        actual = get_legal_moves(self.state)
        expected = set(["5C", "14"])  # move AC to foundation, move 8H onto 9S
        self.assertEqual(expected, actual)

    def test_get_legal_moves_2(self):
        state = move(self.state, TABLEAU1, TABLEAU4)
        # pprint_st(state)
        actual = get_legal_moves(state)
        expected = set(["5C"])  # move AC to foundation
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
