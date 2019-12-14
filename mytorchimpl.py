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
# %matplotlib inline

import random
from tuplestate import *
from gamestate import *
from benchmarking import *
from vectorize import *
random.seed(0)
# print(to_pretty_string(klonstate))

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print('cuda?')
print(device)


all_solutions = os.listdir('../shootme/')

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
        with open(f"../shootme/{seed}") as f:
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
        with open(f"../shootme/{seed}") as f:
            ret = f.read()
            state = get_state(ret)
            yield seed, state

print("All seeds")
# clf_summary(all_solutions)
          
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
    return action.item()

def finish_episode():
    R = 0
    policy_loss = []
    returns = []
    for r in policy.rewards[::-1]:
        R = r + args.gamma * R
        returns.insert(0, R)
    returns = torch.tensor(returns)
    returns = (returns - returns.mean()) / (returns.std() + eps)
    for log_prob, R in zip(policy.saved_log_probs, returns):
        policy_loss.append(-log_prob * R)
    optimizer.zero_grad()
    policy_loss = torch.cat(policy_loss).sum().to(device)
    policy_loss.backward()
    optimizer.step()
    del policy.rewards[:]
    del policy.saved_log_probs[:]
    
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

optimizer = optim.SGD(policy.parameters(), lr=1e-2)
eps = np.finfo(np.float32).eps.item()

random.seed(0)
# train_seeds = random.sample(all_solutions, k=100)
# print('Training game set')
# clf_summary(train_seeds)

training_games = map_seeds_to_states(all_solutions)
          
import datetime
now = datetime.datetime.now()
datestr = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}"
argsstr = f"gamma-{args.gamma}"
PATH = f'./models/mymodel-policy-{datestr}-{argsstr}.torch'

if __name__ == "__main__":
    for i, env in enumerate(training_games):
        seed, klonstate = env
    #     print(seed)
        ep_reward = 0
        done = False
        path = []
        visited = set()
        for t in range(1, 1000):
            action_idx = select_action(klonstate)
            move_code = all_moves[action_idx]
            klonstate, reward = step(klonstate, move_code)
            path.append(move_code)
            if klonstate in visited:
                reward = -1
            else:
                visited.add(klonstate)
            done = reward != 0
            policy.rewards.append(reward)
            ep_reward += reward
            if done:
                break
        final_score = score_state(klonstate)
        print(f"{i:4}  ep reward {ep_reward:.2f}   steps {t:3}   final score {final_score}")#, end=' ')
        if ep_reward > 0:
            print("Solved?!!")
            print(to_pretty_string(klonstate))
    #     print('final score', score_state(klonstate))
    #     print('path', path)
    #     print('final state')
    #     print(to_pretty_string(klonstate))

        finish_episode()
        if i % 200 == 1:
            print('saving...')
            torch.save(policy.state_dict(), PATH)
            print('saved model')
        