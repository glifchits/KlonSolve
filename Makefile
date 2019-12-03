.PHONY: all build profile solver test

all: build

solver: build
	python solver.py

build:
	@echo Building Cython extension
	python setup.py build_ext --inplace

profile: test
	@echo Profile
	cython gamestate.pyx -a && open gamestate.html

test: build
	@echo Running important tests
	python tuplestate_test.py

testall: build
	@echo Running all tests
	python tuplestate_test.py
	python solver_test.py
	python policies_test.py
	python benchmarking_test.py
