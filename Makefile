.PHONY: all build profile solver

all: build

solver: build
	python solver.py

build:
	@echo Building Cython extension
	python setup.py build_ext --inplace

profile:
	@echo Profile
	cython get_legal_moves.pyx -a && open get_legal_moves.html
