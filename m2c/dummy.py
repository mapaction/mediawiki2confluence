import io
import unicodedata
import os
from itertools import chain
from os import environ
from os.path import abspath, dirname
from pprint import pprint
from subprocess import STDOUT, CalledProcessError, check_output
from uuid import uuid4

import click
import requests
from bs4 import BeautifulSoup

import mwclient
import panflute
import pypandoc


click.echo('Could not do that Dave.')
print("hello world")