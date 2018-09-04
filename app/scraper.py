import os
import filecmp
import tempfile

from datetime import datetime
from multiprocessing import Pool

import requests

from app import db_session
from app.models import Filer
from app.operation import operation
from app.base import DisclosuresBase
from app.mixins import LoggerMixin, RunMixin

FILERS_URL = 'http://www.elections.ny.gov:8080/plsql_browser/all_filers'
DISCLOSURES_URL = 'http://www.elections.ny.gov:8080/plsql_browser/filer_contribution_details'

FIRST_YEAR = 1999
LAST_YEAR = datetime.now().year

DISCLOSURES_DATA = {
    'filerid_in': '', # Specify filer ID here
    'fyear_in': '', # Specify filing year here
    'contributor_in': '', # Can leave this blank
    'amount_in': 0 # Keep this
}

FILERS_PATH = 'html/filers.html'
DISCLOSURES_PATH = 'html/disclosures/%s - %s.html'


class DisclosuresScraper(DisclosuresBase, LoggerMixin, RunMixin):

    def __init__(self):
        DisclosuresBase.__init__(self)
        self.run['type'] = 'scraper'


    @operation
    def scrape_disclosures(self, target_id=None):
        """ """
        pool = Pool(processes=10)
        iterator = db_session.query(Filer.filer_id)
        if target_id is not None:
            iterator = db_session.query(Filer.filer_id).filter(Filer.filer_id == target_id)
        for row in iterator:
            filer_id = row[0]
            for f_year in range(FIRST_YEAR, LAST_YEAR + 1):
                pool.apply_async(self.scrape_disclosure, args=(filer_id, f_year))
        self.logger.info('Scraped %d new records.', self.record_counter)


    def scrape_disclosure(self, filer_id, f_year):
        """ """
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
                return
            self.logger.info('%s changed since last scrape; replacing...', fn)

        with open(fn, 'wb+') as fh:
            fh.write(r.content)
        self.record_counter += 1


    @operation
    def scrape_filers(self):
        """ Scrape master list of filers. """
        r = self.session.get(FILERS_URL)
        if os.path.isfile(FILERS_PATH):
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
        self.record_counter += 1
        self.logger.info('New filer ids loaded from source.')
