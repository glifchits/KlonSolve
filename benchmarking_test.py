import os
import pytest
import unittest
from tuplestate import *


@pytest.mark.skipif(os.environ.get("GITHUB_ACTION") != None, reason="In CI environment")
class TestInterop(unittest.TestCase):
    def setUp(self):
        from benchmarking import *

    def test_shootme_seed12(self):
        sm_out = run_shootme_seed(12, fast=True)
        """$ ./KlondikeSolver /G 12 /R /DC 3 /MOVES
         0:
         1: 8H
         2: 6C -3D
         3: JS -JD-5S
         4: 9S -7C-KD-2H
         5: AC -2C-JC-8D-QH
         6: 5C -9D-3S-2S-6S-4S
         7: JH -9H-TS-4D-5D-6D-5H
         8: 3H TD 2D AS 4H 6H AH 8S TH QD KH QS AD KS 7D 4C TC 7H 7S 3C 8C QC 9C KC
         9:
        10:
        11:
        12:
        Minimum Moves Needed: 86"""
        solv_json = convert_shootme_to_solvitaire_json(sm_out)
        state = init_from_solvitaire(solv_json)
        assert state[TABLEAU1] == ("8H",)
        sm_stock = (
            "3H TD 2D AS 4H 6H AH 8S TH QD KH QS AD KS 7D 4C TC 7H 7S 3C 8C QC 9C KC"
        )
        initial_stock = tuple(reversed(sm_stock.split(" ")))
        assert state.stock == initial_stock
        assert state.waste == ()
        assert state[TABLEAU1][-1] == "8H"
        assert state[TABLEAU2][-1] == "6C"
        assert state[TABLEAU3][-1] == "JS"
        assert state[TABLEAU4][-1] == "9S"
        assert state[TABLEAU5][-1] == "AC"
        assert state[TABLEAU6][-1] == "5C"
        assert state[TABLEAU7][-1] == "JH"
