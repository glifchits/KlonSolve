import numpy as np
import torch
import itertools
from gamestate import *
from benchmarking import *
from vectorize import *
from klon_tree import KlonTree

MAX_DATA = 100
SEED = 0


def seed_sequence(all_seeds):
    seeds = sorted(list(all_seeds["Solved-Min"].union(all_seeds["Solved"])))
    rand = np.random.RandomState(SEED)
    rand.shuffle(seeds)
    for s in seeds:
        yield s


def state_best_action_vec(seed):
    state, seq = state_with_moveseq(f"./bench/shootme/{seed}")
    while len(seq) > 0:
        action = seq.pop()
        state_vec = state_to_vec(state)
        action_vec = vectorize_legal_moves(set([action]))
        yield state_vec, action_vec
        state = play_move(state, action)


if __name__ == "__main__":
    all_seeds = clf_seeds(all_solutions)

    data = []
    for seed in itertools.islice(seed_sequence(all_seeds), MAX_DATA):
        state_actions = state_best_action_vec(seed)
        for s, a in state_actions:
            if all_cards_faceup(vec_to_state(s)):
                continue
            data.append((s, a))

    loader = torch.utils.data.DataLoader(data, batch_size=4)
