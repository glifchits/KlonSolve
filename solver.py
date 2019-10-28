import sys
import time
from tuplestate import *
from get_legal_moves import get_legal_moves
from timebudget import timebudget
from policies import yan_et_al

timebudget.report_atexit()


sys.setrecursionlimit(10 ** 6)


def was_visited(state, visited):
    return hash(state) in visited


def append(tup, val):
    return tup + (val,)


@timebudget
def get_actions(state, move_seq):
    """
    input:
        state: current state
        move_seq: sequence of moves taken so far
    """
    # produce the set of legal moves given this state
    move_list = get_legal_moves(state)

    # policy: function(move_code)
    # - given a move code and the state, score the move.
    # - taken over a set of moves, should order the moves by their desirability
    policy = lambda mc: yan_et_al(mc, state)

    return sorted(move_list, key=policy, reverse=True)


visited = set()


def solve(state, move_seq):
    if state_is_win(state):
        print("WIN")
        print(list(move_seq))
        return True
    elif state in visited:
        return False
    visited.add(state)
    child_moves = get_actions(state, move_seq)
    for move_code in child_moves:
        child_state = play_move(state, move_code)
        if solve(child_state, append(move_seq, move_code)):
            return True
    return False


if __name__ == "__main__":
    print("running solver")
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
    start = time.time()
    ret = solve(init_from_ui_state(game), ())
    end = time.time()
    print(f"finished in {end-start:.2f} s")
    print(f"solved: {ret}")
