from distutils.core import setup
from Cython.Build import cythonize

setup(name="KlonSolve", ext_modules=cythonize("gamestate.pyx"))
