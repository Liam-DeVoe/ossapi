from distutils.core import setup
from setuptools import find_packages
import re

with open("README.md", "r") as readme:
    long_description = readme.read()

# https://stackoverflow.com/a/7071358
VERSION = "Unknown"
VERSION_RE = r"^__version__ = ['\"]([^'\"]*)['\"]"

with open("ossapi/version.py") as f:
    match = re.search(VERSION_RE, f.read())
    if match:
        VERSION = match.group(1)
    else:
        raise RuntimeError("Unable to find version string in "
            "ossapi/version.py")

setup(
    name="ossapi",
    version=VERSION,
    description="A python wrapper for the osu! api. Includes api v2 support.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    keywords = ["osu!, wrapper, api, python"],
    author="Liam DeVoe",
    author_email="orionldevoe@gmail.com",
    url="https://github.com/circleguard/ossapi",
    download_url = "https://github.com/circleguard/ossapi/tarball/v" + VERSION,
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "requests",
        "requests_oauthlib",
        "osrparse~=6.0",
        "typing_utils"
    ],
    extras_require={
        "async": [
            "aiohttp"
        ]
    }
)
