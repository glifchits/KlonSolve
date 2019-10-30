import os
import pytest
import unittest
from flaky import flaky
from timeout_decorator import timeout, TimeoutError
from solver import solve
from tuplestate import (
    init_from_ui_state,
    init_from_solvitaire,
    state_is_win,
    copy,
    play_move,
)
from benchmarking import convert_shootme_to_solvitaire_json


TIMEOUT = "TIMEOUT"


@timeout(1)
def solve_under_1sec(initial_state):
    solution = solve(initial_state)
    return solution


def quick_solve(state, attempts=5):
    while attempts > 0:
        try:
            return solve_under_1sec(state)
        except TimeoutError:
            pass
        except AssertionError:
            pass
        finally:
            attempts -= 1
    return TIMEOUT


def validate_move_seq(state, move_seq):
    state = copy(state)
    for move in move_seq:
        state = play_move(state, move)
    return state_is_win(state)


@pytest.mark.skipif(os.environ.get("GITHUB_ACTION") != None, reason="In CI environment")
class TestSolver(unittest.TestCase):
    @flaky(max_runs=10, min_passes=2)
    def test_a_game(self):
        game = {
            "foundation": [[], [], [], []],
            "waste": [],
            "stock": [
                "kc",
                "9c",
                "qc",
                "8c",
                "3c",
                "7s",
                "7h",
                "10c",
                "4c",
                "7d",
                "ks",
                "ad",
                "qs",
                "kh",
                "qd",
                "10h",
                "8s",
                "ah",
                "6h",
                "4h",
                "as",
                "2d",
                "10d",
                "3h",
            ],
            "tableau": [
                ["8H"],
                ["3d", "6C"],
                ["5s", "jd", "JS"],
                ["2h", "kd", "7c", "9S"],
                ["qh", "8d", "jc", "2c", "AC"],
                ["4s", "6s", "2s", "3s", "9d", "5C"],
                ["5h", "6d", "5d", "4d", "10s", "9h", "JH"],
            ],
        }
        state = init_from_ui_state(game)
        solution = quick_solve(state)
        self.assertNotEqual(solution, TIMEOUT, "timed out")
        self.assertNotEqual(solution, False, "game incorrectly deemed unsolvable")
        self.assertTrue(validate_move_seq(state, solution))

    @flaky(max_runs=10, min_passes=2)
    def test_seed_47(self):
        with open("./fixtures/shootme/solvedmin/47.txt") as f:
            ret = f.read()
        deck_json = convert_shootme_to_solvitaire_json(ret)
        state = init_from_solvitaire(deck_json)
        solution = quick_solve(state)
        self.assertNotEqual(solution, TIMEOUT)
        self.assertNotEqual(solution, False)
        self.assertTrue(validate_move_seq(state, solution))


if __name__ == "__main__":
    unittest.main()
