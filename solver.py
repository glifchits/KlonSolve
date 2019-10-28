import re
import sys
from tuplestate import *
from get_legal_moves import get_legal_moves
from timebudget import timebudget

timebudget.report_atexit()


sys.setrecursionlimit(10 ** 6)


def add(my_frozenset, new_value):
    return my_frozenset.union(set([new_value]))


def visit_state(visit_set, state):
    return add(visit_set, hash(state))


def was_visited(state, visited):
    return hash(state) in visited


def append(tup, val):
    return tup + (val,)


build2suit = re.compile(r"^([1-7])([CDSH])$")
build2build = re.compile(r"^([1-7])([1-7])(-[2-9])?$")
talon2build = re.compile(r"^W([1-7])$")
suit2build = re.compile(r"^([CDSH])([1-7])$")
drawmove = re.compile(r"^DR([1-9][0-9]?)$")


@timebudget
def prioritize(move_list, state):
    """re-order the given move list by how
    promising the moves are, descending """
    # Yan et al (2005)
    # - moved from a build stack to a suit stack, gain 5 points
    # - moved from the talon to a build stack, gain 5 points
    # - moved from a suit stack to a build stack, lose 10 points
    def score_move(move_code):
        pri = 0  # default case for priority
        if build2suit.match(move_code):
            return (5, 0)
        elif talon2build.match(move_code):
            # If the card move is from the talon to a build stack, one of the
            # following three assignments of priority occurs:
            card = state.waste[-1]
            # – If the card being moved is not a King,
            #   we assign the move priority 1.
            if card[VALUE] != "K":
                pri = 1
            else:  # card is a King
                # – If the card being moved is a King and its matching Queen is in
                #   the pile, in the talon, in a suit stack, or is face-up in a
                #   build stack, we assign the move priority 1.
                matching_queen = f"Q{card[SUIT]}"
                if matching_queen in state.stock:  # queen is in the pile
                    pri = 1
                elif matching_queen in state.waste:  # queen in the talon
                    pri = 1
                else:
                    tabs = irange(TABLEAU1, TABLEAU7)
                    q_fup_in_tab = (matching_queen in state[t] for t in tabs)
                    if any(q_fup_in_tab):  # queen is faceup in a build stack
                        pri = 1
                    # – If the card being moved is a King and its matching Queen is
                    #   face-down in a build stack, we assign the move priority -1.
                    else:
                        tabs = irange(TABLEAU1, TABLEAU7)
                        mq_fdown = matching_queen.lower()
                        q_fdown_in_tab = (mq_fdown in state[t] for t in tabs)
                        if any(q_fdown_in_tab):  # queen facedown in a build stack
                            pri = -1

            return (5, pri)
        elif suit2build.match(move_code):
            return (-10, pri)
        elif drawmove.match(move_code):
            # my own rule, not in Yan et al
            return (-1, pri)
        else:
            # If the card move is from a build stack to another build stack,
            # one of the following two assignments of priority occurs:
            b2b_match = build2build.match(move_code)
            if b2b_match:
                src, dest, num = b2b_match.groups()
                src = int(src)
                num = 1 if num is None else int(num[1:])
                faceup = count_face_up(state[src])
                facedown = len(state[src]) - faceup
                # – If the move turns an originally face-down card face-up,
                #   we assign this move a priority of k + 1, where k is the
                #   number of originally face-down cards on the source
                #   stack before the move takes place.
                if num == faceup and facedown > 0:  # will reveal a facedown card
                    pri = facedown + 1
                # – If the move empties a stack, we assign this move a priority of 1.
                elif num == len(state[src]):  # moving all cards on stack
                    pri = 1

            return (0, pri)

    return sorted(move_list, key=score_move, reverse=True)


visited = set()


def gameplay(state, move_seq):
    if was_visited(state, visited):
        return False
    if state_is_win(state):
        return True
    visited.add(hash(state))
    moves = get_legal_moves(state)

    for move_code in prioritize(moves, state):
        new_state = play_move(state, move_code)
        is_a_win_state = gameplay(state=new_state, move_seq=append(move_seq, move_code))
        if is_a_win_state:
            print("WIN!!!!")
            pprint_st(new_state)
            return new_state


if __name__ == "__main__":
    print("running solver")
    game = {
        "foundation": [[], [], [], []],
        "waste": [],
        "stock": [
            "kc",
            "9c",
            "qc",
            "8c",
            "3c",
            "7s",
            "7h",
            "10c",
            "4c",
            "7d",
            "ks",
            "ad",
            "qs",
            "kh",
            "qd",
            "10h",
            "8s",
            "ah",
            "6h",
            "4h",
            "as",
            "2d",
            "10d",
            "3h",
        ],
        "tableau": [
            ["8H"],
            ["3d", "6C"],
            ["5s", "jd", "JS"],
            ["2h", "kd", "7c", "9S"],
            ["qh", "8d", "jc", "2c", "AC"],
            ["4s", "6s", "2s", "3s", "9d", "5C"],
            ["5h", "6d", "5d", "4d", "10s", "9h", "JH"],
        ],
    }
    gameplay(state=init_from_ui_state(game), move_seq=())
