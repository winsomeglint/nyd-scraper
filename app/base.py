import requests

from datetime import datetime

RUNTIME = datetime.now()
TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class DisclosuresBase:

    def __init__(self):
        self.run_id = RUNTIME.strftime(TIME_FORMAT)
        self.session = requests.session()
        self.record_counter = 0
        self.run = {
            'run_id': self.run_id,
            'start_time': RUNTIME,
            'status': 'success'
        }
