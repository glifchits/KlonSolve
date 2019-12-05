import re
from gamestate import get_legal_moves, count_face_up, play_move, state_is_win


class EndState:
    def __init__(self, **kwargs):
        self.solved = kwargs.get("solved", None)
        self.moveseq = kwargs.get("moveseq", None)
        self.visited = kwargs.get("visited", None)
        self.msg = kwargs.get("msg", None)
        self.impossible = kwargs.get("impossible", None)


build2suit = re.compile(r"^([1-7])([CDSH])$")
build2build = re.compile(r"^([1-7])([1-7])(-[2-9])?$")
talon2build = re.compile(r"^W([1-7])$")
suit2build = re.compile(r"^([CDSH])([1-7])$")
drawmove = re.compile(r"^DR([1-9][0-9]?)$")

VALUE, SUIT = 0, 1
STOCK = 0
TABLEAU1 = 1
TABLEAU2 = 2
TABLEAU3 = 3
TABLEAU4 = 4
TABLEAU5 = 5
TABLEAU6 = 6
TABLEAU7 = 7
WASTE = 8
FOUNDATION_C = 9
FOUNDATION_D = 10
FOUNDATION_S = 11
FOUNDATION_H = 12


def irange(lo, hi):
    return range(lo, hi + 1)


def yan_et_al(move_code, state):
    """
    returns a tuple: (reward, priority)
        sorting a sequence of these tuples will sort by reward
        and then priority (to break ties)
    """
    # Yan et al (2005)
    # - moved from a build stack to a suit stack, gain 5 points
    # - moved from the talon to a build stack, gain 5 points
    # - moved from a suit stack to a build stack, lose 10 points
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
        # draw moves
        # penalize the ones that Yan et al wouldn't consider
        if move_code.startswith("DR") and move_code != "DR1":
            pri = -1

        return (0, pri)


def yan_et_al_prioritized_actions(state):
    # produce the set of legal moves given this state
    move_list = get_legal_moves(state)

    # policy: function(move_code)
    # - given a move code and the state, score the move.
    # - taken over a set of moves, should order the moves by their desirability
    policy = lambda mc: (yan_et_al(mc, state), mc)

    return sorted(move_list, key=policy, reverse=True)


def simulate_with_heuristic(state, max_states=50_000):
    visited = set()
    moveseq = []
    i = 0
    while True:
        v = len(visited)
        if i >= max_states:
            return EndState(solved=False, visited=v, msg="exceeded max states")
        if state in visited:
            return EndState(solved=False, msg="revisited state", visited=v)
        visited.add(state)
        # Yan et al. Section 4 "Machine Play"
        # 1. identify set of legal moves
        # 2. select and execute a legal move
        actions = yan_et_al_prioritized_actions(state)
        if len(actions) == 0:
            return EndState(solved=False, visited=v, msg="run out of actions")
        action = actions[0]
        moveseq.append(action)
        state = play_move(state, action)
        # 3. If all cards are on suit stacks, declare victory and terminate.
        if state_is_win(state):
            return EndState(solved=True, moveseq=moveseq, visited=v)
        # 4. If new card configuration repeats a previous one, declare loss and terminate.
        # 5. Repeat procedure.
        i += 1


def yan_et_al_rollout_1(state):
    moves = get_legal_moves(state)
    for move in moves:
        new_state = play_move(state, move)
        result = simulate_with_heuristic(new_state)
        if result.solved:
            return EndState(
                solved=True,
                msg="solved in rollout",
                visited=result.visited,
                moveseq=(move,) + tuple(result.moveseq),
            )
    # no optimal move: use the strategy as before
    actions = yan_et_al_prioritized_actions(state)
    if len(actions) == 0:
        return None
    return actions[0]


def yan_et_al_rollout(state, k):
    moves = get_legal_moves(state)
    for move in moves:
        new_state = play_move(state, move)
        if k > 1:
            result = yan_et_al_rollout(new_state, k - 1)
        elif k == 1:
            result = simulate_with_heuristic(new_state)
        if hasattr(result, "solved") and result.solved:
            return EndState(
                solved=True,
                msg="solved in rollout",
                visited=result.visited,
                moveseq=(move,) + tuple(result.moveseq),
            )
    # no optimal move: use the strategy as before
    actions = yan_et_al_prioritized_actions(state)
    if len(actions) == 0:
        return None
    return actions[0]
