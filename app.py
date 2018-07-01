import re
import sys
import requests
import logging

from os import path
from hashlib import md5

from parser import DisclosuresParser
from scraper import DisclosuresScraper

logging.basicConfig(level=logging.INFO)


def run(argv):
    if len(argv) > 1 and argv[1] == '-p':
        parser = DisclosuresParser()
        parser.parse()
    else:
        scraper = DisclosuresScraper()
        scraper.scrape()


if __name__ == '__main__':
    run(sys.argv)
