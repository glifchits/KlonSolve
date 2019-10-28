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
        return True
    elif state in visited:
        return False
    visited.add(state)
    child_moves = get_actions(state, move_seq)
    for move_code in child_moves:
        child_state = play_move(state, move_code)
        if solve(child_state, append(move_seq, move_code)):
            return move_seq
    return False
