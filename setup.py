from codecs import open
from os import path
from setuptools import (
    setup,
    find_packages,
)


here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="web3-gear",
    version="1.0.4",
    description="An adapter between thor-restful and eth-rpc.",
    long_description=long_description,
    url="https://github.com/z351522453/web3-gear",
    author="Han Xiao",
    author_email="smallcpp@foxmail.com",
    license="MIT",
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
    ],
    keywords="thor blockchain ethereum",
    packages=find_packages("."),
    include_package_data=True,
    install_requires=[x.strip() for x in open('requirements')],
    entry_points={
        "console_scripts": [
            "web3-gear=gear.cli:run_server",
        ],
    }
)
