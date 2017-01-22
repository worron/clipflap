#!/usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

"""
Installation routines.
Install:
$ python3 setup.py install --record log.txt
Uninstall:
$ cat log.txt | xargs rm -rf
"""

from setuptools import setup

setup(
	name = "clipflap",
	version = "0.8.dev1",
	description = "Clipboard history widget",
	LICENSE = "GPL",
	author = "worron",
	author_email = "worrongm@gmail.com",
	# url =
	packages=["clipflap"],
	install_requires = ["setuptools"],
	# package_data =
	entry_points = {
		"console_scripts": ["clipflap=clipflap.clipboard:run"],
	},
)
