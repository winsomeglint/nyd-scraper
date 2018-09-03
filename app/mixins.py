import logging

from datetime import datetime

from app.models import Run
from app.db import db_session


class LoggerMixin:
    @property
    def logger(self):
        component = "{}.{}".format(type(self).__module__, type(self).__name__)
        return logging.getLogger(component)


class RunMixin:

    def terminate(self, operation='default', err=None):
        if not hasattr(self, 'run'):
            return

        if err is not None:
            self.run['status'] = 'error'
            self.run['error_msg'] = str(err)
        self.run['operation'] = operation
        self.run['end_time'] = datetime.now()
        self.run['new_records'] = self.record_counter

        run = Run(**self.run)

        db_session.add(run)
        db_session.commit()
