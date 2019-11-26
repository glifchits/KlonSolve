import sys
import time
from collections import namedtuple
from tuplestate import *
from timebudget import timebudget
from policies import *


sys.setrecursionlimit(10 ** 6)


@timebudget
def get_actions(state, move_seq):
    """
    input:
        state: current state
        move_seq: sequence of moves taken so far
    output:
        list of moves ordered by descending priority
    """
    return yan_et_al_prioritized_actions(state, move_seq)


EndState = namedtuple(
    "EndState",
    ["solved", "moveseq", "visited", "msg", "impossible"],
    defaults=((None,) * 5),
)


def solve_aux(state, move_seq, visited, max_states):
    if state_is_win(state):
        return EndState(solved=True, moveseq=move_seq, visited=len(visited))

    elif state in visited:
        return False

    visited.add(state)
    if max_states is not None and len(visited) > max_states:
        return EndState(solved=False, visited=len(visited), msg="exceeded max states")

    child_moves = get_actions(state, move_seq)
    for move_code in child_moves:
        child_state = play_move(state, move_code)
        new_moveseq = move_seq + (move_code,)
        ret = solve_aux(child_state, new_moveseq, visited, max_states)
        if ret:
            return ret

    return False  # EndState(solved=False, impossible=True, visited=len(visited))


def solve(state, max_states=50_000):
    visited = set()
    move_seq = ()
    ret = solve_aux(state, move_seq, visited, max_states)
    if ret:
        return ret
    # otherwise looks like we tried all possible moves
    return EndState(solved=False, impossible=True, visited=len(visited))


if __name__ == "__main__":
    from benchmarking import convert_shootme_to_solvitaire_json

    timebudget.report_atexit()

    with open("./fixtures/shootme/solvedmin/407.txt") as f:
        ret = f.read()
    deck_json = convert_shootme_to_solvitaire_json(ret)
    state = init_from_solvitaire(deck_json)
    solution = solve(state, max_states=100_000)
    print()
    if solution.solved:
        moveseq = list(solution.moveseq)
        visited = solution.visited
        print(f"solved, visited {visited} states. Solution has {len(moveseq)} moves\n")
        print(moveseq)
    else:
        print("no solution")
    print()
