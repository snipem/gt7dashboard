import time
import unittest

import gt7communication


class GT7CommunicationTest(unittest.TestCase):
    def test_run(self):
        gt7comm = gt7communication.GT7Communication("192.168.178.120")
        # Do not quit with the main process
        gt7comm.daemon = False
        gt7comm.start()
        car_data = gt7comm.get_last_data()
        # is always 85
        self.assertEqual(85, car_data.water_temp)
