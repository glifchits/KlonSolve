import re
import os
import random
import subprocess
from pprint import pprint
from tuplestate import init_from_solvitaire
from gamestate import play_move


def listdir(path):
    ls = os.listdir(path)
    return [os.path.join(path, f) for f in ls]


def filename_to_klonstate(fname):
    with open(fname) as f:
        solv = convert_shootme_to_solvitaire_json(f.read())
        state = init_from_solvitaire(solv)
    return state


def random_state(solved=True):
    # if solved == True:
    dirs = ["solved", "solvedmin"]
    # elif solved == False:
    #     dirs = ["impossible"]
    # elif solved == None:
    #     dirs = ["unknown"]
    fulldirs = (f"./fixtures/shootme/{d}" for d in dirs)
    fixtures = [f for d in fulldirs for f in listdir(d)]
    # fname = random.choice(fixtures)
    fname = fixtures[0]
    state = filename_to_klonstate(fname)
    return state


def random_solved_endgame(k):
    dirs = ["solvedmin"]
    fulldirs = (f"./fixtures/shootme/{d}" for d in dirs)
    fixtures = [f for d in fulldirs for f in listdir(d)]
    fname = random.choice(fixtures)
    return endgame(fname, k)


def run_shootme_seed(seed, fast=False):
    cmd = ["./bin/KlondikeSolver", "/G", str(seed), "/R", "/DC", "3", "/MOVES"]
    if fast:
        cmd.append("/FAST")
    data = subprocess.run(cmd, stdout=subprocess.PIPE).stdout.decode("utf-8")
    return data


def convert_shootme_to_solvitaire_json(sm_out):
    lines = [line.strip("\n").replace("T", "10")[4:] for line in sm_out.splitlines()]
    tab_lines = lines[1:8]
    stock_line = lines[8]

    def tableau_pile(line):
        s = line.split("-")
        fup = s[0].strip()
        fdown = s[1:]
        cards = [fup] + [c.strip().lower() for c in fdown]
        return list(reversed(cards))

    return {
        "tableau piles": list(map(tableau_pile, tab_lines)),
        "stock": list(reversed(stock_line.split())),
    }


took_time = re.compile(r".* Took (\d+) ms.$")
win_result = re.compile(r"Minimal solution in (\d+) moves. Took (\d+) ms.")


def parse_winnable(ret):
    lines = ret.splitlines()
    solution_result = lines[15]
    moveseq = lines[-2]
    deck = "\n".join(lines[:13])
    move_count, ms = map(int, win_result.match(solution_result).groups())
    return {
        "solved": True,
        "impossible": False,
        "unknown": False,
        "move_count": move_count,
        "time_ms": ms,
        "result": solution_result,
        "moves": moveseq,
        "deck": deck,
    }


def parse_impossible(ret):
    lines = ret.splitlines()
    solution_result = lines[15]
    moveseq = lines[-2]
    deck = "\n".join(lines[:13])
    ms = int(took_time.match(solution_result).groups()[0])
    return {
        "solved": False,
        "impossible": True,
        "unknown": False,
        "time_ms": ms,
        "result": solution_result,
        "deck": deck,
    }


def state_with_moveseq(fname):
    with open(fname) as f:
        ret = f.read()
    solvjson = convert_shootme_to_solvitaire_json(ret)
    state = init_from_solvitaire(solvjson)
    moveseq = parse_winnable(ret)["moves"].strip().split(" ")
    return state, moveseq


def endgame(fname, k):
    """
    fname: path to a shootme solution fixture
    k: number of moves *remaining* until shootme solution
    :returns: {KlonState}
    """
    state, moveseq = state_with_moveseq(fname)
    while len(moveseq) > k:
        state = play_move(state, moveseq.pop(0))
    return state
