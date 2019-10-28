from timebudget import timebudget
from tuplestate import *


@timebudget
def get_draw_moves(state):
    st = copy(state)
    draw_moves = set()
    top_cards = set()
    if len(st[WASTE]) > 0:
        top_cards.add(st[WASTE][-3:])  # current waste is available
    for draw_count in range(200):  # should be way more than enough
        if len(st[STOCK]) == 0:
            st = replace_stock(st)
        st = draw(st)
        new_move = f"DR{draw_count+1}"
        top_waste = st[WASTE][-3:]
        if top_waste in top_cards:
            return draw_moves
        top_cards.add(top_waste)
        draw_moves.add(new_move)
    return draw_moves


@timebudget
def get_legal_moves(state):
    """ returns a set of legal moves given the state """
    moves = set()
    TABLEAUS = irange(TABLEAU1, TABLEAU7)
    FACEUP = {}
    for tab in TABLEAUS:
        pile = state[tab]
        fu = count_face_up(pile)
        FACEUP[tab] = pile[-fu:]
    # tab to tab
    for src in TABLEAUS:
        for dest in TABLEAUS:
            if src == dest:
                continue
            for i, src_card in enumerate(reversed(FACEUP[src])):
                move = f"{src}{dest}"
                if i > 0:
                    move += f"-{i+1}"
                if len(state[dest]) == 0:  # tableau empty
                    if src_card[VALUE] == "K":
                        moves.add(move)
                elif can_stack(src_card, state[dest][-1]):
                    moves.add(move)
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
                    ord = (src_top[VALUE], fnd_top[VALUE])
                    if ord in VALUE_ORDER:
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
                order = (fnd_top[VALUE], waste_top[VALUE])
                if order in VALUE_ORDER:
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
