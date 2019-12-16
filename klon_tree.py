from gamestate import *


class KlonTree:
    def __init__(self, root_state):
        self.root_state = root_state
        self.state = root_state
        self.visited = set([self.state])
        self.path = []

    def print_root(self):
        print(to_pretty_string(self.root_state))

    def print_state(self):
        print(to_pretty_string(self.state))

    def legal_moves(self):
        """
        Returns only legal moves which would *not* yield a previously visited state
        """
        all_moves = get_legal_moves(self.state)
        children = ((play_move(self.state, move), move) for move in all_moves)
        filtered_moves = set()
        for s, a in children:
            if s not in self.visited:
                filtered_moves.add(a)
        return filtered_moves

    def make_move(self, move_code):
        new_state = play_move(self.state, move_code)
        self.state = new_state
        self.visited.add(new_state)
        self.path.append(move_code)

    def is_win(self):
        return all_cards_faceup(self.state)
