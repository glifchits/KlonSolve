import numpy as np
# import matplotlib.pyplot as plt
from itertools import count
import itertools
from collections import namedtuple, defaultdict
# from tqdm import tqdm, trange
import os
import json
# import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable
from torch.distributions import Categorical        
from itertools import islice
import time
from datetime import datetime
import shutil
import subprocess
import pandas as pd
import multiprocessing

now = datetime.now()
datestr = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}"

# %matplotlib inline

import random
from tuplestate import *
from gamestate import *
from benchmarking import *
from vectorize import *
random.seed(0)

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print('cuda?', device)


def solve_state(ret):
    lines = ret.splitlines()
    result = lines[15]
    if result.startswith('Minimal solution'):
        return "Solved-Min"
    elif result.startswith("Solved"):
        return "Solved"
    elif result.startswith('Impossible'):
        return "Impossible"
    elif result.startswith('Unknown'):
        return "Unknown"

def clf_seeds(seedlist):
    results = defaultdict(set)
    for seed in seedlist:
        with open(f"./bench/shootme/{seed}") as f:
            ret = f.read()
            result = solve_state(ret)
            results[result].add(seed)
    return results

def clf_summary(seedlist):
    results = clf_seeds(seedlist)
    states = ['Solved-Min', 'Solved', 'Impossible', 'Unknown']
    for clfstate in states:
        seeds = results[clfstate]
        print(f"{clfstate:12} {len(seeds):8,}")
        total = sum(len(s) for s in results.values())
    print(('-'*12) + '-' + ('-'*8))
    print(f"{'Total':12} {total:8,}") 
          
def get_state(ret):
    deck_json = convert_shootme_to_solvitaire_json(ret)
    return init_from_solvitaire(deck_json)

def map_seeds_to_states(seed_seq):
    for seed in seed_seq:
        with open(f"./bench/shootme/{seed}") as f:
            ret = f.read()
            state = get_state(ret)
            yield seed, state


results = defaultdict(set)
all_solutions = os.listdir('./bench/shootme/')
seeds = list(map(lambda fname: int(fname[:-4]), all_solutions))

def solve_state(ret):
    lines = ret.splitlines()
    result = lines[15]
    if result.startswith('Minimal solution'):
        return "Solved-Min"
    elif result.startswith("Solved"):
        return "Solved"
    elif result.startswith('Impossible'):
        return "Impossible"
    elif result.startswith('Unknown'):
        return "Unknown"

for seed in sorted(seeds):
    with open(f"bench/shootme/{seed}.txt") as f:
        ret = f.read()
        result = solve_state(ret)
        results[result].add(seed)
    
seed_class = {}
for cls in results.keys():
    seeds_cls = results[cls]
    for seed in seeds_cls:
        seed_class[seed] = cls
          
print('loaded seeds')
          
IN = 233*104
OUT = 623

Args = namedtuple('Args', 'gamma lr seed render log_interval')
args = Args(
    gamma=0.5,
    lr=5e-2,
    seed=1,
    render=False,
    log_interval=20)


class Policy(nn.Module):
    def __init__(self):
        super(Policy, self).__init__()
        self.inlayer = nn.Linear(IN, 233*10)
        self.linear1 = nn.Linear(233*10, 1000)
