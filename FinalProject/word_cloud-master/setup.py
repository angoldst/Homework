
from distutils.core import setup
from Cython.Build import cythonize

setup(
    name='wordcloud',
    ext_modules=cythonize("*.pyx"),
    package_dir={'wordcloud': '.'},
    py_modules=['wordcloud']
)
