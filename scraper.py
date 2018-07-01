import re
import sys
import requests
import logging

from os import path
from hashlib import md5
from datetime import datetime

RUNTIME = datetime.now()

DISCLOSURES_SCRAPER = 'disclosures-scraper'

COMMITTEES_URL = 'http://www.elections.ny.gov:8080/plsql_browser/all_filers'
DISCLOSURES_URL = 'http://www.elections.ny.gov:8080/plsql_browser/filer_contribution_details'

TIME_FORMAT  = '%Y-%m-%d %H:%M:%S'

FIRST_YEAR = 1999
LAST_YEAR = RUNTIME.year

DISCLOSURES_DATA = {
    'filerid_in': '', # Specify filer ID here
    'fyear_in': '', # Specify filing year here
    'contributor_in': '', # Can leave this blank
    'amount_in': 0 # Keep this
}

COMMITTEES_PATH = 'html/committees.html'
DISCLOSURES_PATH = 'html/disclosures/%s - %s.html'


class DisclosuresScraper(object):

    def __init__(self):
        self.run_id = RUNTIME.strftime(TIME_FORMAT)
        self.session = requests.session()
        self.logger = logging.getLogger(DISCLOSURES_SCRAPER)


    def scrape(self):
        """ """
        for filer_id in self.get_filer_ids():
            for f_year in range(FIRST_YEAR, LAST_YEAR + 1):
                fn = DISCLOSURES_PATH % (filer_id, f_year)
                if path.isfile(fn):
                    continue
                self.logger.info('Retrieving: %s', fn)
                data = DISCLOSURES_DATA.copy()
                data['filerid_in'] = filer_id
                data['fyear_in'] = f_year
                try:
                    r = self.session.post(DISCLOSURES_URL, data)
                except requests.exceptions.ConnectionError as e:
                    self.scrape()
                    return
                with open(fn, 'ab+') as fh:
                    fh.write(r.content)


    def get_filer_ids(self):
        """ """
        if not path.isfile(COMMITTEES_PATH):
            r = self.session.get(COMMITTEES_URL)
            with open(COMMITTEES_PATH, 'w+') as fh:
                fh.write(r.content.decode('utf-8'))

        with open(COMMITTEES_PATH) as fh:
            for line in fh.readlines():
                line = self.remove_html_tags(line)
                line = line.strip()
                if not len(line):
                    continue
                first_char = line[0]
                str_remainder = line[1:]
                if not first_char.isalpha() or len(str_remainder) < 5 or len(str_remainder) > 7:
                    continue
                try:
                    int(str_remainder)
                except ValueError:
                    continue

                yield line

    def remove_html_tags(self, text):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
