#!/usr/bin/env python3
# -*- Mode: Python; indent-tabs-mode: t; python-indent: 4; tab-width: 4 -*-

"""
Installation routines.
Install:
$ python3 setup.py install
Uninstall:
$ cat log.txt | xargs rm -rf
"""

from setuptools import setup

setup(
	name = "clipflap",
	version = "1.1",
	description = "Clipboard history widget",
	LICENSE = "GPL",
	author = "worron",
	author_email = "worrongm@gmail.com",
	url = "https://github.com/worron/clipflap",
	packages=["clipflap"],
	install_requires = ["setuptools"],
	package_data = {"cavalcade.data": ["*.ini", "*.svg"]},
	entry_points = {
		"console_scripts": ["clipflap=clipflap.clipboard:run"],
	},

	# Note that these files are only installed correctly if
	# --single-version-externally-managed is used as argument to "setup.py install".
	data_files=[
		("share/icons/hicolor/scalable/apps", ["clipflap/data/clipflap.svg"]),
	],
)