#         self.linear2 = nn.Linear(233*10, 1000)
        self.outlayer = nn.Linear(1000, OUT)
        self.dropout = nn.Dropout(p=0.6)
        self.saved_log_probs = []
        self.rewards = []

    def forward(self, x):
        x = self.inlayer(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.linear1(x)
        x = F.relu(x)
#         x = self.dropout(x)
#         x = self.linear2(x)
#         x = F.relu(x)
        action_scores = self.outlayer(x)
        return F.softmax(action_scores, dim=1)


def select_action(klonstate):
    state_vec = state_to_vec(klonstate)
    movefilter = vector_legal_moves(klonstate)
    torch_state_vec = torch.from_numpy(state_vec).float().reshape(-1).unsqueeze(0).to(device)
    torch_filter = torch.from_numpy(movefilter.astype(np.float32)).unsqueeze(0).to(device)
    probs = policy(torch_state_vec) * torch_filter
    if (probs == 0).all():
        torch_filter.requires_grad_()
        # sample all legal moves with uniform probability
        m = Categorical(torch_filter)
    else:
        # :attr:`probs` will be normalized to sum to 1
        m = Categorical(probs)
    action = m.sample()
    log_prob = m.log_prob(action)
    policy.saved_log_probs.append(log_prob)
    del torch_state_vec
    del torch_filter
    return action.item()

    
def step(curr_state, move_code):
    new_state = play_move(curr_state, move_code)
    reward = 0  
    if state_is_win(new_state) or all_cards_faceup(new_state):
        reward = 1
    if not state_is_legal(new_state):
        print('\n got illegal state by playing move', move_code)
        print('prev state')
        print(to_pretty_string(curr_state))
        print('\nnew state')
        print(to_pretty_string(new_state))
        assert state_is_legal(new_state), 'got illegal state'
    return new_state, reward

          
def score_state(klonstate):
    fnds = [klonstate.foundation1, klonstate.foundation2, 
            klonstate.foundation3, klonstate.foundation4]
    return sum(map(len, fnds))

      
policy = Policy()
policy.to(device)

# optimizer = optim.SGD(policy.parameters(), lr=1e-2)
eps = np.finfo(np.float32).eps.item()

random.seed(0)
# train_seeds = random.sample(all_solutions, k=100)
# print('Training game set')
# clf_summary(train_seeds)

training_games = map_seeds_to_states(all_solutions)
          
argsstr = f"gamma-{args.gamma}"
PATH = f'./models/mymodel-policy-201912132128-gamma-0.5.torch'

policy.load_state_dict(torch.load(PATH))
policy.eval()

          
solve_results = defaultdict(dict)
resultfile = f"solve_results/{datestr}_mymodel-policy-201912132128-gamma-0.5.json"

######### BENCHMARKING CODE
def map_seeds_to_states(seed_seq):
    for seed in seed_seq:
        with open(f"bench/shootme/{seed}.txt") as f:
            ret = f.read()
            state = get_state(ret)
            yield seed, state

def get_seeds(fname):
    with open(fname) as f:
        return map(int, f.read().strip().split(' '))
    
    
def get_suite_states(fname):
    return list(map_seeds_to_states(get_seeds(fname)))


def get_suite_files(size):
    pref = f'./bench/suites/{size}/'
    ls = sorted(os.listdir(pref))
    if len(ls) == 0:
        raise Exception(f"no suite files in {pref}")
    return [os.path.join(pref, f) for f in ls]


Result = namedtuple('Result', 
    ['seed', 'time', 
     'solved', 'visited', 'msg',
     'seq', 'seqlen', 
     'datetime', 'shootme']
)
          
          
# for i, env in enumerate(training_games):
#     seed, klonstate = env
# #     print(seed)
#     ep_reward = 0
#     done = False
#     path = []
#     visited = set()
#     for t in range(1, 2000):
#         action_idx = select_action(klonstate)
#         move_code = all_moves[action_idx]
#         klonstate, reward = step(klonstate, move_code)
#         done = reward != 0
#         if done:
#             break
#     final_score = score_state(klonstate)
#     print(f"{i:4}  ep reward {ep_reward:.2f}   steps {t:3}   final score {final_score}")#, end=' ')
#     if ep_reward > 0:
#         print("Solved?!!")
#         print(to_pretty_string(klonstate))
# #     print('final score', score_state(klonstate))
# #     print('path', path)
# #     print('final state')
# #     print(to_pretty_string(klonstate))

#     if i % 50 == 0 and i > 40:
#         solve_results[seed] = {
#             'state': klonstate,
#             'path': path,
#             'reward': reward,
#             'steps': t,
#             'score_state': score_state(klonstate),
#         }
#         with open(resultfile, 'w') as f:
#             json.dump(solve_results, f)
          
def run_solver(seedstate, max_states=10_000):
    seed, klonstate = seedstate
    print(f"working on seed {seed}")
    shootme = seed_class[seed]
    path = []
    start = time.time()
    visited = set()
    for t in range(1, max_states):
        action_idx = select_action(klonstate)
        move_code = all_moves[action_idx]
        path.append(move_code)
        klonstate, reward = step(klonstate, move_code)
        visited.add(klonstate)
        done = reward != 0
        if done:
            break
    end = time.time()
    elapsed = end-start
    
    now = datetime.now().isoformat()
    is_solved = state_is_win(klonstate)
    final_score = score_state(klonstate)
    msg = f"{now}: finished, is solved? {is_solved}  took {elapsed:.2f}, score {final_score} (shootme: {shootme})"
    print(msg)
    return Result(
        seed=seed, time=elapsed,
        solved=is_solved,
        visited=len(visited),
        msg=msg,
        seq=path, seqlen=len(path), 
        datetime=now, shootme=shootme
    )

# def run_solver(seedstate):
#     seed, state = seedstate
#     start = time.time()
#     sol = solve(state, max_states=10_000)
#     seq = None
#     seqlen = -1
#     if sol.solved:
#         seq = " ".join(sol.moveseq)
#         seqlen = len(seq)
#     end = time.time()
#     elapsed = end-start
#     shootme = seed_class[seed]
#     now = datetime.now().isoformat()
#     return Result(
#         seed=seed, time=elapsed,
#         solved=sol.solved,
#         visited=sol.visited,
#         msg=sol.msg,
#         seq=seq, seqlen=seqlen, 
#         datetime=now, shootme=shootme
#     )



proc = subprocess.Popen("git log --pretty=oneline | head -c 10", shell=True, stdout=subprocess.PIPE)
out, err = proc.communicate()
git = out.decode('ascii')
foldername = f"suite-10-torch-reinforce-201912132128-{datestr}-{git}"
folderpath = os.path.join("./bench/", foldername)

# try:
#     shutil.rmtree(folderpath)
# except FileNotFoundError:
#     pass
# print(folderpath)

def timestr():
    now = datetime.now()
    return now.strftime("%Y%m%d-%H%M%S")

def save_results(results, suite_file):
    df = pd.DataFrame(results)
    fname = os.path.join(folderpath, f"{suite_file}-{timestr()}.csv")
    df.to_csv(fname)

          
if not os.path.exists(folderpath):
    os.makedirs(folderpath)

# with multiprocessing.Pool() as pool:
for suite_file in get_suite_files(size=10):
    print(f"starting {suite_file}")
    states = get_suite_states(suite_file)
    ret = map(run_solver, states)
    _, fname = os.path.split(suite_file)
    fname, _ = os.path.splitext(fname)
    save_results(ret, fname)
    print(f'done {suite_file}')
