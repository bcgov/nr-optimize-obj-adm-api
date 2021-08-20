#!/usr/bin/env python
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools

    use_setuptools()
    from setuptools import setup, find_packages


def read(relative):
    """
    Read file contents and return a list of lines.
    ie, read the VERSION file
    """
    contents = open(relative, "r").read()
    return [x for x in contents.split("\n") if x != ""]


with open("README.rst", "r") as f:
    readme = f.read()

setup(
    name="python-ecsclient",
    url="https://github.com/EMCECS/python-ecsclient",
    keywords=["ecsclient"],
    long_description=readme,
    version=read("VERSION")[0],
    description="A library for interacting with the ECS Management API",
    author="ECS",
    author_email="ecs@dell.com",
    tests_require=read("./test-requirements.txt"),
    install_requires=read("./requirements.txt"),
    test_suite="nose.collector",
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=["ez_setup"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
