from setuptools import setup, find_packages

setup(
    name="what",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "what=src.what:main",
        ],
    },
)
