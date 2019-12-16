import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable
from torch.distributions import Categorical

from collections import defaultdict
import datetime
import json

from klon_tree import KlonTree
from benchmarking import *
from vectorize import *

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print("device", device)

GAMMA = 0.5
LR = 1e-2
MAX_STEPS = 1000

IN = 233 * 104
OUT = 623

now = datetime.datetime.now()
datestr = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}"
argsstr = f"gamma-{GAMMA}-lr-{LR:.2g}"
versionstr = f"{datestr}-{argsstr}-nodropout"
MODEL_PATH = f"./models/{versionstr}.torch"
RESULT_PATH = f"./results/{versionstr}.json"


class Policy(nn.Module):
    def __init__(self):
        super(Policy, self).__init__()
        self.linear1 = nn.Linear(IN, 233 * 20)
        self.linear2 = nn.Linear(233 * 20, 233 * 8)
        self.dropout = nn.Dropout(p=0.6)
        self.linear3 = nn.Linear(233 * 8, 1500)
        self.linear4 = nn.Linear(1500, OUT)
        self.saved_log_probs = []
        self.rewards = []

    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = F.relu(self.linear2(x))
        x = self.dropout(x)
        x = F.relu(self.linear3(x))
        action_scores = self.linear4(x)
        return F.softmax(action_scores, dim=1)


policy = Policy()
policy.to(device)

optimizer = optim.SGD(policy.parameters(), lr=LR)
eps = np.finfo(np.float32).eps.item()


def select_action(klonstate, legal_moves):
    state_vec = state_to_vec(klonstate)
    movefilter = vectorize_legal_moves(legal_moves)
    torch_state_vec = (
        torch.from_numpy(state_vec).float().reshape(-1).unsqueeze(0).to(device)
    )
    torch_filter = (
        torch.from_numpy(movefilter.astype(np.float32)).unsqueeze(0).to(device)
    )
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
    move_code_idx = action.item()
    move_code = all_moves[move_code_idx]
    return move_code


def finish_episode():
    R = 0
    policy_loss = []
    returns = []
    for r in policy.rewards[::-1]:
        R = r + GAMMA * R
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


def play_game(klonstate):
    tree = KlonTree(klonstate)

    for step in range(MAX_STEPS):
        klonstate = tree.state
        legal_moves = tree.legal_moves()
        reward = 0
        if len(legal_moves) == 0:
            reward = -1
        else:
            move_code = select_action(klonstate, legal_moves)
            tree.make_move(move_code)
        if step <= 52:  # obviously won't be done yet
            reward = 0
        elif tree.is_win():
            reward = 1

        policy.rewards.append(reward)

        if reward != 0:
            break

    finish_episode()
    return (reward, step, tree)


rewards = []
wins = {}


def write_results():
    with open(RESULT_PATH, "w") as f:
        json.dump({"net": str(policy), "rewards": rewards, "wins": wins}, f)


try:
    for i, env in enumerate(training_games):
        seed, klonstate = env
        ret = play_game(klonstate)
        reward, steps, tree = ret
        rewards.append(reward)
        if i % 10 == 0 and i > 0:
            last_10 = np.average(rewards[-10:])
            last_100 = np.average(rewards[-100:])
            print(f"rewards {i:4} ::: avg10: {last_10:.2f}, avg100: {last_100:.2f}")
        if reward > 0:
            print(f"got a win!! {seed}")
            wins[seed] = tree.path
        if i % 200 == 1 and i > 10:
            print(f"saving... {MODEL_PATH}")
            torch.save(policy.state_dict(), MODEL_PATH)
            print("saved model")
            write_results()
finally:
    write_results()
