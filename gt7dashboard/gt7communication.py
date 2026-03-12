import datetime
import json
import logging
import math
import socket
import struct
import time
import copy
import traceback
from datetime import timedelta
from threading import Thread
from typing import List

from Crypto.Cipher import Salsa20

from gt7dashboard.gt7data import GTData
from gt7dashboard.gt7helper import divide_laps, seconds_to_lap_time, should_save_lap
from gt7dashboard.gt7lap import Lap



class Session():
    def __init__(self):
        # best lap overall
        self.special_packet_time = 0
        self.best_lap=-1
        self.min_body_height=1000000 # deliberate high number to be counted down
        self.max_speed=0

    def __eq__(self, other):
        return other is not None and self.best_lap == other.best_lap and self.min_body_height == other.min_body_height and self.max_speed == other.max_speed

class GT7Communication(Thread):
    def __init__(self, playstation_ip):
        # Thread control
        Thread.__init__(self)
        self._shall_run = True
        self._shall_restart = False
        # True will always quit with the main process
        self.daemon = True

        # Set lap callback function as none
        self.lap_callback_function = None

        self.playstation_ip = playstation_ip
        self.send_port = 33739
        self.receive_port = 33740
        self._last_time_data_received = 0

        self.current_lap = Lap()
        self.session = Session()
        self.laps = []
        self.package_id = 0
        self.last_data = GTData(None)

        # This is used to record race data in any case. This will override the "in_race" flag.
        # When recording data. Useful when recording replays.
        self.always_record_data = False


    def stop(self):
        self._shall_run = False
    def run(self):
        while self._shall_run:
            s = None
            try:
                self._shall_restart = False
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                if self.playstation_ip == "255.255.255.255":
                    s.setsockopt (socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                s.bind(('0.0.0.0', self.receive_port))
                self._send_hb(s)
                s.settimeout(10)
                package_id = 0
                package_nr = 0
                while not self._shall_restart and self._shall_run:
                    try:
                        # Receive data from the socket
                        data, address = s.recvfrom(4096)
                        # Increment the package number
                        package_nr = package_nr + 1

                        # Decrypt the received data using Salsa20
                        ddata = salsa20_dec(data)


                        # Check if the decrypted data length is greater than 0 and if the package ID is greater than the current package ID
                        if len(ddata) > 0 and struct.unpack('i', ddata[0x70:0x70 + 4])[0] > package_id:
                            # Update the last time data was received to the current time
                            self._last_time_data_received = time.time()
                            new_data_tl = GTData(ddata)

                            package_id = new_data_tl.package_id

                            is_new_lap = divide_laps(self.last_data, new_data_tl)

                            bstlap = new_data_tl.best_lap
                            lstlap = new_data_tl.last_lap

                            self.current_lap.is_replay = self.always_record_data

                            if new_data_tl.current_lap == 0:
                                self.session.special_packet_time = 0
                            
                            #(new_data_tl.in_race or self.always_record_data)

                            if is_new_lap:
                                self.session.special_packet_time += lstlap - self.current_lap.lap_ticks * 1000.0 / 60.0
                                self.session.best_lap = bstlap

                                if new_data_tl.last_lap > 0:
                                    # Regular finished laps (crossing the finish line in races or time trials)
                                    # have their lap time stored in last_lap
                                    self.current_lap.lap_finish_time = new_data_tl.last_lap
                                else:
                                    # Manual laps have no time assigned, so take current live time as lap finish time.
                                    # Finish time is tracked in seconds while live time is tracked in ms
                                    self.current_lap.lap_finish_time = self.current_lap.lap_live_time * 1000

                                if should_save_lap(self.last_data, new_data_tl, self.current_lap):
                                    self.finish_lap()
                                self.current_lap = Lap()

                            # Update the last received data with the new GTData
                            self.last_data = new_data_tl
                            self._log_data(new_data_tl)

                            if package_nr > 100:
                                self._send_hb(s)
                                package_nr = 0

                    except (OSError, TimeoutError) as e:
                        # Handler for package exceptions
                        self._send_hb(s)
                        package_nr = 0
                        # Reset package id for new connections
                        package_id = 0

            except Exception as e:
                # Handler for general socket exceptions
                # TODO logging not working
                print("Error while connecting to %s:%d: %s" % (self.playstation_ip, self.send_port, e))
                s.close()
                # Wait before reconnect
                time.sleep(5)

    def restart(self):
        self._shall_restart = True

    def is_connected(self) -> bool:
        return self._last_time_data_received > 0 and (time.time() - self._last_time_data_received) <= 1

    def _send_hb(self, s):
        send_data = 'A'
        s.sendto(send_data.encode('utf-8'), (self.playstation_ip, self.send_port))

    def get_last_data(self) -> GTData:
        timeout = time.time() + 5  # 5 seconds timeout
        while True:

            if self.last_data is not None:
                return self.last_data

            if time.time() > timeout:
                break

    def get_last_data_once(self) -> GTData:
        if self.last_data is not None:
            return self.last_data

    def get_laps(self) -> List[Lap]:
        return self.laps

    def load_laps(self, laps: List[Lap], to_last_position = False, to_first_position = False, replace_other_laps = False):
        if to_last_position:
            self.laps = self.laps + laps
        elif to_first_position:
            self.laps = laps + self.laps
        elif replace_other_laps:
            self.laps = laps

    def _log_data(self, data):

        # if not (data.in_race or self.always_record_data):
        #     return

        if data.is_paused:
            return

        if data.ride_height < self.session.min_body_height:
            self.session.min_body_height = data.ride_height

        if data.car_speed > self.session.max_speed:
            self.session.max_speed = data.car_speed

        if data.throttle == 100:
            self.current_lap.full_throttle_ticks += 1

        if data.brake == 100:
            self.current_lap.full_brake_ticks += 1

        if data.brake == 0 and data.throttle == 0:
            self.current_lap.no_throttle_and_no_brake_ticks += 1
            self.current_lap.data_coasting.append(1)
        else:
            self.current_lap.data_coasting.append(0)

        if data.brake > 0 and data.throttle > 0:
            self.current_lap.throttle_and_brake_ticks += 1

        self.current_lap.lap_ticks += 1

        if data.tyre_temp_FL > 100 or data.tyre_temp_FR > 100 or data.tyre_temp_rl > 100 or data.tyre_temp_rr > 100:
            self.current_lap.tires_overheated_ticks += 1

        self.current_lap.data_braking.append(data.brake)
        self.current_lap.data_throttle.append(data.throttle)
        self.current_lap.data_speed.append(data.car_speed)

        delta_divisor = data.car_speed
        if data.car_speed == 0:
            delta_divisor = 1

        delta_fl = data.type_speed_FL / delta_divisor
        delta_fr = data.type_speed_FR / delta_divisor
        delta_rl = data.type_speed_RL / delta_divisor
        delta_rr = data.type_speed_FR / delta_divisor

        if delta_fl > 1.1 or delta_fr > 1.1 or delta_rl > 1.1 or delta_rr > 1.1:
            self.current_lap.tires_spinning_ticks += 1

        self.current_lap.data_tires.append(delta_fl + delta_fr + delta_rl + delta_rr)

        ## RPM and shifting

        self.current_lap.data_rpm.append(data.rpm)
        self.current_lap.data_gear.append(data.current_gear)

        ## Log Position

        self.current_lap.data_position_x.append(data.position_x)
        self.current_lap.data_position_y.append(data.position_y)
        self.current_lap.data_position_z.append(data.position_z)

        ## Log Boost

        self.current_lap.data_boost.append(data.boost)

        ## Log Yaw Rate

        # This is the interval to collection yaw rate
        interval = 1 * 60 # 1 second has 60 fps and 60 data ticks
        self.current_lap.data_rotation_yaw.append(data.rotation_yaw)

        # Collect yaw rate, skip first interval with all zeroes
        if len(self.current_lap.data_rotation_yaw) > interval:
            yaw_rate_per_second = data.rotation_yaw - self.current_lap.data_rotation_yaw[-interval]
        else:
            yaw_rate_per_second = 0

        self.current_lap.data_absolute_yaw_rate_per_second.append(abs(yaw_rate_per_second))

        # Adapted from https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728/post-13810797
        self.current_lap.lap_live_time = (self.current_lap.lap_ticks * 1. / 60.) - (self.session.special_packet_time / 1000.)
        self.current_lap.data_time.append(self.current_lap.lap_live_time)

        self.current_lap.car_id = data.car_id


    def finish_lap(self, manual=False):
        """
        Finishes a lap with info we only know after crossing the line after each lap
        """

        # Track recording meta data
        self.current_lap.is_replay = self.always_record_data
        self.current_lap.is_manual = manual

        self.current_lap.fuel_at_end = self.last_data.current_fuel
        self.current_lap.fuel_consumed = self.current_lap.fuel_at_start - self.current_lap.fuel_at_end
        # self.current_lap.lap_finish_time = self.current_lap.lap_finish_time
        self.current_lap.total_laps = self.last_data.total_laps
        self.current_lap.title = seconds_to_lap_time(self.current_lap.lap_finish_time / 1000)
        self.current_lap.car_id = self.last_data.car_id
        self.current_lap.number = self.last_data.current_lap - 1  # Is not counting the same way as the in-game timetable
        # TODO Proper pythonic name
        self.current_lap.EstimatedTopSpeed = self.last_data.estimated_top_speed

        
        self.current_lap.lap_end_timestamp = datetime.datetime.now()
        # if len(self.laps) > 1:
        #     self.current_lap = equalizer_lap(self.laps[0], self.current_lap)

        self.laps.insert(0, self.current_lap)

        # Make a copy of this lap and call the callback function if set
        if self.lap_callback_function:
            self.lap_callback_function(copy.deepcopy(self.current_lap))

        # Reset current lap with an empty one
        self.current_lap = Lap()
        self.current_lap.fuel_at_start = self.last_data.current_fuel


    def reset(self):
        """
        Resets the current lap, all stored laps and the current session.
        """
        self.current_lap = Lap()
        self.session = Session()
        self.last_data = GTData(None)
        self.laps = []

    def set_lap_callback(self, new_lap_callback):
        self.lap_callback_function = new_lap_callback


# data stream decoding
def salsa20_dec(dat):
    key = b'Simulator Interface Packet GT7 ver 0.0'
    # Seed IV is always located here
    oiv = dat[0x40:0x44]
    iv1 = int.from_bytes(oiv, byteorder='little')
    # Notice DEADBEAF, not DEADBEEF
    iv2 = iv1 ^ 0xDEADBEAF
    iv = bytearray()
    iv.extend(iv2.to_bytes(4, 'little'))
    iv.extend(iv1.to_bytes(4, 'little'))
    cipher = Salsa20.new(key[0:32], bytes(iv))
    ddata = cipher.decrypt(dat)
    magic = int.from_bytes(ddata[0:4], byteorder='little')
    if magic != 0x47375330:
        return bytearray(b'')
    return ddata
