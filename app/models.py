
import os

from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, Date, DateTime, Float, Text, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Filer(Base):
    __tablename__ = 'filer'
    __searchable__ = ['filer_id', 'name', 'address', 'status']
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, index=True, default=datetime.utcnow)
    run_id = Column(Text)
    uuid = Column(Text, unique=True)
    filer_id = Column(Text, index=True, unique=True)
    name = Column(Text, index=True)
    address = Column(Text, index=True)
    status = Column(Text)
    disclosures = relationship('Disclosure', backref='payer', lazy='dynamic')

    def __repr__(self):
        return '<Filer {}>'.format(self.filer_id)


class Disclosure(Base):
    __tablename__ = 'disclosure'
    __searchable__ = ['filer_id', 'filing_year', 'contributor', 'address',
                      'amount', 'date', 'report_code', 'schedule']
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, index=True, default=datetime.utcnow)
    run_id = Column(Text)
    uuid = Column(Text, unique=True)
    filer_id = Column(Text, ForeignKey('filer.filer_id'), index=True)
    filing_year = Column(Integer)
    contributor = Column(Text, index=True)
    address = Column(Text, index=True)
    amount = Column(Float)
    date = Column(Date)
    report_code = Column(Text)
    schedule = Column(Text)

    def __repr__(self):
        return '<Disclosure {} {} {}>'.format(self.filer_id, self.amount,
                                              self.date)


engine = create_engine(os.environ.get('DATABASE_URL'))

Base.metadata.create_all(engine)
