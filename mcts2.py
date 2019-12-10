import math
import random
from decimal import Decimal
from functools import lru_cache
from itertools import count
from collections import defaultdict
from gamestate import (
    KlonState,
    state_is_win,
    play_move,
    get_legal_moves,
    to_pretty_string,
    random_move,
    count_face_up,
)
from policies import yan_et_al
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


CYCLE_REWARD = -10
DEAD_END_REWARD = -20
WIN_REWARD = 100
TIMEOUT_REWARD = -1
NON_TERMINAL = 0


class MCTS:
    def __init__(self):
        self.children = dict()
        self.ancestors = dict()
        self.Q = defaultdict(int)
        self.N = defaultdict(int)
        self.tried_actions = defaultdict(set)
        self._all_nodes = set()

    def search(tree, node, budget=1000):
        # print(f"search node {node}")
        for _ in range(budget):
            leaf = tree.tree_policy(node)
            # print(f"  leaf {leaf}")
            reward = tree.rollout_policy(leaf)
            # print(f"  leaf reward {reward}")
            tree.backup(leaf, reward)
        if tree.is_terminal(node):
            return None
        return tree.uct_best_child(node, exploration=0)

    ### tree policy

    def tree_policy(tree, node):
        while not tree.is_terminal(node):
            if tree.not_fully_expanded(node):
                node = tree.expand(node)
            else:
                node = tree.uct_best_child(node, exploration=10)
        return node

    def not_fully_expanded(tree, node):
        # haven't searched node's children
        if node not in tree.children:
            return True
        # if some actions haven't been tried yet, not fully exp
        untried = tree.node_untried_actions(node)
        return len(untried) > 0

    def is_terminal(tree, node):
        if node.is_win:
            return True
        if node.is_cycle:
            return True
        # node is terminal if we know it has no children
        if node not in tree.children:
            return False  # not terminal, as least as far as we know
        all_tried = len(tree.node_untried_actions(node)) == 0
        children = tree.children[node]
        return len(children) == 0 and all_tried

    def reward(tree, node):
        fnds = [node.foundation1, node.foundation2, node.foundation3, node.foundation4]
        lens = map(len, fnds)
        tabs = [
            node.tableau1,
            node.tableau2,
            node.tableau3,
            node.tableau4,
            node.tableau5,
            node.tableau6,
            node.tableau7,
        ]
        facedown_penalty = 0
        for tab_pile in tabs:
            faceup = count_face_up(tab_pile)
            facedown = len(tab_pile) - faceup
            facedown_penalty += facedown
        # talon_penalty = len(node.stock) + len(node.waste)
        return sum(lens) - facedown_penalty  # - talon_penalty

    def node_untried_actions(tree, node):
        all_actions = node.all_legal_moves
        tried_actions = tree.tried_actions[node]
        untried = all_actions - tried_actions
        return untried

    def expand(tree, node):
        if node not in tree.children:
            tree.children[node] = set()
            tree._all_nodes.add(node)
        while len(tree.node_untried_actions(node)) > 0:
            untried = tree.node_untried_actions(node)
            move = random.choice(list(untried))
            tree.tried_actions[node].add(move)
            child = node.play_move(move)
            if not tree.has_visited_state(child):
                tree.children[node].add(child)
                tree._all_nodes.add(child)
                return child
        return node

    def has_visited_state(tree, state):
        # nodes = set(tree.children.keys())
        # children = {c for cs in tree.children.values() for c in cs}
        # all_nodes = nodes.union(children)
        return state in tree._all_nodes

    ########

    def rollout_policy(tree, node, max_depth=5_000):
        """
        returns: reward
        """
        visited = set()  # states visited during this rollout
        rollout_disabled_moves = set()
        for _ in range(max_depth):
            if tree.is_terminal(node):
                return tree.reward(node)
            visited.add(node)
            # actions = node.all_legal_moves - rollout_disabled_moves
            # a = random.choice(list(actions))
            a = random_move(node)
            # if len(actions) == 0:
            #     return DEAD_END_REWARD
            child = node.play_move(a)
            if child in visited:
                rollout_disabled_moves.add(a)
            else:
                node = child
                rollout_disabled_moves = set()
        return TIMEOUT_REWARD

    def backup(tree, node, reward):
        while node is not None:
            tree.Q[node] += reward
            tree.N[node] += 1
            node = node.parent

    def uct_best_child(tree, node, exploration=0):
        # print(f"   uct_best_child {node} (exp={exploration})")
        if node not in tree.children:
            raise Exception(
                f"called best child for node {node} with unexplored children"
            )
        children = tree.children[node]
        if len(children) == 0:
            raise Exception(f"called best child for node {node} with 0 children")

        def uct(c):
            """ see Algorithm 2: UCT in Browne et al (2012) """
            if tree.N[c] == 0:
                return float("-inf")  # avoid unvisited nodes
            exploit = tree.Q[c] / tree.N[c]
            explore = math.sqrt(2 * math.log(tree.N[node]) / tree.N[c])
            return exploit + exploration * explore

        max_uct = max([uct(c) for c in children])
        max_children = [c for c in children if abs(uct(c) - max_uct) < 0.001]
        # ret = max(children, key=uct)
        ret = random.choice(max_children)
        return ret


class KlonNode(KlonState):
    def __new__(cls, *klonstate, parent=None, action=None):
        self = super(KlonNode, cls).__new__(cls, *klonstate)

        self.parent = parent
        self.action = action

        if parent is not None:
            self.ancestors = parent.ancestors.union(frozenset([parent]))
        else:
            self.ancestors = frozenset()

        self._all_legal_moves = None
        self._is_win = None
        # should probably never happen!
        self.is_cycle = self in self.ancestors
        return self

    @property
    def all_legal_moves(self):
        if self._all_legal_moves is None:
            self._all_legal_moves = get_legal_moves(self)
        return self._all_legal_moves

    @property
    def is_win(self):
        if self._is_win is None:
            self._is_win = state_is_win(self)
        return self._is_win

    def play_move(self, move):
        child = play_move(self, move)
        return KlonNode(*child, parent=self, action=move)

    def __repr__(self):
        return f"K{hash(self)%999999:06}"

    def to_pretty_string(self):
        return to_pretty_string(self)


def children_terminal(node):
    return all(tree.is_terminal(c) for c in tree.children[node])


if __name__ == "__main__":
    # import random
    # from itertools import count
    from benchmarking import random_state
    import sys

    # from mcts2 import KlonNode, MCTS, random_move, get_legal_moves

    # %pdb
    tree = MCTS()
    random.seed(0)
    root_state = random_state()
    root = KlonNode(*root_state)
    node = root
    print(f"ROOT STATE: {node}")
    path = [node]
    # print(node.to_pretty_string())

    for i in count(1):
        print(f"{i:3}: search on {node} (path len {len(path)})")
        if tree.is_terminal(node):
            if node.is_win:
                print("WIN!")
                print(node)
                print(node.to_pretty_string())
                sys.exit(0)

            print(f"{node} is TERMINAL")
            print(node.to_pretty_string())
            child = path.pop()  # equal to `node`
            while tree.is_terminal(child):
                parent = path.pop()
                if child in tree.children[parent]:
                    tree.children[parent].remove(child)
                child = parent
            path = []
            node = root
            # node = child
        else:
            node = tree.search(node)
            if node in path:
                print(f"CYCLE {node} in visited")
            path.append(node)

    print(node)
    print(node.to_pretty_string())
