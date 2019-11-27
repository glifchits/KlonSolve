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


class EndState:
    def __init__(self, **kwargs):
        self.solved = kwargs.get("solved", None)
        self.moveseq = kwargs.get("moveseq", None)
        self.visited = kwargs.get("visited", None)
        self.msg = kwargs.get("msg", None)
        self.impossible = kwargs.get("impossible", None)


def solve(state, max_states=50_000):
    visited = set()
    moveseq = []
    i = 0
    while True:
        v = len(visited)
        if i >= max_states:
            return EndState(solved=False, visited=v, msg="exceeded max states")
        if state in visited:
            return EndState(solved=False, msg="revisited state", visited=v)
        visited.add(state)
        # Yan et al. Section 4 "Machine Play"
        # 1. identify set of legal moves
        actions = get_actions(state, moveseq)
        # 2. select and execute a legal move
        action = actions[0]
        moveseq.append(action)
        state = play_move(state, action)
        # 3. If all cards are on suit stacks, declare victory and terminate.
        if state_is_win(state):
            return EndState(solved=True, moveseq=moveseq, visited=v)
        # 4. If new card configuration repeats a previous one, declare loss and terminate.
        # 5. Repeat procedure.
        i += 1


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
