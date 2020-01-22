import sys
from distutils.util import get_platform
import setuptools

with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
    name="watchlogs",
    version="0.1.3.14",
    entry_points={
        "console_scripts": [
            "watchlogs=watchlogs.watchlogs:main",
        ],
    },
    author="Samuel Albanie",
    description="A simple, colourful logfile watcher",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/albanie/watchlogs",
    packages=["watchlogs"],
    python_requires=">=3.6",
    install_requires=[
        "colored",
        "seaborn",
        "tailf",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        'Operating System :: POSIX :: Linux',
    ],
)
