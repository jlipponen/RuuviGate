import io
from setuptools import setup

with io.open('README.md', encoding='utf-8') as f:
    readme = f.read()

setup(
   name = 'ruuvigate',
    version = '0.1.0',
    author = 'Jan Lipponen',
    author_email = 'jan.lipponen@gmail.com',
    description = 'Python package to push RuuviTag data periodically to specified cloud service',
    long_description = readme,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/jlipponen/RuuviGate',
    license='MIT',
    python_requires='>=3.8',
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux'
    ],
    install_requires=[
        'azure-iot-device>=2.9.0',
        'ruuvitag-sensor>=1.2.0',
        'PyYAML>=6.0'
    ],
    packages=[
        'ruuvigate'
    ],
    include_package_data=True,
)
