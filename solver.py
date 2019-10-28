import re
import sys
from tuplestate import *

sys.setrecursionlimit(10 ** 6)

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


def add(my_frozenset, new_value):
    return my_frozenset.union(set([new_value]))


def visit_state(visit_set, state):
    return add(visit_set, hash(state))


def was_visited(state, visited):
    return hash(state) in visited


def append(tup, val):
    return tup + (val,)


def reject(state):
    """ return True if the state is not winnable, else False """
    pass


build2suit = re.compile(r"^([1-7])([CDSH])$")
talon2build = re.compile(r"^W([1-7])$")
suit2build = re.compile(r"^([CDSH])([1-7])$")
drawmove = re.compile(r"^DR([1-9][0-9]?)$")


def prioritize(move_list):
    """re-order the given move list by how
    promising the moves are, descending """
    # Yan et al (2005)
    # - moved from a build stack to a suit stack, gain 5 points
    # - moved from the talon to a build stack, gain 5 points
    # - moved from a suit stack to a build stack, lose 10 points
    def score_move(move_code):
        if build2suit.match(move_code):
            return 5
        elif talon2build.match(move_code):
            return 5
        elif suit2build.match(move_code):
            return -10
        elif drawmove.match(move_code):
            # my own rule, not in Yan et al
            return -1
        else:
            return 0

    return sorted(move_list, key=score_move, reverse=True)


visited = set()


def gameplay(state, move_seq):
    if was_visited(state, visited):
        return False
    if state_is_win(state):
        return True
    visited.add(hash(state))
    moves = get_legal_moves(state)

    for move_code in prioritize(moves):
        new_state = play_move(state, move_code)
        is_a_win_state = gameplay(state=new_state, move_seq=append(move_seq, move_code))
        if is_a_win_state:
            print("WIN!!!!")
            pprint_st(new_state)
            return new_state


if __name__ == "__main__":
    gameplay(state=init_from_ui_state(game), move_seq=())
