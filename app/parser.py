import os
import re
import string
import logging

from random import *
from lxml import html
from hashlib import sha1
from os import path, walk
from datetime import datetime
from lxml.etree import ParserError

from app.db import db_session
from app.models import Filer, Disclosure

from sqlalchemy import and_

# Constants
DISCLOSURES_PARSER = 'disclosures-parser'
DISCLOSURES_DIR = 'html/disclosures'

TERMINATE = b'total contributions received during period'

ROW_SELECTOR = './/table[2]/tr'

RUNTIME = datetime.now()
TIME_FORMAT  = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT = '%d-%b-%y'

FILERS_PATH = 'html/filers.html'

# Regexs
FILER_ID_RE = '[AC][0-9][0-9][0-9][0-9][0-9]'
AMOUNT_RE = '[0-9].*\.[0-9][0-9]'
STATUS_PATTERN = 'status ='

CHARS = string.ascii_letters


class DisclosuresParser(object):

    def __init__(self):
        self.run_id = RUNTIME.strftime(TIME_FORMAT)
        self.logger = logging.getLogger(DISCLOSURES_PARSER)


    def parse_disclosures(self):
        """ """
        for subdir, dirs, files in os.walk(DISCLOSURES_DIR):
            for fn in files:
                filer_id = fn.split(' - ')[0]
                file_path = path.join(subdir, fn)
                self.logger.info('Processing: %s', file_path)
                with open(file_path, encoding='utf8',errors='replace') as fh:
                    content = fh.read()
                try:
                    doc = html.fromstring(content)
                except ParserError:
                    self.logger.warning('VERIFY: File %s empty', fn)
                    continue

                for index, row in enumerate(doc.findall(ROW_SELECTOR)):
                    if not index or TERMINATE in html.tostring(row).lower():
                        continue

                    cells = row.xpath('./td//*/text()')
                    cells = list(map(str.strip, cells))
                    cells = list(filter(len, cells))
                    if not len(cells):
                        continue
                    self.logger.info('Unparsed row %s', html.tostring(row))
                    self.logger.info('Parsed row %s', cells)
                    filing_year = cells[0]
                    try:
                        filing_year = int(filing_year)
                    except ValueError:
                        filing_year = 0
                    contributor = cells[1]
                    address_length = len(cells) - 6
                    address = '; '.join(cells[2:2 + address_length])
                    amount_index = -4
                    try:
                        date = str(datetime.strptime(cells[-3], DATE_FORMAT))
                    except ValueError:
                        date = None
                        amount_index = -3
                    amount = cells[amount_index].replace(',','')
                    try:
                        amount = float(amount)
                    except ValueError:
                        amount = -1.00
                    report_code = cells[-2]
                    schedule = cells[-1]
                    uuid_date = date
                    if date is None:
                        uuid_date = str(datetime.utcnow())
                    salt = ''.join(choice(CHARS) for x in range(randint(0, 26)))
                    uuid = filer_id + contributor + address + str(amount) \
                           + uuid_date + report_code + schedule + self.run_id \
                           + salt
                    uuid = sha1(bytes(uuid, 'utf-8')).hexdigest()

                    if db_session.query(Disclosure).filter(and_(
                        Disclosure.filer_id == filer_id,
                        Disclosure.filing_year == filing_year,
                        Disclosure.contributor == contributor,
                        Disclosure.address == address,
                        Disclosure.amount == amount,
                        Disclosure.date == date,
                        Disclosure.report_code == report_code,
                        Disclosure.schedule == schedule
                    )).first() is not None:
                        continue

                    record = Disclosure(
                        run_id=self.run_id,
                        uuid=uuid,
                        filer_id=filer_id,
                        filing_year=filing_year,
                        contributor=contributor,
                        address=address,
                        amount=amount,
                        date=date,
                        report_code=report_code,
                        schedule=schedule
                    )
                    db_session.add(record)
                    self.logger.info('Inserting [%s] %s', uuid, record)

                db_session.commit()


    def parse_filers(self):
        """ """
        with open(FILERS_PATH, encoding='utf8',errors='replace') as fh:
            line = self.skip_blank_lines(fh)
            while line:
                if re.match(FILER_ID_RE, line):
                    filer_id = line
                    line = self.skip_blank_lines(fh)
                    name = line
                    status_not_reached = True
                    status = ''
                    address = []
                    while status_not_reached:
                        line = self.skip_blank_lines(fh)
                        if STATUS_PATTERN in line.lower():
                            status_not_reached = False
                            status = line.split(' = ')[-1]
                            address = '; '.join(address)
                            salt = ''.join(choice(CHARS) for x in range(randint(0, 26)))
                            uuid = filer_id + name + address + status \
                                   + self.run_id + salt
                            uuid = sha1(bytes(uuid, 'utf-8')).hexdigest()
                            if db_session.query(Filer).filter(and_(
                                Filer.filer_id == filer_id,
                                Filer.name == name,
                                Filer.address == address,
                                Filer.status == status
                            )).first() is None:
                                record = Filer(
                                    run_id=self.run_id,
                                    uuid=uuid,
                                    filer_id=filer_id,
                                    name=name,
                                    address=address,
                                    status=status
                                )
                                db_session.add(record)
                                self.logger.info('Inserting [%s] %s', uuid, record) # noqa
                            break
                        address.append(line)
                line = self.skip_blank_lines(fh)

        db_session.commit()


    def skip_blank_lines(self, fh):
        """ """
        line_not_found = True
        line = fh.readline()
        while line_not_found and line:
            line = self.remove_html_tags(line)
            line = line.strip()
            if not len(line):
                line = fh.readline()
                continue
            line_not_found = False
        return line


    def remove_html_tags(self, text):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
