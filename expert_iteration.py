import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.autograd import Variable
from torch.distributions import Categorical
from collections import defaultdict
import itertools
from itertools import islice
import datetime
import json
from klon_tree import KlonTree
from benchmarking import *
from vectorize import *
from policies import EndState


device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print("device", device)

LR = 1e-3
MAX_STEPS = 1000

IN = 233 * 104
OUT = 623

now = datetime.datetime.now()
datestr = f"{now.year}{now.month}{now.day}{now.hour}{now.minute}"
argsstr = f"lr-{LR:.2g}"
versionstr = f"exitapprentice-{datestr}-{argsstr}-nodropout"
MODEL_PATH = f"./models/{versionstr}.torch"
RESULT_PATH = f"./results/{versionstr}.json"


# bootstrap an apprentice
class Apprentice(nn.Module):
    def __init__(self):
        super(Apprentice, self).__init__()
        self.linear1 = nn.Linear(IN, 233 * 20)
        self.linear2 = nn.Linear(233 * 20, 233 * 10)
        self.dropout = nn.Dropout(p=0.6)
        self.linear3 = nn.Linear(233 * 10, 1500)
        self.dropout2 = nn.Dropout(p=0.6)
        self.linear4 = nn.Linear(1500, OUT)
        self.saved_log_probs = []
        self.rewards = []

    def forward(self, x):
        x = F.relu(self.linear1(x))
        x = self.dropout(x)
        x = F.relu(self.linear2(x))
        x = F.relu(self.linear3(x))
        x = self.dropout2(x)
        action_scores = self.linear4(x)
        return F.softmax(action_scores, dim=1)


apprentice = Apprentice()
apprentice.to(device)
optimizer = optim.Adam(apprentice.parameters(), lr=LR)
eps = np.finfo(np.float32).eps.item()

# apprentice.load_state_dict(
#     torch.load("./models/201912161346-gamma-0.5-lr-0.001-nodropout.torch")
# )
# apprentice.eval()


def apprentice_select_action(klonstate, legal_moves):
    """
    :returns:
        move code idx
        selected move log prob
        prob distribution {tensor: (1,OUT)}
    """
    state_vec = state_to_vec(klonstate)
    movefilter = vectorize_legal_moves(legal_moves)
    tstatevec = torch.from_numpy(state_vec).float().reshape(-1).unsqueeze(0).to(device)
    tfilter = torch.from_numpy(movefilter.astype(np.float32)).unsqueeze(0).to(device)
    probs = apprentice(tstatevec) * tfilter
    if (probs == 0).all():
        tfilter.requires_grad_()
        # sample all legal moves with uniform probability
        m = Categorical(tfilter)
    else:
        # :attr:`probs` will be normalized to sum to 1
        m = Categorical(probs)
    action = m.sample()
    log_prob = m.log_prob(action)
    try:
        move_code_idx = action.item()
    except RuntimeError:
        import pdb

        pdb.set_trace()
    return move_code_idx, log_prob, m.probs


def simulate_with_apprentice(state, max_steps=1_000):
    """
    :returns: {EndState}
    """
    tree = KlonTree(state)
    for step in range(max_steps):
        legal_moves = tree.legal_moves()
        if tree.is_win():
            return EndState(
                solved=True,
                msg=f"found win after {step} steps",
                visited=len(tree.visited),
                moveseq=tree.path,
            )
        if len(legal_moves) == 0:
            return EndState(
                solved=False, msg="no legal moves remaining", visited=len(tree.visited)
            )
        with torch.no_grad():
            move_idx, lp, ps = apprentice_select_action(tree.state, legal_moves)
            move = all_moves[move_idx]
            tree.make_move(move)
    return EndState(solved=False, msg="exceeded max steps", visited=step)


# expert apprentice does k-step lookahead using apprentice for rollouts
def select_expert_move(state, k=2):
    """
    :returns: ( move_idx, {EndState} )
    """
    tree = KlonTree(state)
    legal_moves = tree.legal_moves()
    if len(legal_moves) == 0:
        return EndState(solved=False, msg="no legal moves remaining")
    # one-step lookahead
    for move in legal_moves:
        child_state = play_move(state, move)
        result = simulate_with_apprentice(child_state)
        if hasattr(result, "solved") and result.solved:
            endstate = EndState(
                solved=True,
                msg="solved in rollout",
                visited=result.visited,
                moveseq=(move,) + tuple(result.moveseq),
            )
            move_idx = np.argmax(vectorize_legal_moves(set([move])))
            return (move_idx, endstate)
    # no optimal move: use apprentice to choose an action
    with torch.no_grad():
        move_idx, lp, probs = apprentice_select_action(state, legal_moves)
    return move_idx, None


