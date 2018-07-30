import os
import filecmp
import requests
import logging
import tempfile

from os import path
from datetime import datetime

from app.db import db_session
from app.models import Filer

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


class DisclosuresScraper(object):

    def __init__(self):
        self.run_id = RUNTIME.strftime(TIME_FORMAT)
        self.session = requests.session()
        self.logger = logging.getLogger(DISCLOSURES_SCRAPER)


    def scrape_disclosures(self, filer_id=None):
        """ """
        iterator = db_session.query(Filer.filer_id)
        if filer_id is not None:
            iterator = db_session.query(Filer.filer_id).filter(Filer.filer_id == filer_id)
        for row in iterator:
            filer_id = row[0]
            for f_year in range(FIRST_YEAR, LAST_YEAR + 1):
                data = DISCLOSURES_DATA.copy()
                data['filerid_in'] = filer_id
                data['fyear_in'] = f_year
                fn = DISCLOSURES_PATH % (filer_id, f_year)
                try:
                    self.logger.info('Retrieving: %s', fn)
                    r = self.session.post(DISCLOSURES_URL, data)
                except requests.exceptions.ConnectionError as e:
                    self.logger.error(e)
                    self.scrape_disclosures()
                    return

                if os.path.isfile(fn):
                    tmp_file, tmp_path = tempfile.mkstemp()
                    with os.fdopen(tmp_file, 'wb') as tmp:
                        tmp.write(r.content)
                    not_updated = filecmp.cmp(fn, tmp_path)
                    os.remove(tmp_path)
                    if not_updated:
                        self.logger.info('No change in %s', fn)
                        continue
                    self.logger.info('%s changed since last scrape; replacing...', fn)

                with open(fn, 'wb+') as fh:
                    fh.write(r.content)


    def scrape_filers(self):
        """ """
        r = self.session.get(FILERS_URL)
        if path.isfile(FILERS_PATH):
            # Check if the old file and the new are different sizes. If so, use the
            # new one.
            self.logger.info('Retrieving filers list...')
            tmp_file, tmp_path = tempfile.mkstemp()
            with os.fdopen(tmp_file, 'wb') as tmp:
                tmp.write(r.content)
            not_updated = filecmp.cmp(FILERS_PATH, tmp_path)
            os.remove(tmp_path)
            if not_updated:
                self.logger.info('No change in filers list.')
                return

        with open(FILERS_PATH, 'wb+') as fh:
            fh.write(r.content)
        self.logger.info('New filer ids loaded from source.')
