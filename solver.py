import sys
import time
from collections import namedtuple
from tuplestate import *
from timebudget import timebudget
from policies import *


sys.setrecursionlimit(10 ** 6)


def solve(state, max_states=50_000, **solver_params):
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
        result = yan_et_al_rollout(state, **solver_params)
        # 2. select and execute a legal move
        if result is None:
            return EndState(solved=False, msg="no avail moves", visited=v)
        if hasattr(result, "solved"):
            return result  # solved in rollout
        # otherwise the rollout gives the old heuristic strategy
        action = result
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

    import os

    for fname in os.listdir("./fixtures/shootme/solvedmin"):
        with open(f"./fixtures/shootme/solvedmin/{fname}") as f:
            ret = f.read()
        print(fname)
        deck_json = convert_shootme_to_solvitaire_json(ret)
        state = init_from_solvitaire(deck_json)
        solution = solve(state, max_states=100_000, k=1)
        # print()
        if solution.solved:
            moveseq = list(solution.moveseq)
            visited = solution.visited
            print(f"solved, visited {visited} states, solved in {len(moveseq)} moves")
            # print(moveseq)
        else:
            print("no solution")
        # print()
