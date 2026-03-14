"""
setup.py — Makes the project installable as a package.

CONCEPT: Adding setup.py lets you install the framework in editable mode:
    pip install -e .

This adds `src/` and `config/` to the Python path so imports like
    from src.api.posts_api import PostsAPI
work from anywhere without needing PYTHONPATH manipulation.
"""

from setuptools import setup, find_packages

setup(
    name="pytest-api-framework",
    version="1.0.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "requests",
        "pytest",
        "pydantic",
        "allure-pytest",
    ],
    python_requires=">=3.10",
)
