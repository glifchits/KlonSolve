from gamestate import *
from vectorize import *
from tuplestate import (
    init_from_solvitaire,
    init_from_ui_state,
    init_from_dict,
    to_ui_state,
)
import numpy as np
import unittest
import json


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

    def test_waste_to_foundation(self):
        game = {
            "foundation": [["AC", "2C"], [], [], []],
            # fmt: off
            "waste": [
                "3H", "10D", "2D", "AS", "4H", "6H", "AH",
                "8S", "QD", "KH", "AD", "KS", "7D", "4C",
                "10C", "7H", "7S", "3C",
            ],
            # fmt: on
            "stock": ["kc", "9c", "qc"],
            "tableau": [
                ["KD", "QS", "JH"],
                ["3d", "6C"],
                ["5s", "jd", "JS", "10H", "9S", "8H", "7C"],
                ["2H"],
                ["qh", "8d", "JC"],
                ["4s", "6s", "2s", "3s", "9d", "5C"],
                ["5h", "6d", "5d", "4d", "10s", "9H", "8C"],
            ],
        }
        state = init_from_ui_state(game)
        actual = get_legal_moves(state)
        expected = set()
        expected.add("WC")  # move 3C from waste to foundation (2C)
        expected.add("35-4")  # move TH+4 onto JC (useless move)
        for i in irange(1, 6):
            expected.add(f"DR{i}")
        self.assertEqual(actual, expected)

    def test_waste_ace_to_foundation(self):
        state = copy(self.state)
        for _ in range(3):
            state = draw(state)
        self.assertEqual(state.waste[-1], "TH")
        state = move(state, WASTE, TABLEAU3)
        for _ in range(5):
            state = draw(state)
        self.assertEqual(state.stock, ())
        self.assertEqual(state.waste[-1], "KC")
        state = replace_stock(state)
        for _ in range(4):
            state = draw(state)
        self.assertEqual(state.waste[-1], "AD")
        # get moves for this state
        actual = get_legal_moves(state)
        expected = set()
        expected.add("WD")  # move AD from waste to foundation
        expected.add("5C")  # move AC from tableau to foundation
        expected.add("14")  # move 8H onto 9S
        expected.add("43")  # move 9S onto TH
        for i in irange(1, 7):
            expected.add(f"DR{i}")
        self.assertEqual(expected, actual)

    def test_endgame_1(self):
        game = {
            "foundation": [
                ["AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C"],
                ["AD", "2D", "3D", "4D", "5D", "6D", "7D"],
                ["AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S"],
                ["AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH"],
            ],
            "waste": [],
            "stock": [],
            "tableau": [
                ["KD", "QS"],
                ["KC"],
                [],
                ["KH", "QC", "JD", "10S", "9D"],
                ["qh", "8d", "JC", "10D"],
                ["KS", "QD", "JS"],
                [],
            ],
        }
        state = init_from_ui_state(game)
        actual = get_legal_moves(state)
        expected = set()
        expected.add("56")  # move TD onto JS
        expected.add("62-2")  # move red Q onto K
        expected.add("H1")  # bring JH off foundation onto QS
        expected.add("41-3")  # move red J+2 onto QS
        expected.add("S5")  # move 9S off foundation to TD
        self.assertEqual(expected, actual)

    def test_endgame_2(self):
        game = {
            "foundation": [
                ["AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC"],
                ["AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD"],
                ["AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS"],
                ["AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH"],
            ],
            "waste": [],
            "stock": [],
            "tableau": [
                ["KD", "QS"],
                ["KH", "QC"],
                [],
                ["KC"],
                ["QH"],
                ["KS", "QD"],
                [],
            ],
        }
        state = init_from_ui_state(game)
        # a sequence of moves I wrote, easy win. must be possible to make these moves
        move_seq = ("5H", "6D", "2C", "1S", "1D", "2H", "4C", "6S")
        for move_code in move_seq:
            moves = get_legal_moves(state)
            self.assertIn(move_code, moves)
            state = play_move(state, move_code)
        self.assertTrue(state_is_win(state))

    def test_irange_forward(self):
        expected = [4, 5, 6, 7, 8, 9]
        actual = list(irange(4, 9))
        self.assertEqual(expected, actual)

    def test_irange_backward(self):
        actual = list(irange(10, 5))
        expected = [10, 9, 8, 7, 6, 5]
        self.assertEqual(expected, actual)

    def test_play_move_draws_more_than_stock(self):
        state = copy(self.state)
        # self.assertTrue(False)
        dr8 = play_move(state, "DR8")
        self.assertEqual(dr8.waste[-1], "KC")
        dr9 = draw(dr8)
        self.assertEqual(dr9.stock, ())
        self.assertEqual(dr9.waste[-1], "KC")
        self.assertEqual(play_move(state, "DR9").waste[-1], "2D")
        self.assertEqual(play_move(state, "DR14").waste[-1], "7H")

    def test_state_equality(self):
        state1 = copy(self.state)
        moves = get_legal_moves(state1)
        draws = [m for m in moves if m.startswith("DR")]
        highest_draw = max(draws, key=lambda dr: int(dr[2:]))
        state2 = play_move(state1, highest_draw)
        state3 = replace_stock(draw(state2))
        self.assertEqual(state1, state3)
        self.assertEqual(draw(state1), draw(state3))
        self.assertNotEqual(state1, draw(state1))
        self.assertNotEqual(state1, draw(state3))

    def test_state_hashing(self):
        state1 = copy(self.state)
        moves = get_legal_moves(state1)
        draws = [m for m in moves if m.startswith("DR")]
        highest_draw = max(draws, key=lambda dr: int(dr[2:]))
        state2 = play_move(state1, highest_draw)
        state3 = replace_stock(draw(state2))
        self.assertEqual(hash(state1), hash(state3))
        self.assertEqual(hash(draw(state1)), hash(draw(state3)))
        self.assertNotEqual(hash(state1), hash(draw(state1)))
        self.assertNotEqual(hash(state1), hash(draw(state3)))

    def test_state_is_win(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","2S","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH","KH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": (),
        }
        state = init_from_dict(d)
        self.assertTrue(state_is_win(state))

    def test_state_is_not_win_1(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","2S","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": ("KH",),
        }
        state = init_from_dict(d)
        self.assertFalse(state_is_win(state))

    def test_state_is_not_win_2(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","2S","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","KH","QH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": (),
        }
        state = init_from_dict(d)
        self.assertFalse(state_is_win(state))

    def test_state_dead_end_bjarnason2007_fig8a(self):
        # Figure 8a from Bjarnason et al (2007)
        d = {
            "foundations": [(), (), (), ()],
            # fmt: off
            "stock": reversed("JD,3D,TD,TS,6S,8H,AS,2D,JS,9H,4C,9C,4S,7S,2C,9S,AH,TC,AD,QH,JC,7C,8D,4H".split(",")),
            # fmt: on
            "waste": (),
            "tableau": [
                ("3H",),
                ("ks", "6D"),
                ("7d", "3c", "5H"),
                ("5c", "qc", "4d", "TH"),
                ("3s", "6h", "kc", "ac", "QD"),
                ("8c", "jh", "2h", "8s", "9d", "6C"),
                ("kh", "5d", "7h", "kd", "5s", "2s", "QS"),
            ],
        }
        state = init_from_dict(d)
        self.assertTrue(state_is_dead_end(state))

    def test_state_dead_end_faceup_stack(self):
        # Figure 8a from Bjarnason et al (2007) with two faceup cards blocking tableau
        stockstr = (
            "3D,TD,TS,6S,8H,AS,2D,JS,9H,4C,9C,4S,7S,2C,9S,AH,TC,AD,QH,JC,7C,8D,4H"
        )
        d = {
            "foundations": [(), (), (), ()],
            "stock": reversed(stockstr.split(",")),
            "waste": (),
            "tableau": [
                ("3H",),
                ("ks", "6D"),
                ("7d", "3c", "5H"),
                ("5c", "qc", "4d", "TH"),
                ("3s", "6h", "kc", "ac", "QD"),
                ("8c", "jh", "2h", "8s", "9d", "6C"),
                ("kh", "5d", "7h", "kd", "5s", "2s", "QS", "JD"),
            ],
        }
        state = init_from_dict(d)
        self.assertTrue(state_is_dead_end(state))

    def test_state_dead_end_bjarnason2007_fig8b(self):
        stockstr = (
            "TS,5C,QC,2H,3D,6C,AC,2C,5S,4H,4S,JH,TC,6S,AD,7C,KH,6D,KD,3H,8C,9H,9C"
        )
        d = {
            "foundations": [(), (), (), ()],
            "stock": reversed(stockstr.split(",")),
            "waste": (),
            "tableau": [
                ("KC",),
                ("2d", "3C"),
                ("8s", "2s", "5D", "4C"),
                ("8d", "7h", "qd", "JD"),
                ("7d", "4d", "8h", "QH", "JS"),
                ("ks", "as", "ah", "7s", "9s", "QS"),
                ("5h", "3s", "9d", "jc", "6h", "th", "TD"),
            ],
        }
        state = init_from_dict(d)
        state = play_move(state, "75")  # move TD from 7 onto 5 (JS,TD)
        self.assertTrue(state_is_dead_end(state))

    def test_not_dead_end_1(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","2S","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH","KH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": (),
        }
        state = init_from_dict(d)
        # self.assertTrue(state_is_win(state))
        self.assertFalse(state_is_dead_end(state))

    def test_not_dead_end_2(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","2S","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": ("KH",),
        }
        state = init_from_dict(d)
        self.assertFalse(state_is_dead_end(state))

    def test_not_dead_end_3(self):
        game = {
            "foundation": [
                ["AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC"],
                ["AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD"],
                ["AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS"],
                ["AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH"],
            ],
            "waste": [],
            "stock": [],
            "tableau": [
                ["KD", "QS"],
                ["KH", "QC"],
                [],
                ["KC"],
                ["QH"],
                ["KS", "QD"],
                [],
            ],
        }
        state = init_from_ui_state(game)
        self.assertFalse(state_is_dead_end(state))

    def test_not_dead_end_4(self):
        state = KlonState(
            stock=(
                # fmt: off
                "QC", "5C", "AS", "JS", "KS", "9D", "5D", "3S", "6C", "8H", "6D", "9C",
                "TD", "KH", "7H", "JH", "QS", "8D", "3C", "QD", "4S", "5S", "7S", "AH",
                # fmt: on
            ),
            tableau1=("3H",),
            tableau2=("9h", "JC"),
            tableau3=("7d", "4c", "4D"),
            tableau4=("2d", "ad", "tc", "2C"),
            tableau5=("kc", "6h", "2h", "ts", "KD"),
            tableau6=("ac", "5h", "3d", "9s", "7c", "2S"),
            tableau7=("4h", "8s", "jd", "qh", "th", "8c", "6S"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(state_is_dead_end(state))

    def test_not_dead_end_5(self):
        state = KlonState(
            stock=(
                # fmt: off
                "QC", "5C", "AS", "JS", "KS", "9D", "5D", "3S", "6C", "8H", "6D",
                "9C", "TD", "KH", "7H", "JH", "QS", "8D", "3C", "QD", "4S",
                # fmt: on
            ),
            tableau1=("3H", "2C"),
            tableau2=("9h", "JC"),
            tableau3=("7d", "4c", "4D"),
            tableau4=("2d", "ad", "TC"),
            tableau5=("kc", "6h", "2h", "ts", "KD"),
            tableau6=("ac", "5h", "3d", "9s", "7c", "2S"),
            tableau7=("4h", "8s", "jd", "qh", "th", "8c", "6S"),
            waste=("AH", "7S", "5S"),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(state_is_dead_end(state))

    def test_all_cards_faceup_1(self):
        state = KlonState(
            stock=(),
            tableau1=("KD", "QC", "JD"),
            tableau2=("KS", "QD"),
            tableau3=("KH",),
            tableau4=("KC", "QH", "JS"),
            tableau5=(),
            tableau6=(),
            tableau7=("QS",),
            waste=(),
            foundation1=(
                "AC",
                "2C",
                "3C",
                "4C",
                "5C",
                "6C",
                "7C",
                "8C",
                "9C",
                "TC",
                "JC",
            ),
            foundation2=("AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "TD"),
            foundation3=("AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "TS"),
            foundation4=(
                "AH",
                "2H",
                "3H",
                "4H",
                "5H",
                "6H",
                "7H",
                "8H",
                "9H",
                "TH",
                "JH",
            ),
        )
        self.assertTrue(all_cards_faceup(state))

    def test_all_cards_faceup_2(self):
        state = KlonState(
            stock=(),
            tableau1=("KH", "QC"),
            tableau2=("KC",),
            tableau3=("KD", "QS", "JH"),
            tableau4=(),
            tableau5=("QH",),
            tableau6=("KS", "QD", "JS"),
            tableau7=(),
            waste=(),
            foundation1=(
                "AC",
                "2C",
                "3C",
                "4C",
                "5C",
                "6C",
                "7C",
                "8C",
                "9C",
                "TC",
                "JC",
            ),
            foundation2=(
                "AD",
                "2D",
                "3D",
                "4D",
                "5D",
                "6D",
                "7D",
                "8D",
                "9D",
                "TD",
                "JD",
            ),
            foundation3=("AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "TS"),
            foundation4=("AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "TH"),
        )
        self.assertTrue(all_cards_faceup(state))

    def test_all_cards_faceup_3(self):
        state = KlonState(
            stock=(),
            tableau1=(),
            tableau2=("KH", "QC", "JD", "TC", "9H"),
            tableau3=("KS", "QD", "JS", "TH", "9S"),
            tableau4=("JH", "TS", "9D"),
            tableau5=(),
            tableau6=("KC", "QH", "JC", "TD", "9C"),
            tableau7=(),
            waste=("KD", "QS"),
            foundation1=("AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C"),
            foundation2=("AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D"),
            foundation3=("AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S"),
            foundation4=("AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H"),
        )
        self.assertTrue(all_cards_faceup(state))

    def test_all_cards_faceup_4(self):
        state = KlonState(
            stock=(),
            tableau1=(),
            tableau2=(),
            tableau3=(),
            tableau4=(),
            tableau5=(),
            tableau6=(),
            tableau7=(),
            waste=(),
            foundation1=(
                "AC",
                "2C",
                "3C",
                "4C",
                "5C",
                "6C",
                "7C",
                "8C",
                "9C",
                "TC",
                "JC",
                "QC",
                "KC",
            ),
            foundation2=(
                "AD",
                "2D",
                "3D",
                "4D",
                "5D",
                "6D",
                "7D",
                "8D",
                "9D",
                "TD",
                "JD",
                "QD",
                "KD",
            ),
            foundation3=(
                "AS",
                "2S",
                "3S",
                "4S",
                "5S",
                "6S",
                "7S",
                "8S",
                "9S",
                "TS",
                "JS",
                "QS",
                "KS",
            ),
            foundation4=(
                "AH",
                "2H",
                "3H",
                "4H",
                "5H",
                "6H",
                "7H",
                "8H",
                "9H",
                "TH",
                "JH",
                "QH",
                "KH",
            ),
        )
        self.assertTrue(all_cards_faceup(state))

    def test_not_all_cards_faceup_1(self):
        state = KlonState(
            stock=(),
            tableau1=("KC", "QH", "JC", "TH"),
            tableau2=("KS", "QD"),
            tableau3=(),
            tableau4=("jh", "9h", "JS", "TD"),
            tableau5=("KH", "QS"),
            tableau6=(),
            tableau7=("KD", "QC", "JD", "TS", "9D"),
            waste=("8D",),
            foundation1=("AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "TC"),
            foundation2=("AD", "2D", "3D", "4D", "5D", "6D", "7D"),
            foundation3=("AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S"),
            foundation4=("AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H"),
        )
        self.assertFalse(all_cards_faceup(state))

    def test_not_all_cards_faceup_2(self):
        state = KlonState(
            stock=(),
            tableau1=("KC", "QH", "JC"),
            tableau2=("TH",),
            tableau3=("KH", "QS"),
            tableau4=(),
            tableau5=(),
            tableau6=("qc", "8h", "JS"),
            tableau7=(),
            waste=("JH", "9H", "KS"),
            foundation1=("AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "TC"),
            foundation2=(
                "AD",
                "2D",
                "3D",
                "4D",
                "5D",
                "6D",
                "7D",
                "8D",
                "9D",
                "TD",
                "JD",
                "QD",
                "KD",
            ),
            foundation3=("AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "TS"),
            foundation4=("AH", "2H", "3H", "4H", "5H", "6H", "7H"),
        )
        self.assertFalse(all_cards_faceup(state))

    def test_not_all_cards_faceup_3(self):
        state = KlonState(
            stock=(),
            tableau1=(),
            tableau2=(),
            tableau3=("KC", "QH", "JS", "TD"),
            tableau4=("KD", "QS"),
            tableau5=("KS", "QD"),
            tableau6=(),
            tableau7=("qc", "KH"),
            waste=("JC", "JD", "9D"),
            foundation1=("AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "TC"),
            foundation2=("AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D"),
            foundation3=("AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "TS"),
            foundation4=(
                "AH",
                "2H",
                "3H",
                "4H",
                "5H",
                "6H",
                "7H",
                "8H",
                "9H",
                "TH",
                "JH",
            ),
        )
        self.assertFalse(all_cards_faceup(state))

    def test_not_all_cards_faceup_4(self):
        state = KlonState(
            stock=("9H", "KD", "QC", "3S", "KC", "9C", "6D", "JC"),
            tableau1=("KS", "QD", "JS"),
            tableau2=("5h", "4S"),
            tableau3=("9s", "jd", "8C", "7D"),
            tableau4=("2s", "8h", "3d", "8D", "7C"),
            tableau5=("7s", "6s", "5c", "4H", "3C", "2H"),
            tableau6=("2c", "as", "qs", "ts", "3h", "7H", "6C", "5D"),
            tableau7=("ah", "ac", "6h", "9d", "qh", "4c", "4D"),
            waste=("5S", "8S", "KH", "TC", "TH", "JH", "TD"),
            foundation1=(),
            foundation2=("AD", "2D"),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(all_cards_faceup(state))

    def test_not_all_cards_faceup_5(self):
        state = KlonState(
            stock=(
                "TS",
                "AC",
                "8D",
                "7D",
                "6H",
                "KH",
                "8C",
                "7S",
                "KD",
                "AS",
                "7H",
                "4C",
                "6C",
                "5H",
                "5C",
                "KS",
                "9H",
                "JH",
                "5D",
                "7C",
                "JD",
                "KC",
                "3S",
                "9S",
            ),
            tableau1=("4H",),
            tableau2=("th", "AH"),
            tableau3=("4s", "8s", "5S"),
            tableau4=("qd", "4d", "qh", "9D"),
            tableau5=("ad", "jc", "td", "tc", "6D"),
            tableau6=("qc", "8h", "js", "9c", "6s", "QS"),
            tableau7=("2h", "3d", "2c", "2s", "2d", "3h", "3C"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(all_cards_faceup(state))

    def test_state_is_legal_1(self):
        self.assertTrue(state_is_legal(self.state))

    def test_state_is_legal_2(self):
        state = KlonState(
            # fmt: off
            stock=(
                "TS", "AC", "8D", "7D", "6H", "KH", "8C", "7S", "KD", "AS", "7H", "4C",
                "6C", "5H", "5C", "KS", "9H", "JH", "5D", "7C", "JD", "KC", "3S", "9S",
            ),
            # fmt: on
            tableau1=("4H",),
            tableau2=("th", "AH"),
            tableau3=("4s", "8s", "5S"),
            tableau4=("qd", "4d", "qh", "9D"),
            tableau5=("ad", "jc", "td", "tc", "6D"),
            tableau6=("qc", "8h", "js", "9c", "6s", "QS"),
            tableau7=("2h", "3d", "2c", "2s", "2d", "3h", "3C"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertTrue(state_is_legal(state))

    def test_state_is_legal_3(self):
        game = {
            "foundation": [
                ["AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC"],
                ["AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD"],
                ["AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS"],
                ["AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH"],
            ],
            "waste": [],
            "stock": [],
            "tableau": [
                ["KD", "QS"],
                ["KH", "QC"],
                [],
                ["KC"],
                ["QH"],
                ["KS", "QD"],
                [],
            ],
        }
        state = init_from_ui_state(game)
        self.assertTrue(state_is_legal(state))

    def test_state_is_legal_4(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","2S","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH","KH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": (),
        }
        state = init_from_dict(d)
        self.assertTrue(state_is_legal(state))

    def test_state_is_not_legal_1(self):
        d = {
            # fmt: off
            "foundations": [
                ("2C","AC","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"), # 2C before AC
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","2S","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH","KH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": (),
        }
        state = init_from_dict(d)
        self.assertFalse(state_is_legal(state))

    def test_state_is_not_legal_2(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AS","3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"), # 3S on top of AS
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH","KH"),
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": (),
        }
        state = init_from_dict(d)
        self.assertFalse(state_is_legal(state))

    def test_state_is_not_legal_3(self):
        d = {
            # fmt: off
            "foundations": [
                ("AC","2C","3C","4C","5C","6C","7C","8C","9C","TC","JC","QC","KC"),
                ("AD","2D","3D","4D","5D","6D","7D","8D","9D","TD","JD","QD","KD"),
                ("AH","2H","3H","4H","5H","6H","7H","8H","9H","TH","JH","QH","KH"), # Hearts in Spade stack
                ("AS",'2S',"3S","4S","5S","6S","7S","8S","9S","TS","JS","QS","KS"), # and vice versa
            ],
            # fmt: on
            "stock": (),
            "tableau": [(), (), (), (), (), (), ()],
            "waste": (),
        }
        state = init_from_dict(d)
        self.assertFalse(state_is_legal(state))

    def test_state_is_not_legal_4(self):
        state = KlonState(
            # fmt: off
            stock=(
                "TS", "AC", "8D", "7D", "6H", "KH", "8C", "7S", "KD", "AS", "7H", "4C",
                "6C", "5H", "5C", "KS", "9H", "JH", "5D", "7C", "JD", "KC", "3S", "9S",
            ),
            # fmt: on
            tableau1=("4H",),
            tableau2=("th", "AH"),
            tableau3=("4s", "8s", "5S"),
            tableau4=("qd", "4d", "qh", "9D"),
            tableau5=("ad", "jc", "td", "tc", "6D", "QS"),  # not in value order
            tableau6=("qc", "8h", "js", "9c", "6s"),
            tableau7=("2h", "3d", "2c", "2s", "2d", "3h", "3C"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(state_is_legal(state))

    def test_state_is_not_legal_5(self):
        state = KlonState(
            # fmt: off
            stock=(
                "TS", "AC", "8D", "7D", "6H", "KH", "8C", "7S", "KD", "AS", "7H", "4C",
                "6C", "5H", "5C", "KS", "9H", "JH", "5D", "7C", "JD", "KC", "3S", "9S",
            ),
            # fmt: on
            tableau1=("4H",),
            tableau2=("th", "AH"),
            tableau3=("4s", "8s", "5S"),
            tableau4=("qd", "4d", "qh", "9D"),
            tableau5=("ad", "jc", "td", "tc", "6D"),
            tableau6=("qc", "8h", "js", "9c", "6s", "qs"),  # last face down
            tableau7=("2h", "3d", "2c", "2s", "2d", "3h", "3C"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(state_is_legal(state))

    def test_state_is_not_legal_6(self):
        state = KlonState(
            # fmt: off
            stock=(
                "TS", "AC", "8D", "7D", "6H", "KH", "8C", "7S", "KD", "AS", "7H", "4C",
                "6C", "5H", "5C", "KS", "9H", "JH", "5D", "7C", "JD", "KC", "3S", "9S",
            ),
            # fmt: on
            tableau1=("4H",),
            tableau2=("th", "AH"),
            tableau3=("4s", "8s", "5S"),
            tableau4=("qd", "4d", "qh", "9D"),
            tableau5=("ad", "jc", "td", "tc", "6D"),
            tableau6=("qc", "8h", "js", "9c", "6S"),  # missing QS
            tableau7=("2h", "3d", "2c", "2s", "2d", "3h", "3C"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(state_is_legal(state))

    def test_state_is_not_legal_6(self):
        state = KlonState(
            # fmt: off
            stock=(
                "TS", "AC", "8D", "7D", "6H", "KH", "8C", "7S", "KD", "AS", "7H", "4C",
                "6C", "5C", "KS", "9H", "JH", "5D", "7C", "JD", "KC", "3S", "9S",
            ),
            # fmt: on
            tableau1=("4H",),
            tableau2=("th", "AH"),
            tableau3=("4s", "8s", "5S"),
            tableau4=("qd", "4d", "qh", "9D"),
            tableau5=("ad", "jc", "td", "tc", "6D", "5H"),  # invalid rank stack
            tableau6=("qc", "8h", "js", "9c", "6s", "QS"),
            tableau7=("2h", "3d", "2c", "2s", "2d", "3h", "3C"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        self.assertFalse(state_is_legal(state))

    ###### Vectorizing

    def test_state_to_vec_is_an_array_of_expected_size(self):
        vec = state_to_vec(self.state)
        self.assertEqual(vec.shape, (233, 104))

    def test_state_to_vec_inversion_1(self):
        transformed = vec_to_state(state_to_vec(self.state))
        self.assertEqual(transformed, self.state)

    def test_state_to_vec_inversion_2(self):
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
        transformed = vec_to_state(state_to_vec(state))
        self.assertEqual(transformed, state)

    def test_vector_legal_moves(self):
        state = KlonState(
            # fmt: off
            stock=(
                "TH", "8D", "7H", "KC", "3D", "TD", "5H", "8C", "QS", "JS", "9H", "7C",
                "6D", "8S", "QD", "QH", "AC", "9C", "5S", "KH", "QC", "2S", "TC", "9D",
            ),
            # fmt: on
            tableau1=("4D",),
            tableau2=("3c", "4C"),
            tableau3=("9s", "7d", "6H"),
            tableau4=("ah", "7s", "2c", "JD"),
            tableau5=("ad", "6s", "2h", "ts", "AS"),
            tableau6=("4h", "8h", "2d", "ks", "jc", "5C"),
            tableau7=("3h", "4s", "3s", "5d", "jh", "6c", "KD"),
            waste=(),
            foundation1=(),
            foundation2=(),
            foundation3=(),
            foundation4=(),
        )
        # fmt: off
        expected = np.array([
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1,
            1, 1, 1, 1, 1, 0, 0])
        # fmt: on
        actual = vector_legal_moves(state)
        self.assertTrue(np.array_equal(actual, expected))
        # assert the reference moves vector has the expected size
        self.assertEqual(actual.shape, (623,))

    def test_to_pretty_string(self):
        game = {
            "foundation": [
                ["AC", "2C", "3C", "4C", "5C", "6C", "7C", "8C", "9C", "10C", "JC"],
                ["AD", "2D", "3D", "4D", "5D", "6D", "7D", "8D", "9D", "10D", "JD"],
                ["AS", "2S", "3S", "4S", "5S", "6S", "7S", "8S", "9S", "10S", "JS"],
                ["AH", "2H", "3H", "4H", "5H", "6H", "7H", "8H", "9H", "10H", "JH"],
            ],
            "waste": [],
            "stock": [],
            "tableau": [
                ["KD", "QS"],
                ["KH", "QC"],
                [],
                ["KC"],
                ["QH"],
                ["KS", "QD"],
                [],
            ],
        }
        state = init_from_ui_state(game)
        actual = to_pretty_string(state)
        expected = """Stock:
        Waste:
        Fnd C: AC 2C 3C 4C 5C 6C 7C 8C 9C TC JC
        Fnd D: AD 2D 3D 4D 5D 6D 7D 8D 9D TD JD
        Fnd S: AS 2S 3S 4S 5S 6S 7S 8S 9S TS JS
        Fnd H: AH 2H 3H 4H 5H 6H 7H 8H 9H TH JH
        Tab 1: KD QS
        Tab 2: KH QC
        Tab 3:
        Tab 4: KC
        Tab 5: QH
        Tab 6: KS QD
        Tab 7: """
        for line_act, line_exp in zip(actual.splitlines(), expected.splitlines()):
            self.assertEqual(line_act.strip(), line_exp.strip())


if __name__ == "__main__":
    unittest.main()
