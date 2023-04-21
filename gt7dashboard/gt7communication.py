import datetime
import json
import logging
import socket
import struct
import time
import traceback
from datetime import timedelta
from threading import Thread
from typing import List

from salsa20 import Salsa20_xor

from gt7dashboard.gt7helper import seconds_to_lap_time
from gt7dashboard.gt7lap import Lap


class GTData:
    def __init__(self, ddata):
        if not ddata:
            return

        self.package_id = struct.unpack('i', ddata[0x70:0x70 + 4])[0]
        self.best_lap = struct.unpack('i', ddata[0x78:0x78 + 4])[0]
        self.last_lap = struct.unpack('i', ddata[0x7C:0x7C + 4])[0]
        self.current_lap = struct.unpack('h', ddata[0x74:0x74 + 2])[0]
        self.current_gear = struct.unpack('B', ddata[0x90:0x90 + 1])[0] & 0b00001111
        self.suggested_gear = struct.unpack('B', ddata[0x90:0x90 + 1])[0] >> 4
        self.fuel_capacity = struct.unpack('f', ddata[0x48:0x48 + 4])[0]
        self.current_fuel = struct.unpack('f', ddata[0x44:0x44 + 4])[0]  # fuel
        self.boost = struct.unpack('f', ddata[0x50:0x50 + 4])[0] - 1

        self.tyre_diameter_FL = struct.unpack('f', ddata[0xB4:0xB4 + 4])[0]
        self.tyre_diameter_FR = struct.unpack('f', ddata[0xB8:0xB8 + 4])[0]
        self.tyre_diameter_RL = struct.unpack('f', ddata[0xBC:0xBC + 4])[0]
        self.tyre_diameter_RR = struct.unpack('f', ddata[0xC0:0xC0 + 4])[0]

        self.type_speed_FL = abs(3.6 * self.tyre_diameter_FL * struct.unpack('f', ddata[0xA4:0xA4 + 4])[0])
        self.type_speed_FR = abs(3.6 * self.tyre_diameter_FR * struct.unpack('f', ddata[0xA8:0xA8 + 4])[0])
        self.type_speed_RL = abs(3.6 * self.tyre_diameter_RL * struct.unpack('f', ddata[0xAC:0xAC + 4])[0])
        self.tyre_speed_RR = abs(3.6 * self.tyre_diameter_RR * struct.unpack('f', ddata[0xB0:0xB0 + 4])[0])

        self.car_speed = 3.6 * struct.unpack('f', ddata[0x4C:0x4C + 4])[0]

        if self.car_speed > 0:
            self.tyre_slip_ratio_FL = '{:6.2f}'.format(self.type_speed_FL / self.car_speed)
            self.tyre_slip_ratio_FR = '{:6.2f}'.format(self.type_speed_FR / self.car_speed)
            self.tyre_slip_ratio_RL = '{:6.2f}'.format(self.type_speed_RL / self.car_speed)
            self.tyre_slip_ratio_RR = '{:6.2f}'.format(self.tyre_speed_RR / self.car_speed)

        self.time_on_track = timedelta(
            seconds=round(struct.unpack('i', ddata[0x80:0x80 + 4])[0] / 1000))  # time of day on track

        self.total_laps = struct.unpack('h', ddata[0x76:0x76 + 2])[0]  # total laps

        self.current_position = struct.unpack('h', ddata[0x84:0x84 + 2])[0]  # current position
        self.total_positions = struct.unpack('h', ddata[0x86:0x86 + 2])[0]  # total positions

        self.car_id = struct.unpack('i', ddata[0x124:0x124 + 4])[0]  # car id

        self.throttle = struct.unpack('B', ddata[0x91:0x91 + 1])[0] / 2.55  # throttle
        self.rpm = struct.unpack('f', ddata[0x3C:0x3C + 4])[0]  # rpm
        self.rpm_rev_warning = struct.unpack('H', ddata[0x88:0x88 + 2])[0]  # rpm rev warning

        self.brake = struct.unpack('B', ddata[0x92:0x92 + 1])[0] / 2.55  # brake

        self.boost = struct.unpack('f', ddata[0x50:0x50 + 4])[0] - 1  # boost

        self.rpm_rev_limiter = struct.unpack('H', ddata[0x8A:0x8A + 2])[0]  # rpm rev limiter

        self.estimated_top_speed = struct.unpack('h', ddata[0x8C:0x8C + 2])[0]  # estimated top speed

        self.clutch = struct.unpack('f', ddata[0xF4:0xF4 + 4])[0]  # clutch
        self.clutch_engaged = struct.unpack('f', ddata[0xF8:0xF8 + 4])[0]  # clutch engaged
        self.rpm_after_clutch = struct.unpack('f', ddata[0xFC:0xFC + 4])[0]  # rpm after clutch

        self.oil_temp = struct.unpack('f', ddata[0x5C:0x5C + 4])[0]  # oil temp
        self.water_temp = struct.unpack('f', ddata[0x58:0x58 + 4])[0]  # water temp

        self.oil_pressure = struct.unpack('f', ddata[0x54:0x54 + 4])[0]  # oil pressure
        self.ride_height = 1000 * struct.unpack('f', ddata[0x38:0x38 + 4])[0]  # ride height

        self.tyre_temp_FL = struct.unpack('f', ddata[0x60:0x60 + 4])[0]  # tyre temp FL
        self.tyre_temp_FR = struct.unpack('f', ddata[0x64:0x64 + 4])[0]  # tyre temp FR

        self.suspension_fl = struct.unpack('f', ddata[0xC4:0xC4 + 4])[0]  # suspension FL
        self.suspension_fr = struct.unpack('f', ddata[0xC8:0xC8 + 4])[0]  # suspension FR

        self.tyre_temp_rl = struct.unpack('f', ddata[0x68:0x68 + 4])[0]  # tyre temp RL
        self.tyre_temp_rr = struct.unpack('f', ddata[0x6C:0x6C + 4])[0]  # tyre temp RR

        self.suspension_rl = struct.unpack('f', ddata[0xCC:0xCC + 4])[0]  # suspension RL
        self.suspension_rr = struct.unpack('f', ddata[0xD0:0xD0 + 4])[0]  # suspension RR

        self.gear_1 = struct.unpack('f', ddata[0x104:0x104 + 4])[0]  # 1st gear
        self.gear_2 = struct.unpack('f', ddata[0x108:0x108 + 4])[0]  # 2nd gear
        self.gear_3 = struct.unpack('f', ddata[0x10C:0x10C + 4])[0]  # 3rd gear
        self.gear_4 = struct.unpack('f', ddata[0x110:0x110 + 4])[0]  # 4th gear
        self.gear_5 = struct.unpack('f', ddata[0x114:0x114 + 4])[0]  # 5th gear
        self.gear_6 = struct.unpack('f', ddata[0x118:0x118 + 4])[0]  # 6th gear
        self.gear_7 = struct.unpack('f', ddata[0x11C:0x11C + 4])[0]  # 7th gear
        self.gear_8 = struct.unpack('f', ddata[0x120:0x120 + 4])[0]  # 8th gear

        # self.struct.unpack('f', ddata[0x100:0x100+4])[0]					# ??? gear

        self.position_x = struct.unpack('f', ddata[0x04:0x04 + 4])[0]  # pos X
        self.position_y = struct.unpack('f', ddata[0x08:0x08 + 4])[0]  # pos Y
        self.position_z = struct.unpack('f', ddata[0x0C:0x0C + 4])[0]  # pos Z

        self.velocity_x = struct.unpack('f', ddata[0x10:0x10 + 4])[0]  # velocity X
        self.velocity_y = struct.unpack('f', ddata[0x14:0x14 + 4])[0]  # velocity Y
        self.velocity_z = struct.unpack('f', ddata[0x18:0x18 + 4])[0]  # velocity Z

        self.rotation_pitch = struct.unpack('f', ddata[0x1C:0x1C + 4])[0]  # rot Pitch
        self.rotation_yaw = struct.unpack('f', ddata[0x20:0x20 + 4])[0]  # rot Yaw
        self.rotation_roll = struct.unpack('f', ddata[0x24:0x24 + 4])[0]  # rot Roll

        self.angular_velocity_x = struct.unpack('f', ddata[0x2C:0x2C + 4])[0]  # angular velocity X
        self.angular_velocity_y = struct.unpack('f', ddata[0x30:0x30 + 4])[0]  # angular velocity Y
        self.angular_velocity_z = struct.unpack('f', ddata[0x34:0x34 + 4])[0]  # angular velocity Z

        self.is_paused = bin(struct.unpack('B', ddata[0x8E:0x8E + 1])[0])[-2] == '1'
        self.in_race = bin(struct.unpack('B', ddata[0x8E:0x8E + 1])[0])[-1] == '1'

        # struct.unpack('f', ddata[0x28:0x28+4])[0]					# rot ???

        # bin(struct.unpack('B', ddata[0x8E:0x8E+1])[0])[2:]	# various flags (see https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketG7S0.cs)
        # bin(struct.unpack('B', ddata[0x8F:0x8F+1])[0])[2:]	# various flags (see https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketG7S0.cs)
        # bin(struct.unpack('B', ddata[0x93:0x93+1])[0])[2:]	# 0x93 = ???

        # struct.unpack('f', ddata[0x94:0x94+4])[0]			# 0x94 = ???
        # struct.unpack('f', ddata[0x98:0x98+4])[0]			# 0x98 = ???
        # struct.unpack('f', ddata[0x9C:0x9C+4])[0]			# 0x9C = ???
        # struct.unpack('f', ddata[0xA0:0xA0+4])[0]			# 0xA0 = ???

        # struct.unpack('f', ddata[0xD4:0xD4+4])[0]			# 0xD4 = ???
        # struct.unpack('f', ddata[0xD8:0xD8+4])[0]			# 0xD8 = ???
        # struct.unpack('f', ddata[0xDC:0xDC+4])[0]			# 0xDC = ???
        # struct.unpack('f', ddata[0xE0:0xE0+4])[0]			# 0xE0 = ???

        # struct.unpack('f', ddata[0xE4:0xE4+4])[0]			# 0xE4 = ???
        # struct.unpack('f', ddata[0xE8:0xE8+4])[0]			# 0xE8 = ???
        # struct.unpack('f', ddata[0xEC:0xEC+4])[0]			# 0xEC = ???
        # struct.unpack('f', ddata[0xF0:0xF0+4])[0]			# 0xF0 = ???

    def to_json(self):
        return json.dumps(self, indent=4, sort_keys=True, default=str)

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

        self.playstation_ip = playstation_ip
        self.send_port = 33739
        self.receive_port = 33740
        self._last_time_data_received = 0

        self.current_lap = Lap()
        self.session = Session()
        self.laps = []
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
                s.bind(('0.0.0.0', self.receive_port))
                self._send_hb(s)
                s.settimeout(10)
                previous_lap = -1
                package_id = 0
                package_nr = 0
                while not self._shall_restart and self._shall_run:
                    try:
                        data, address = s.recvfrom(4096)
                        package_nr = package_nr + 1
                        ddata = salsa20_dec(data)
                        if len(ddata) > 0 and struct.unpack('i', ddata[0x70:0x70 + 4])[0] > package_id:

                            self.last_data = GTData(ddata)
                            self._last_time_data_received = time.time()

                            package_id = struct.unpack('i', ddata[0x70:0x70 + 4])[0]

                            bstlap = struct.unpack('i', ddata[0x78:0x78 + 4])[0]
                            lstlap = struct.unpack('i', ddata[0x7C:0x7C + 4])[0]
                            curlap = struct.unpack('h', ddata[0x74:0x74 + 2])[0]

                            if curlap == 0:
                                self.session.special_packet_time = 0

                            if curlap > 0 and (self.last_data.in_race or self.always_record_data):

                                if curlap != previous_lap:
                                    # New lap
                                    previous_lap = curlap

                                    self.session.special_packet_time += lstlap - self.current_lap.lap_ticks * 1000.0 / 60.0
                                    self.session.best_lap = bstlap

                                    self.finish_lap()

                            else:
                                curLapTime = 0
                                # Reset lap
                                self.current_lap = Lap()

                            self._log_data(self.last_data)

                            if package_nr > 100:
                                self._send_hb(s)
                                package_nr = 0
                    except (OSError, TimeoutError) as e:
                        # Handler for package exceptions
                        self._send_hb(s)
                        package_nr = 0

            except Exception as e:
                # Handler for general socket exceptions
                logging.info("No connection to %s:%d: %s" % (self.playstation_ip, self.send_port, e))
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

        if not (data.in_race or self.always_record_data):
            return

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
        self.current_lap.data_rpm.append(data.rpm)

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

        ## Log Position

        self.current_lap.data_position_x.append(data.position_x)
        self.current_lap.data_position_y.append(data.position_y)
        self.current_lap.data_position_z.append(data.position_z)

        # Adapted from https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728/post-13810797
        self.current_lap.lap_live_time = (self.current_lap.lap_ticks * 1. / 60.) - (self.session.special_packet_time / 1000.)

        self.current_lap.data_time.append(self.current_lap.lap_live_time)

        self.current_lap.car_id = data.car_id

    def finish_lap(self, manual=False):
        """
        Finishes a lap with info we only know after crossing the line after each lap
        """

        if manual:
            # Manual laps have no time assigned, so take current live time as lap finish time.
            # Finish time is tracked in seconds while live time is tracked in ms
            self.current_lap.lap_finish_time = self.current_lap.lap_live_time * 1000
        else:
            # Regular finished laps (crossing the finish line in races or time trials)
            # have their lap time stored in last_lap
            self.current_lap.lap_finish_time = self.last_data.last_lap

        # Track recording meta data
        self.current_lap.is_replay = self.always_record_data
        self.current_lap.is_manual = manual

        self.current_lap.fuel_at_end = self.last_data.current_fuel
        self.current_lap.fuel_consumed = self.current_lap.fuel_at_start - self.current_lap.fuel_at_end
        self.current_lap.lap_finish_time = self.current_lap.lap_finish_time
        self.current_lap.title = seconds_to_lap_time(self.current_lap.lap_finish_time / 1000)
        self.current_lap.car_id = self.last_data.car_id
        self.current_lap.number = self.last_data.current_lap - 1  # Is not counting the same way as the in-game timetable
        self.current_lap.EstimatedTopSpeed = self.last_data.estimated_top_speed

        # Race is not in 0th lap, which is before starting the race.
        # We will only persist those laps that have crossed the starting line at least once
        # TODO Correct this comment, this is about Laptime not lap numbers
        if self.current_lap.lap_finish_time > 0:
            self.laps.insert(0, self.current_lap)

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
    ddata = Salsa20_xor(dat, bytes(iv), key[0:32])
    magic = int.from_bytes(ddata[0:4], byteorder='little')
    if magic != 0x47375330:
        return bytearray(b'')
    return ddata
