import setuptools

with open("README.md", "r") as f:
    long_description = f.read()


setuptools.setup(
    name="watchlogs",
    version="0.1.1",
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
    packages=setuptools.find_packages(),
    install_requires=[
        "colored",
        "seaborn",
        "pyinotify",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
