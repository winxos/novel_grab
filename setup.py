# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from novel_grab import (__author__, __description__, __long_description__, __email__, __license__,
                        __title__, __url__, __version__)

setup(
    name=__title__,
    version=__version__,
    description=__description__,
    long_description=__long_description__,
    author=__author__,
    author_email=__email__,
    license=__license__,
    url=__url__,  # use the URL to the github repo
    keywords=['crawler', 'winxos', 'AISTLAB'],  # arbitrary keywords
    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    install_requires=['lxml'],
    packages=find_packages(),
    package_dir={'novel_grab': 'novel_grab'},
    package_data={
        "novel_grab": ["*.json"]
    },
    entry_points={
        "console_scripts": [
            "novel_grab = novel_grab.novel_grab:download",
        ]
    }
)
