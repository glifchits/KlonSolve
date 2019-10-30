import sys
import time
from tuplestate import *
from get_legal_moves import get_legal_moves
from timebudget import timebudget
from policies import yan_et_al


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


def solve_aux(state, move_seq, visited):
    if state_is_win(state):
        return move_seq
    elif state in visited:
        return False
    visited.add(state)
    child_moves = get_actions(state, move_seq)
    for move_code in child_moves:
        child_state = play_move(state, move_code)
        new_moveseq = append(move_seq, move_code)
        ret = solve_aux(child_state, new_moveseq, visited)
        if ret:
            return ret
    return False


def solve(state):
    visited = set()
    move_seq = ()
    return solve_aux(state, move_seq, visited)


if __name__ == "__main__":
    from benchmarking import convert_shootme_to_solvitaire_json

    timebudget.report_atexit()

    with open("./bench/47-solvedmin.txt") as f:
        ret = f.read()
    deck_json = convert_shootme_to_solvitaire_json(ret)
    state = init_from_solvitaire(deck_json)
    solution = solve(state)
    if solution:
        print(list(solution))
