import io
from setuptools import setup

import ruuvigate

with io.open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(
    name = "ruuvigate",
    version = ruuvigate.__version__,
    author = "Jan Lipponen",
    author_email = "jan.lipponen@gmail.com",
    description = "An application to push RuuviTag data periodically to cloud",
    long_description = readme,
    long_description_content_type = "text/markdown",
    url = "https://github.com/jlipponen/RuuviGate",
    license='MIT',
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux"
    ],
    python_requires=[
        ">=3.8",
    ],
    install_requires=[
        'ptyprocess;platform_system=="Linux"'
    ],
    packages=[
        'ruuvigate'
    ],
    include_package_data=True,
)
