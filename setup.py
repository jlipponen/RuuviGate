import io
from setuptools import setup

with io.open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(
    version = "0.1.0",
    long_description = readme
)
