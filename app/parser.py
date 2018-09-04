import os
import re
import uuid
import fnmatch
import hashlib

from datetime import datetime
from multiprocessing import Pool

from lxml import html
from lxml.etree import ParserError
from sqlalchemy import and_

from app import db_session
from app.operation import operation
from app.base import DisclosuresBase
from app.models import Filer, Disclosure
from app.mixins import LoggerMixin, RunMixin

# Constants
DISCLOSURES_DIR = 'html/disclosures'

TERMINATE = b'total contributions received during period'

ROW_SELECTOR = './/table[2]/tr'

DATE_FORMAT = '%d-%b-%y'

FILERS_PATH = 'html/filers.html'

# Regexs
FILER_ID_RE = r'[AC][0-9][0-9][0-9][0-9][0-9]'
AMOUNT_RE = r'[0-9].*\.[0-9][0-9]'
STATUS_PATTERN = 'status ='


class DisclosuresParser(DisclosuresBase, LoggerMixin, RunMixin):

    def __init__(self):
        DisclosuresBase.__init__(self)
        self.run['type'] = 'parser'


    @operation
    def parse_disclosures(self, target_id=None):
        """ """
        pattern = '*'
        if target_id is not None:
            pattern = target_id + pattern
        pool = Pool(processes=10)
        for subdir, _, files in os.walk(DISCLOSURES_DIR):
            for fn in fnmatch.filter(files, pattern):
                pool.apply_async(self.parse_disclosure, args=(subdir, fn))
        self.logger.info('Parsed %d new records.', self.record_counter)


    def parse_disclosure(self, subdir, fn):
        """ """
        filer_id = fn.split(' - ')[0]
        file_path = os.path.join(subdir, fn)
        self.logger.info('Processing: %s', file_path)
        with open(file_path, encoding='utf8', errors='replace') as fh:
            content = fh.read()
        try:
            doc = html.fromstring(content)
        except ParserError:
            self.logger.warning('VERIFY: File %s empty', fn)
            return
        donation_count = {}
        for index, row in enumerate(doc.findall(ROW_SELECTOR)):
            if not index or TERMINATE in html.tostring(row).lower():
                continue

            cells = row.xpath('./td//*/text()')
            cells = list(map(str.strip, cells))
            cells = list(filter(len, cells))
            if not len(cells):
                continue
            filing_year = cells[0]
            try:
                filing_year = int(filing_year)
            except ValueError:
                filing_year = 0
            contributor = cells[1] or ''
            address_length = len(cells) - 6
            address = '; '.join(cells[2:2 + address_length])
            amount_index = -4
            try:
                date = str(datetime.strptime(cells[-3], DATE_FORMAT))
            except ValueError:
                date = None
                amount_index = -3
            try:
                amount = cells[amount_index].replace(',', '')
                amount = float(amount)
            except ValueError:
                amount = -1.00
            report_code = cells[-2] or ''
            schedule = cells[-1] or ''
            d_uuid = str(uuid.uuid1())
            count_date = date or ''
            count_id = str(filing_year) + contributor + address + str(amount) \
                       + count_date + report_code + schedule
            m = hashlib.md5()
            m.update(count_id.encode('utf-8'))
            m = m.hexdigest()
            if donation_count.get(m) is None:
                donation_count[m] = 1
            else:
                donation_count[m] += 1
            similar_results = db_session.query(Disclosure).filter(and_(
                Disclosure.filer_id == filer_id,
                Disclosure.filing_year == filing_year,
                Disclosure.contributor == contributor,
                Disclosure.address == address,
                Disclosure.amount == amount,
                Disclosure.date == date,
                Disclosure.report_code == report_code,
                Disclosure.schedule == schedule
            )).all()

            print(similar_results)

            if len(similar_results) >= donation_count[m]:
                continue

            record = Disclosure(
                run_id=self.run_id,
                uuid=d_uuid,
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
            self.record_counter += 1
            self.logger.info('Inserting [%s] %s', d_uuid, record)

        db_session.commit()


    @operation
    def parse_filers(self):
        """ """
        with open(FILERS_PATH, encoding='utf8', errors='replace') as fh:
            line = self._skip_blank_lines(fh)
            while line:
                if re.match(FILER_ID_RE, line):
                    filer_id = line
                    line = self._skip_blank_lines(fh)
                    name = line
                    status_not_reached = True
                    status = ''
                    address = []
                    while status_not_reached:
                        line = self._skip_blank_lines(fh)
                        if STATUS_PATTERN in line.lower():
                            status_not_reached = False
                            status = line.split(' = ')[-1]
                            address = '; '.join(address)
                            f_uuid = str(uuid.uuid1())
                            if db_session.query(Filer).filer(and_(
                                    Filer.filer_id == filer_id,
                                    Filer.name == name,
                                    Filer.address == address,
                                    Filer.status == status
                            )).first() is None:
                                record = Filer(
                                    run_id=self.run_id,
                                    uuid=f_uuid,
                                    filer_id=filer_id,
                                    name=name,
                                    address=address,
                                    status=status
                                )
                                db_session.add(record)
                                self.logger.info('Inserting [%s] %s', f_uuid,
                                                 record)
                                self.record_counter += 1
                            break
                        address.append(line)
                line = self._skip_blank_lines(fh)

        db_session.commit()


    def _skip_blank_lines(self, fh):
        """ """
        line_not_found = True
        line = fh.readline()
        while line_not_found and line:
            line = self._remove_html_tags(line)
            line = line.strip()
            if not len(line):
                line = fh.readline()
                continue
            line_not_found = False
        return line


    def _remove_html_tags(self, text):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
