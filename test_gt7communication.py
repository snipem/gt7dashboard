import time
import unittest

import gt7communication
from gt7lap import Lap

PLAYSTATION_IP = "192.168.178.119"


# @unittest.skip("Works only with real game running")
class GT7CommunicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.gt7comm = gt7communication.GT7Communication(PLAYSTATION_IP)
        # Do not quit with the main process
        self.gt7comm.daemon = False
        self.gt7comm.start()
        # Sleep until connection is setup
        # TODO Add timeout
        while not self.gt7comm.is_connected():
            time.sleep(0.1)

    def tearDown(self) -> None:
        self.gt7comm.stop()
    def test_run(self):
        car_data = self.gt7comm.get_last_data()
        self.assertTrue(self.gt7comm.is_connected())
        # is always 85
        self.assertEqual(85, car_data.water_temp)

    def test_run_add_debug(self):
        while self.gt7comm.is_connected():
            car_data = self.gt7comm.get_last_data()
            print(car_data.rpm, car_data.in_race)
        # self.assertTrue(self.gt7comm.is_connected())
        # is always 85
        # self.assertEqual(85, car_data.water_temp)

    def test_load_laps(self):
        self.gt7comm = gt7communication.GT7Communication(PLAYSTATION_IP)

        self.gt7comm.laps = [Lap()]
        self.gt7comm.laps[0].number = 0

        laps = [Lap(), Lap()]
        laps[0].number = 1
        laps[1].number = 2

        self.gt7comm.load_laps(laps, to_last_position=True)
        self.assertEqual(3, len(self.gt7comm.laps))
        self.assertEqual(1, self.gt7comm.laps[1].number)

        self.gt7comm.load_laps(laps, to_first_position=True)
        self.assertEqual(5, len(self.gt7comm.laps))
        self.assertEqual(1, self.gt7comm.laps[3].number)

        self.gt7comm.load_laps(laps, replace_other_laps=True)
        self.assertEqual(2, len(self.gt7comm.laps))
        self.assertEqual(1, self.gt7comm.laps[0].number)
