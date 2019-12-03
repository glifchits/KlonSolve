import numpy as np
from pprint import pprint
from gamestate import KlonState


def init_from_ui_state(game_dict):
    def card(c):
        """ fixes up card definitions for UI format compat """
        if c.startswith("10"):
            t = "t" if c[-1] in "cdsh" else "T"
            return c.replace("10", t)
        return c

    def mapcards(it):
        return tuple(map(card, it))

    foundation = tuple(mapcards(f) for f in game_dict["foundation"])
    stock = tuple(card(c).upper() for c in game_dict["stock"])
    waste = tuple(mapcards(game_dict["waste"]))
    tableau = [mapcards(t) for t in game_dict["tableau"]]
    return KlonState(
        stock=stock,
        waste=waste,
        tableau1=tableau[0],
        tableau2=tableau[1],
        tableau3=tableau[2],
        tableau4=tableau[3],
        tableau5=tableau[4],
        tableau6=tableau[5],
        tableau7=tableau[6],
        foundation1=foundation[0],
        foundation2=foundation[1],
        foundation3=foundation[2],
        foundation4=foundation[3],
    )


def init_from_solvitaire(game_dict):
    def card(c):
        """ fixes up card definitions for Solvitaire format compat """
        if c.startswith("10"):
            t = "t" if c[-1] in "cdsh" else "T"
            return c.replace("10", t)
        return c

    stock = tuple(map(card, game_dict["stock"]))
    tableau = tuple(tuple(map(card, t)) for t in game_dict["tableau piles"])
    waste = tuple(game_dict.get("waste", ()))
    foundation = tuple(game_dict.get("foundations", [tuple()] * 4))
    return KlonState(
        stock=stock,
        waste=waste,
        tableau1=tableau[0],
        tableau2=tableau[1],
        tableau3=tableau[2],
        tableau4=tableau[3],
        tableau5=tableau[4],
        tableau6=tableau[5],
        tableau7=tableau[6],
        foundation1=foundation[0],
        foundation2=foundation[1],
        foundation3=foundation[2],
        foundation4=foundation[3],
    )


def to_dict(state):
    TABLEAU = [TABLEAU1, TABLEAU2, TABLEAU3, TABLEAU4, TABLEAU5, TABLEAU6, TABLEAU7]
    FND = [FOUNDATION_C, FOUNDATION_D, FOUNDATION_S, FOUNDATION_H]
    return {
        "stock": list(state.stock),
        "waste": list(state.waste),
        "tableau": list(map(lambda t: list(state[t]), TABLEAU)),
        "foundation": list(map(lambda f: list(state[f]), FND)),
    }


def to_ui_state(state):
    def update_card(card):
        t = "t" if "t" in card else "T"
        return card.replace(t, "10")

    def cardseq(seq):
        return list(map(update_card, seq))

    s = to_dict(state)
    s["stock"] = list(map(lambda c: c.lower(), cardseq(s["stock"])))
    s["waste"] = cardseq(s["waste"])
    for pile in ["tableau", "foundation"]:
        for i, seq in enumerate(s[pile]):
            s[pile][i] = cardseq(s[pile][i])
    return s


def pprint_st(state):
    pprint(to_dict(state))


def init_from_dict(game):
    tableau = game["tableau"]
    foundation = game["foundations"]
    return KlonState(
        stock=tuple(game["stock"]),
        waste=tuple(game["waste"]),
        tableau1=tuple(tableau[0]),
        tableau2=tuple(tableau[1]),
        tableau3=tuple(tableau[2]),
        tableau4=tuple(tableau[3]),
        tableau5=tuple(tableau[4]),
        tableau6=tuple(tableau[5]),
        tableau7=tuple(tableau[6]),
        foundation1=tuple(foundation[0]),
        foundation2=tuple(foundation[1]),
        foundation3=tuple(foundation[2]),
        foundation4=tuple(foundation[3]),
    )
