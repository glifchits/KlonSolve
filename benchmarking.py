import subprocess
from pprint import pprint


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
