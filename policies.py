import re
from tuplestate import *
from timebudget import timebudget


build2suit = re.compile(r"^([1-7])([CDSH])$")
build2build = re.compile(r"^([1-7])([1-7])(-[2-9])?$")
talon2build = re.compile(r"^W([1-7])$")
suit2build = re.compile(r"^([CDSH])([1-7])$")
drawmove = re.compile(r"^DR([1-9][0-9]?)$")


@timebudget
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

        return (0, pri)
