import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable
from torch.distributions import Categorical

from tuplestate import *
from gamestate import *
from benchmarking import *
from vectorize import *


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print('cuda?', device)


IN = 233*104
OUT = 623


class Policy(nn.Module):
    def __init__(self):
        super(Policy, self).__init__()
        self.inlayer = nn.Linear(IN, 233*10)
        self.linear1 = nn.Linear(233*10, 1000)
        self.outlayer = nn.Linear(1000, OUT)
        self.dropout = nn.Dropout(p=0.6)
        self.saved_log_probs = []
        self.rewards = []
        self.version = 1

    def forward(self, x):
        x = self.inlayer(x)
        x = F.relu(x)
        x = self.dropout(x)
        x = self.linear1(x)
        x = F.relu(x)
        action_scores = self.outlayer(x)
        return F.softmax(action_scores, dim=1)
    
    def __str__(self):
        return f"PolicyNetwork {self.version}"


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