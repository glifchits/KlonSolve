"""
A minimal implementation of Monte Carlo tree search (MCTS) in Python 3
Luke Harold Miles, July 2019, Public Domain Dedication
See also https://en.wikipedia.org/wiki/Monte_Carlo_tree_search
https://gist.github.com/qpwo/c538c6f73727e254fdc7fab81024f6e1
"""
from abc import ABC, abstractmethod
from collections import defaultdict
import math
import random
from decimal import *
from gamestate import (
    KlonState,
    get_legal_moves,
    play_move,
    state_is_win,
    to_pretty_string,
)
from policies import yan_et_al_prioritized_actions


class MCTS:
    "Monte Carlo tree searcher. First rollout the tree then choose a move."

    def __init__(self, exploration_weight=1):
        self.Q = defaultdict(int)  # total reward of each node
        self.N = defaultdict(int)  # total visit count for each node
        self.children = dict()  # children of each node
        self.exploration_weight = exploration_weight
        self.existing_children = set()

    def choose(self, node):
        "Choose the best successor of node. (Choose a move in the game)"
        if node.is_terminal():
            raise RuntimeError(f"choose called on terminal node {node}")

        if node not in self.children:
            print("rollout policy child")
            return node.rollout_policy_child()

        choose_children = set(self.children[node]) - node.ancestor_set

        def score(n):
            if self.N[n] == 0:
                return float("-inf")  # avoid unseen moves
            return self.Q[n] / self.N[n]  # average reward

        max_score = max(map(score, choose_children))
        max_children = [c for c in choose_children if score(c) == max_score]
        return random.choice(max_children)
        # return max(choose_children, key=score)

    def do_rollout(self, node):
        "Make the tree one layer better. (Train for one iteration.)"
        path = self._select(node)
        leaf = path[-1]
        self._expand(leaf)
        reward = self._simulate(leaf)
        self._backpropagate(path, reward)

    def _select(self, node):
        "Find an unexplored descendent of `node`"
        path = []
        while True:
            if node in path:
                raise ValueError("detected cycle")
            path.append(node)
            if node not in self.children or not self.children[node]:
                # node is either unexplored or terminal
                return path
            unexplored = self.children[node] - self.children.keys()
            if unexplored:
                n = unexplored.pop()
                path.append(n)
                return path
            # node = self._uct_select(node)  # descend a layer deeper
            # def _uct_select(node):
            #     "Select a child of node, balancing exploration & exploitation"
            select_nodes = self.children[node] - set(path)  # dont pick from explored
            if len(select_nodes) == 0:
                # node is terminal
                return path

            # All children should already be expanded:
            assert all(n in self.children for n in select_nodes)

            log_N_vertex = math.log(self.N[node])

            def uct(n):
                "Upper confidence bound for trees"
                exploit = self.Q[n] / self.N[n]
                explore = Decimal(math.sqrt(log_N_vertex / self.N[n]))
                return exploit + self.exploration_weight * explore

            node = max(select_nodes, key=uct)

    def _expand(self, node):
        "Update the `children` dict with the children of `node`"
        if node in self.children:
            return  # already expanded
        children = set()
        for child in node.find_children():
            # only add as a child if it is not child of other nodes
            # if child not in self.existing_children:
            children.add(child)
            self.existing_children.add(child)
        self.children[node] = children

    def _simulate(self, node):
        "Returns the reward for a random simulation (to completion) of `node`"
        max_states = 1_000
        visited = set([node])
        for _ in range(max_states):
            if node.is_terminal():
                reward = node.reward()
                return reward
            if node in visited:  # cycle
                return -1
            node = node.rollout_policy_child()
            visited.add(node)
        return Decimal("-0.1")  # reward for bailed out at state limit

    def _backpropagate(self, path, reward):
        "Send the reward back up to the ancestors of the leaf"
        for node in reversed(path):
            self.N[node] += 1
            self.Q[node] += Decimal(reward)


class KlondikeNode(KlonState):
    def __new__(cls, *klonstate, parent=None):
        self = super(KlondikeNode, cls).__new__(cls, *klonstate)
        self.parent = parent
        self._cached_legal_moves = None
        if parent is None:  # no parents => no ancestors
            self.ancestor_set = frozenset()
        else:  # my ancestors are my parent's ancestors and my parent
            self.ancestor_set = parent.ancestor_set.union(frozenset([parent]))
        return self

    @property
    def ancestors(self):
        anc = []
        node = self
        while node.parent is not None:
            anc.append(node.parent)
            node = node.parent
        return anc

    def make_move(state, move):
        new_state = play_move(state, move)
        return KlondikeNode(*new_state, parent=state)

    def find_children(state):
        if state._cached_legal_moves is None:
            moves = get_legal_moves(state)
            children = set()
            for move in moves:
                child_state = state.make_move(move)
                if not child_state in state.ancestor_set:
                    children.add(child_state)
            state._cached_legal_moves = children
        return state._cached_legal_moves

    def find_random_child(state):
        if state.is_terminal():
            return None
        children = state.find_children()
        child_list = list(children)
        if len(child_list) == 0:
            import pdb

            pdb.set_trace()
        random_child = random.choice(child_list)
        return random_child

    def rollout_policy_child(state):
        # return state.find_random_child()
        moves = yan_et_al_prioritized_actions(state)
        best_move = moves[0]
        return state.make_move(best_move)

    def is_win(state):
        return state_is_win(state)

    def is_childless(state):
        child_states = state.find_children()
        if len(child_states) == 0:
            return True
        return False

    def is_terminal(state):
        return state.is_win() or state.is_childless()

    def reward(state):
        if state.is_win():
            return 1
        elif state.is_childless():
            return -1
        return 0

    def to_pretty_string(state):
        return to_pretty_string(state)

    def to_vec(state):
        return state_to_vec(state)

    def __repr__(state):
        i = hash(state) % 99999
        return f"K{i}"
