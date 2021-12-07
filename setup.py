import io
from setuptools import setup

import ruuvigate

with io.open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(
    version = ruuvigate.__version__,
    long_description = readme
)
