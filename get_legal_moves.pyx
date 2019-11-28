cimport cython
from timebudget import timebudget
from tuplestate import TABLEAUS, FNDS, FND_SUITS, WASTE, STOCK
from tuplestate import count_face_up, replace_stock, draw, copy


cdef RED = "DH"
cdef BLACK = "CS"
cdef VALUE = 0  # could remove these and just import from tuplestate
cdef SUIT = 1   # could remove these and just import from tuplestate


cdef int can_stack(str card, str onto):
    """ `card` is the card to move, `onto` is the card to stack onto """
    cdef cs = card[SUIT]
    cdef os = onto[SUIT]
    if (cs == 'D' or cs == 'H') and (os == 'D' or os == 'H'):
        return 0
    if (cs == 'C' or cs == 'S') and (os == 'C' or os == 'S'):
        return 0
    cdef cv = card[VALUE]
    cdef ov = onto[VALUE]
    return in_value_order(cv, ov)


cdef int in_value_order(str cv, str ov):
    return 1 if (
      (cv == "A" and ov == "2") or
      (cv == "2" and ov == "3") or
      (cv == "3" and ov == "4") or
      (cv == "4" and ov == "5") or
      (cv == "5" and ov == "6") or
      (cv == "6" and ov == "7") or
      (cv == "7" and ov == "8") or
      (cv == "8" and ov == "9") or
      (cv == "9" and ov == "T") or
      (cv == "T" and ov == "J") or
      (cv == "J" and ov == "Q") or
      (cv == "Q" and ov == "K")
    ) else 0


@timebudget
def get_draw_moves(state):
    if len(state.stock) == 0 and len(state.waste) == 0:
        return set()
    st = copy(state)
    draw_moves = set()
    seen_top_cards = set()
    if len(st[WASTE]) > 0:
        seen_top_cards.add(st[WASTE][-3:])  # current waste is available
    for draw_count in range(100):  # should be way more than enough
        if len(st[STOCK]) == 0:
            st = replace_stock(st)
        st = draw(st)
        new_move = f"DR{draw_count+1}"
        top_waste = st[WASTE][-3:]
        if top_waste in seen_top_cards: # cycled through
            return draw_moves
        seen_top_cards.add(top_waste)
        draw_moves.add(new_move)
    return draw_moves


@cython.boundscheck(False)
# @cython.wraparound(False) # causes segfaults
@timebudget
def tableau_to_tableau(state):
    # TABLEAU1 = 1 and TABLEAU7 = 7
    # range(1, 8) is all tableau indices
    FACEUP = {}
    moves = set()
    for tab in range(1, 8):
        pile = state[tab]
        fu = count_face_up(pile)
        FACEUP[tab] = pile[-fu:]
    for src in range(1, 8):
        for dest in range(1, 8):
            if src == dest:
                continue
            num_to_move = 1
            faceup = FACEUP[src]
            idx = len(faceup) - 1
            while idx >= 0:
                state_dest = state[dest]
                src_card = faceup[idx]
                if len(state_dest) == 0:  # tableau empty
                    # only move a king to empty tableau if not the entire stack
                    # this would be a useless move
                    if src_card[VALUE] == "K" and len(state[src]) > num_to_move:
                        move = f"{src}{dest}"
                        if num_to_move > 1:
                            move += f"-{num_to_move}"
                        moves.add(move)
                elif can_stack(src_card, state_dest[-1]):
                    move = f"{src}{dest}"
                    if num_to_move > 1:
                        move += f"-{num_to_move}"
                    moves.add(move)
                num_to_move += 1
                idx -= 1
    return moves


@timebudget
def get_legal_moves(state):
    """ returns a set of legal moves given the state """
    moves = set()
    # tab to tab
    moves = moves.union(tableau_to_tableau(state))
    # tab to foundation
    for src in TABLEAUS:
        if len(state[src]) == 0:
            continue  # can't move empty to foundation
        src_top = state[src][-1]
        for fnd, fnd_suit in zip(FNDS, FND_SUITS):
            move = f"{src}{fnd_suit}"
            if len(state[fnd]) == 0:
                if src_top[VALUE] == "A" and src_top[SUIT] == fnd_suit:
                    moves.add(move)
            else:
                fnd_top = state[fnd][-1]
                if src_top[SUIT] == fnd_top[SUIT]:
                    # ord = (fnd_top[VALUE], src_top[VALUE])
                    cv = fnd_top[VALUE]
                    ov = src_top[VALUE]
                    # if ord in VALUE_ORDER:
                    if in_value_order(cv, ov):
                        moves.add(move)
    # waste to tableau
    if len(state.waste) > 0:
        waste_top = state.waste[-1]
        for dest in TABLEAUS:
            move = f"W{dest}"
            if len(state[dest]) == 0:
                # empty tableau, can move a king
                if waste_top[VALUE] == "K":
                    moves.add(move)
            else:
                # non-empty tableau pile, can stack normally
                dest_top = state[dest][-1]
                if can_stack(waste_top, dest_top):
                    moves.add(move)
    # waste to foundation
    if len(state.waste) > 0:
        waste_top = state.waste[-1]
        for fnd, fnd_suit in zip(FNDS, FND_SUITS):
            if waste_top[SUIT] != fnd_suit:
                continue  # only bother looking at the correct foundation
            move = f"W{fnd_suit}"
            if len(state[fnd]) == 0:
                if waste_top[VALUE] == "A":
                    moves.add(move)
            else:
                fnd_top = state[fnd][-1]
                # order = (fnd_top[VALUE], waste_top[VALUE])
                # if order in VALUE_ORDER:
                if in_value_order(fnd_top[VALUE], waste_top[VALUE]):
                    moves.add(move)
    # foundation to tableau
    for fnd, fnd_suit in zip(FNDS, FND_SUITS):
        if len(state[fnd]) == 0:
            continue  # can't move any cards from an empty foundation
        fnd_top = state[fnd][-1]
        for tab in TABLEAUS:
            if len(state[tab]) == 0:
                continue  # not gonna move a king onto empty tableau
            tab_top = state[tab][-1]
            if can_stack(fnd_top, tab_top):
                move = f"{fnd_suit}{tab}"
                moves.add(move)
    # draw moves
    moves = moves.union(get_draw_moves(state))
    return moves
