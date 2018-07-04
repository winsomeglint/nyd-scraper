import os
import re
import requests
import logging
import tempfile

from os import path
from datetime import datetime

from classes.db import DBTool

RUNTIME = datetime.now()

DISCLOSURES_SCRAPER = 'disclosures-scraper'

FILERS_URL = 'http://www.elections.ny.gov:8080/plsql_browser/all_filers'
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

FILERS_PATH = 'html/filers.html'
DISCLOSURES_PATH = 'html/disclosures/%s - %s.html'

FILERS_TABLE = 'filers'


class DisclosuresScraper(object):

    def __init__(self):
        self.run_id = RUNTIME.strftime(TIME_FORMAT)
        self.session = requests.session()
        self.db = DBTool()
        self.logger = logging.getLogger(DISCLOSURES_SCRAPER)


    def scrape_disclosures(self):
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
                    self.scrape_disclosures()
                    return

                with open(fn, 'ab+') as fh:
                    fh.write(r.content)


    def get_filer_ids(self):
        """ """
        c = self.db.query(FILERS_TABLE, properties=['filer_id'])

        for filer_id in c.fetchall():
            yield filer_id[0]

    def scrape_filers(self):
        """ """
        r = self.session.get(FILERS_URL)
        if path.isfile(FILERS_PATH):
            # Check if the old file and the new are different sizes. If so, use the
            # new one.
            filers_file_size = os.path.getsize(FILERS_PATH)
            tmp_file, tmp_path = tempfile.mkstemp()
            os.write(tmp_file, r.content)
            os.close(tmp_file)
            tmp_file_size = os.path.getsize(tmp_path)
            os.remove(tmp_path)
            if tmp_file_size == filers_file_size:
                return

        with open(FILERS_PATH, 'w+') as fh:
            fh.write(r.content)
        self.logger.log('New filer ids loaded from source.')