def generate_self_play_samples(klonstate, max_steps=1_000, states=1):
    # for i, env in enumerate(training_games):
    states_for_game = []
    tree = KlonTree(klonstate)
    for step in range(max_steps):
        legal_moves = tree.legal_moves()
        if len(legal_moves) == 0:
            break
        move_idx, _, probs = apprentice_select_action(tree.state, legal_moves)
        states_for_game.append((tree.state, probs))
        move_code = all_moves[move_idx]
        tree.make_move(move_code)
    # apprentice_states +=
    return random.sample(states_for_game, states)
    # # yes seems wasteful but not sure how to get independent samples otherwise
    # print(f"returning {len(apprentice_states)} (state, action tensor) pairs")
    # return apprentice_states


def generate_expert_moves_dataset(apprentice_states):
    for i, (state, app_probs) in enumerate(apprentice_states):
        exp_move, result = select_expert_move(state)
        emstr = f"exp move {exp_move}"
        resultstr = "<none>"
        if result is not None:
            if result.solved:
                resultstr = f"solved! {len(result.moveseq)}"
            else:
                resultstr = f"not solved {result.msg}"
        print(f"  expert moves data: {i:3} {emstr} {resultstr}")
        yield state, app_probs, exp_move, result


def chunks(iterator, n):
    # https://dev.to/orenovadia/solution-chunked-iterator-python-riddle-3ple
    for first in iterator:  # take one item out (exits loop if `iterator` is empty)
        rest_of_chunk = itertools.islice(iterator, 0, n - 1)
        yield itertools.chain([first], rest_of_chunk)


def train_apprentice(training_games, batch_size=5, states=1):
    """
    training_games: used as initial states for the apprentice self-play
        - as the apprentice plays, we collect (state, action tensor) pairs
        - action tensor is the probs output by the apprentice network
        - we use the action tensor for gradients
    batch_size: we extract [...(state, action tensor)] for this many games
    states: only keep this many states out of all the (state, action tensor) pairs
        - Anthony et al: keep the dataset uncorrelated. Should only be 1 actually
    """
    # gen_apprentice_states = generate_self_play_samples(training_games, states=states)
    results = {}
    for ep_i in itertools.count(1):
        print(f"episode {ep_i:3}")
        apprentice.train()

        # optimizer
        optimizer.zero_grad()

        # collect expert moves data from self-play
        app_probs = []
        exp_preds = []
        exp_results = []
        while len(app_probs) < batch_size:
            # collect only successful rollouts until we get desired batch size
            seed, klonstate = next(training_games)
            print(
                f"current: {len(app_probs)}/{batch_size}, tried {len(exp_results)}, seed: {seed}"
            )
            print(f" generating self play samples from seed {seed}")
            apprentice_states = generate_self_play_samples(klonstate)
            expert_moves = generate_expert_moves_dataset(apprentice_states)
            for i, dta in enumerate(expert_moves):
                state, apprentice_probs, exp_move, exp_result = dta
                print(f"  {i:3}, exp:{exp_move}, result:{str(exp_result)}")
                if exp_result and exp_result.solved:
                    app_probs.append(apprentice_probs)
                    exp_preds.append(exp_move)
                exp_results.append(exp_result)
        failed_attempts = exp_results.count(None)
        attempts = len(exp_results)
        print(f"got {attempts - failed_attempts} out of {attempts}")
        ap = torch.cat(app_probs)
        ep = torch.Tensor(exp_preds).to(device, dtype=torch.long)
        print("app probs", ap.shape, "exp probs", ep.shape)

        loss = nn.CrossEntropyLoss()
        output = loss(ap, ep)

        # update!
        output.backward()
        optimizer.step()
        print("step!")

        ### results
        results[ep_i] = {
            "exp_preds": list(map(int, exp_preds)),
            "num_searches": len(app_probs),
            "batch": attempts,
            "total_tried": failed_attempts,
        }

        print("saving outputs")
        if i % 2 == 0 and i > 1:
            print(f"saving... {MODEL_PATH}")
            torch.save(policy.state_dict(), MODEL_PATH)
            print("saved model")
        with open(RESULT_PATH, "w") as f:
            json.dump(results, f)


train_apprentice(get_training_games(), batch_size=10)
