#!/usr/bin/env python
# -*- coding: utf8 -*-
from setuptools import setup, find_packages

setup(
    name="divine-pak",
    packages=find_packages(),
    version="0.1",
    description="Read the Divinity: Original Sins 2 PAK file format",
    author="Tyler Kennedy",
    author_email="tk@tkte.ch",
    url="http://github.com/TkTech/divine-pak",
    classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
    ],
    install_requires=['lz4', 'click'],
    entry_points='''
        [console_scripts]
        divine-pak=pak.cli:cli
    '''
)
