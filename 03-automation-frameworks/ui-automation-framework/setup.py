from setuptools import setup, find_packages

setup(
    name="ui-automation-framework",
    version="1.0.0",
    packages=find_packages(exclude=["tests*"]),
    install_requires=["selenium", "pytest", "allure-pytest"],
    python_requires=">=3.10",
)
