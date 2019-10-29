import unittest
import timeout_decorator
from flaky import flaky
from timeout_decorator import TimeoutError
from solver import solve
from tuplestate import init_from_ui_state


@timeout_decorator.timeout(1)
def solve_under_1sec(initial_state):
    solution = solve(initial_state)
    return solution


class TestSolver(unittest.TestCase):
    @flaky(max_runs=5, min_passes=2)
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
        solution = solve_under_1sec(state)
        self.assertNotEqual(solution, None, "timed out, or erroneously returned None")
        self.assertNotEqual(solution, False, "game incorrectly deemed unsolvable")


if __name__ == "__main__":
    unittest.main()
