from pprint import pformat


class State:
    def __init__(self, stock, tableau, waste, foundations):
        self.stock = stock
        self.tableau = tableau
        self.waste = waste
        self.foundations = foundations

    def __hash__(self):
        return (
            hash(self.stock)
            + hash(self.tableau)
            + hash(self.waste)
            + hash(self.foundations)
        )

    def __str__(self):
        return pformat(self.to_game_dict())

    @staticmethod
    def init_from_game(game_dict):
        stock = tuple(game_dict["stock"])
        tableau = tuple(
            tuple(card.upper() for card in t) for t in game_dict["tableau piles"]
        )
        waste = tuple(game_dict["waste"])
        foundations = tuple(game_dict.get("foundations", [tuple()] * 4))
        return State(stock, tableau, waste, foundations)

    def to_game_dict(self):
        return {
            "stock": self.stock,
            "tableau piles": self.tableau,
            "waste": self.waste,
            "foundations": self.foundations,
        }

    def _update_stock(self, new_stock):
        return State(new_stock, new_tableau, self.waste, self.foundations)

    def _update_tableau(self, new_tableau):
        return State(self.stock, new_tableau, self.waste, self.foundations)

    def _update_waste(self, new_waste):
        return State(self.stock, self.tableau, new_waste, self.foundations)

    def _update_foundation(self, new_foundation):
        return State(self.stock, self.tableau, self.waste, new_foundation)

    def _pop_tableau(self, src):
        """
        returns (`card`, `new_tableau`)
        """
        new_tableau = list(self.tableau)
        new_talon = list(new_tableau[src])
        card = new_talon.pop()
        new_tableau[src] = tuple(new_talon)
        return card, tuple(new_tableau)

    def _push_tableau(self, card, src):
        """
        add `card` to `src` talon
        returns `new_tableau`
        """
        new_tableau = list(self.tableau)
        new_talon = new_tableau[src] + (card,)
        new_tableau[src] = new_talon
        return tuple(new_tableau)

    def _pop_foundation(self, src):
        """ (card, new_foundation) """
        new_fnds = list(self.foundations)
        new_fnd = list(new_fnds[src])
        card = new_fnd.pop()
        new_fnds[src] = tuple(new_fnd)
        return card, tuple(new_fnds)

    def _push_foundation(self, card, dest):
        """ returns `new foundation` """
        new_fnds = list(self.foundations)
        new_fnd = list(new_fnds[dest])
        new_fnd.append(card)
        new_fnds[dest] = tuple(new_fnd)
        return tuple(new_fnds)

    def move_tableau_to_tableau(self, src, dest):
        card, tab = self._pop_tableau(src)
        s = self._update_tableau(tab)
        tab = s._push_tableau(card, dest)
        return s._update_tableau(tab)

    def move_tableau_to_foundation(self, srct, destf):
        card, tab = self._pop_tableau(srct)
        s = self._update_tableau(tab)
        fnd = s._push_foundation(card, destf)
        s = s._update_foundation(fnd)
        return s

    def move_foundation_to_tableau(self, srcf, destt):
        card, fnd = self._pop_foundation(srcf)
        s = self._update_foundation(fnd)
        tab = s._push_tableau(card, destt)
        s = s._update_tableau(tab)
        return s


import unittest
import json


class TestState(unittest.TestCase):
    def test_init_from_game(self):
        with open("./fixtures/game1.json") as f:
            game = json.load(f)
        state = State.init_from_game(game)
        initial_stock = (
            "10H,8D,7H,KC,3D,10D,5H,8C,QS,JS,9H,7C,"
            "6D,8S,QD,QH,AC,9C,5S,KH,QC,2S,10C,9D"
        )
        self.assertEqual(state.stock, tuple(initial_stock.split(",")))

        piles = [
            ["4D"],
            ["3c", "4C"],
            ["9s", "7d", "6H"],
            ["ah", "7s", "2c", "JD"],
            ["ad", "6s", "2h", "10s", "AS"],
            ["4h", "8h", "2d", "ks", "jc", "5C"],
            ["3h", "4s", "3s", "5d", "jh", "6c", "KD"],
        ]
        self.assertEqual(len(state.tableau), len(piles))
        for actual_pile, expected_pile in zip(state.tableau, piles):
            expected_pile_upper = tuple(c.upper() for c in expected_pile)
            self.assertEqual(tuple(actual_pile), expected_pile_upper)

        self.assertEqual(state.waste, ())
        self.assertEqual(state.foundations, ((), (), (), ()))

    def setUp(self):
        self.state = State(
            stock=("10H", "8D", "7H"),
            foundations=((), (), (), ("AH",)),
            waste=(),
            tableau=(("4D",), ("3C", "7D")),
        )

    def test_tableau_to_tableau(self):
        self.assertEqual(len(self.state.tableau[0]), 1)
        self.assertEqual(len(self.state.tableau[1]), 2)
        s = self.state.move_tableau_to_tableau(0, 1)
        self.assertNotEqual(s, self.state)
        self.assertEqual(s.tableau[0], ())
        self.assertEqual(s.tableau[1], ("3C", "7D", "4D"))

    def test_tableau_to_foundation(self):
        self.assertEqual(len(self.state.tableau[0]), 1)
        self.assertEqual(len(self.state.foundations[0]), 0)
        s = self.state.move_tableau_to_foundation(0, 0)
        self.assertNotEqual(s, self.state)
        self.assertEqual(s.tableau[0], ())
        self.assertEqual(s.foundations[0], ("4D",))

    def test_foundation_to_tableau(self):
        self.assertEqual(len(self.state.tableau[0]), 1)
        self.assertEqual(self.state.foundations[3], ("AH",))
        s = self.state.move_foundation_to_tableau(3, 0)
        self.assertNotEqual(s, self.state)
        self.assertEqual(s.tableau[0], ("4D", "AH"))
        self.assertEqual(s.foundations[3], ())


if __name__ == "__main__":
    unittest.main()


# from state import State
# state = State(stock=("10H", "8D", "7H"),foundations=((), (), (), ()),waste=(),tableau=(("4D",), ("3C", "7D")))
