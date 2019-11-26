.PHONY: all build profile solver test

all: build

solver: build
	python solver.py

build:
	@echo Building Cython extension
	python setup.py build_ext --inplace

profile:
	@echo Profile
	cython get_legal_moves.pyx -a && open get_legal_moves.html

test: build
	@echo Running important tests
	python tuplestate_test.py # -k test_endgame_1
