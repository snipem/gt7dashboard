import time
import unittest

import gt7communication
from gt7lap import Lap


class GT7CommunicationTest(unittest.TestCase):
    def test_run(self):
        gt7comm = gt7communication.GT7Communication("192.168.178.120")
        # Do not quit with the main process
        gt7comm.daemon = False
        gt7comm.start()
        car_data = gt7comm.get_last_data()
        # is always 85
        self.assertEqual(85, car_data.water_temp)


    def test_load_laps(self):
        gt7comm = gt7communication.GT7Communication("192.168.178.120")

        gt7comm.laps = [Lap()]
        gt7comm.laps[0].Number = 0

        laps = [Lap(), Lap()]
        laps[0].Number = 1
        laps[1].Number = 2

        gt7comm.load_laps(laps, to_last_position=True)
        self.assertEqual(3, len(gt7comm.laps))
        self.assertEqual(1, gt7comm.laps[1].Number)

        gt7comm.load_laps(laps, to_first_position=True)
        self.assertEqual(5, len(gt7comm.laps))
        self.assertEqual(1, gt7comm.laps[3].Number)

        gt7comm.load_laps(laps, replace_other_laps=True)
        self.assertEqual(2, len(gt7comm.laps))
        self.assertEqual(1, gt7comm.laps[0].Number)
