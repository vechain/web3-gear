from codecs import open
from os import path
from setuptools import (
    setup,
    find_packages,
)


here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()


setup(
    name="web3-gear",
    version="2.0.2",
    description="An adapter between thor-restful and eth-rpc.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vechain/web3-gear",
    author="Han Xiao",
    author_email="smallcpp@foxmail.com",
    license="MIT",
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
    ],
    keywords="thor blockchain ethereum",
    packages=find_packages("."),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=[x.strip() for x in open('requirements.txt')],
    entry_points={
        "console_scripts": [
            "web3-gear=gear.cli:run_server",
        ],
    }
)
