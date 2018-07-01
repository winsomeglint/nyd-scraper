import os
import sys
import sqlite3
import logging

from os import path, walk
from lxml import html
from datetime import datetime

from dbtool import DBTool

# Constants
DISCLOSURES_PARSER = 'disclosures-parser'
DISCLOSURES_DIR = 'html/disclosures'
DISCLOSURES_TABLE = 'ny_disclosures'

TERMINATE = b'total contributions received during period'

ROW_SELECTOR = './/table[2]/tr'

RUNTIME = datetime.now()
TIME_FORMAT  = '%Y-%m-%d %H:%M:%S'
UUID_FORMAT = '%Y%m%d%H%M%S%f'


class DisclosuresParser(object):

    def __init__(self):
        self.run_id = RUNTIME.strftime(TIME_FORMAT)
        self.db = DBTool()
        self.logger = logging.getLogger(DISCLOSURES_PARSER)

        #If table doesn't already exist, create it
        self.db.create_table(DISCLOSURES_TABLE,
            id='integer primary key autoincrement',
            run_id='text',
            uuid='text',
            filer_id='text',
            filing_year='text',
            contributor='text',
            address='text',
            amount='text',
            date='text',
            report_code='text',
            schedule='text'
        )


    def parse(self):
        """ """
        for subdir, dirs, files in os.walk(DISCLOSURES_DIR):
            for fn in files:
                filer_id = fn.split(' - ')[0]
                file_path = path.join(subdir, fn)
                self.logger.info('Processing: %s', file_path)
                with open(file_path) as fh:
                    content = fh.read()
                doc = html.fromstring(content)

                for index, row in enumerate(doc.findall(ROW_SELECTOR)):
                    if not index or TERMINATE in html.tostring(row).lower():
                        continue

                    cells = row.xpath('./td//*/text()')
                    cells = list(map(str.strip, cells))
                    cells = list(filter(lambda x: len(x), cells))
                    if not len(cells):
                        continue
                    filing_year = cells[0]
                    contributor = cells[1]
                    address_length = len(cells) - 6
                    address = '; '.join(cells[2:2 + address_length])
                    amount = cells[-4]
                    date = cells[-3]
                    report_code = cells[-2]
                    schedule = cells[-1]

                    c = self.db.query(DISCLOSURES_TABLE,
                        filer_id=filer_id,
                        filing_year=filing_year,
                        contributor=contributor,
                        address = address,
                        amount = amount,
                        date = date,
                        report_code = report_code,
                        schedule = schedule
                    )
                    if c.fetchone() is not None:
                        continue

                    self.db.insert(DISCLOSURES_TABLE,
                        None,
                        self.run_id,
                        datetime.now().strftime(UUID_FORMAT),
                        filer_id,
                        filing_year,
                        contributor,
                        address,
                        amount,
                        date,
                        report_code,
                        schedule
                    )

                    self.logger.info('Inserted record for contributor %s to filer_id %s.', contributor, filer_id)
