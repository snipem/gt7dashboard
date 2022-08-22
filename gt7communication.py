import socket
import struct
import time
import traceback
from datetime import timedelta
from threading import Thread
from typing import List

from salsa20 import Salsa20_xor

from gt7helper import secondsToLaptime
from gt7lap import Lap


class GT_Data:
    def __init__(self, ddata):
        if not ddata:
            return

        self.package_id = struct.unpack('i', ddata[0x70:0x70 + 4])[0]
        self.bst_lap = struct.unpack('i', ddata[0x78:0x78 + 4])[0]
        self.last_lap = struct.unpack('i', ddata[0x7C:0x7C + 4])[0]
        self.current_lap = struct.unpack('h', ddata[0x74:0x74 + 2])[0]
        self.current_gear = struct.unpack('B', ddata[0x90:0x90 + 1])[0] & 0b00001111
        self.suggested_gear = struct.unpack('B', ddata[0x90:0x90 + 1])[0] >> 4
        self.fuelCapacity = struct.unpack('f', ddata[0x48:0x48 + 4])[0]
        self.current_fuel = struct.unpack('f', ddata[0x44:0x44 + 4])[0]  # fuel
        self.boost = struct.unpack('f', ddata[0x50:0x50 + 4])[0] - 1

        self.tyreDiamFL = struct.unpack('f', ddata[0xB4:0xB4 + 4])[0]
        self.tyreDiamFR = struct.unpack('f', ddata[0xB8:0xB8 + 4])[0]
        self.tyreDiamRL = struct.unpack('f', ddata[0xBC:0xBC + 4])[0]
        self.tyreDiamRR = struct.unpack('f', ddata[0xC0:0xC0 + 4])[0]

        self.tyreSpeedFL = abs(3.6 * self.tyreDiamFL * struct.unpack('f', ddata[0xA4:0xA4 + 4])[0])
        self.tyreSpeedFR = abs(3.6 * self.tyreDiamFR * struct.unpack('f', ddata[0xA8:0xA8 + 4])[0])
        self.tyreSpeedRL = abs(3.6 * self.tyreDiamRL * struct.unpack('f', ddata[0xAC:0xAC + 4])[0])
        self.tyreSpeedRR = abs(3.6 * self.tyreDiamRR * struct.unpack('f', ddata[0xB0:0xB0 + 4])[0])

        self.carSpeed = 3.6 * struct.unpack('f', ddata[0x4C:0x4C + 4])[0]

        if self.carSpeed > 0:
            self.tyreSlipRatioFL = '{:6.2f}'.format(self.tyreSpeedFL / self.carSpeed)
            self.tyreSlipRatioFR = '{:6.2f}'.format(self.tyreSpeedFR / self.carSpeed)
            self.tyreSlipRatioRL = '{:6.2f}'.format(self.tyreSpeedRL / self.carSpeed)
            self.tyreSlipRatioRR = '{:6.2f}'.format(self.tyreSpeedRR / self.carSpeed)

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
        self.tyre_diameter_FL = 200 * self.tyreDiamFL  # tyre diameter FL
        self.tyre_diameter_FR = 200 * self.tyreDiamFR  # tyre diameter FR

        self.suspension_fl = struct.unpack('f', ddata[0xC4:0xC4 + 4])[0]  # suspension FL
        self.suspension_fr = struct.unpack('f', ddata[0xC8:0xC8 + 4])[0]  # suspension FR

        self.tyre_temp_rl = struct.unpack('f', ddata[0x68:0x68 + 4])[0]  # tyre temp RL
        self.tyre_temp_rr = struct.unpack('f', ddata[0x6C:0x6C + 4])[0]  # tyre temp RR
        self.tyre_diameter_rl = 200 * self.tyreDiamRL  # tyre diameter RL
        self.tyre_diameter_rr = 200 * self.tyreDiamRR  # tyre diameter RR

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

        self.pos_x = struct.unpack('f', ddata[0x04:0x04 + 4])[0]  # pos X
        self.pos_y = struct.unpack('f', ddata[0x08:0x08 + 4])[0]  # pos Y
        self.pos_z = struct.unpack('f', ddata[0x0C:0x0C + 4])[0]  # pos Z

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

class Session():
    def __init__(self):
        # best lap overall
        self.special_packet_time = 0
        self.best_lap=-1
        self.min_body_height=999999
        self.max_speed=0

    def __eq__(self, other):
        return other is not None and self.best_lap == other.best_lap and self.min_body_height == other.min_body_height and self.max_speed == other.max_speed




class GT7Communication(Thread):
    def __init__(self, playstation_ip):
        Thread.__init__(self)
        self.session = Session()
        self.laps = []
        # Always quit with the main process
        self.daemon = True
        self.last_data = GT_Data(None)
        self.current_lap = Lap()
        self.SendPort = 33739
        self.ReceivePort = 33740
        self._last_data_received = 0
        self.Playstation_IP = playstation_ip
        self.dataExample = []

    def run(self):
        # self.connect()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('0.0.0.0', self.ReceivePort))
        self._send_hb(s)
        s.settimeout(10)
        prevlap = -1
        pktid = 0
        pknt = 0
        while True:
            try:
                data, address = s.recvfrom(4096)
                pknt = pknt + 1
                ddata = salsa20_dec(data)
                if len(ddata) > 0 and struct.unpack('i', ddata[0x70:0x70 + 4])[0] > pktid:

                    self.last_data = GT_Data(ddata)
                    self._last_data_received = time.time()

                    pktid = struct.unpack('i', ddata[0x70:0x70 + 4])[0]

                    bstlap = struct.unpack('i', ddata[0x78:0x78 + 4])[0]
                    lstlap = struct.unpack('i', ddata[0x7C:0x7C + 4])[0]
                    curlap = struct.unpack('h', ddata[0x74:0x74 + 2])[0]

                    if curlap == 0:
                        self.session.special_packet_time = 0

                    if curlap > 0 and self.last_data.in_race:

                        if curlap != prevlap:
                            # New lap
                            prevlap = curlap

                            self.session.special_packet_time += lstlap - self.current_lap.LapTicks * 1000.0/60.0

                            self._log_lap()
                            if lstlap > 0:
                                self.laps.insert(0, self.current_lap)

                            self.session.best_lap = bstlap

                            self.current_lap = Lap()
                            self.current_lap.FuelAtStart = self.last_data.current_fuel
                            # trackLap(lstlap, curlap, bstlap)
                    else:
                        curLapTime = 0
                        # Reset lap
                        self.current_lap = Lap()

                    self._log_data(self.last_data)

                    if pknt > 100:
                        self._send_hb(s)
                        pknt = 0
            except Exception as e:
                print(traceback.format_exc())
                self._send_hb(s)
                pknt = 0
                pass

    def is_connected(self) -> bool:
        return self._last_data_received > 0 and (time.time() - self._last_data_received) <= 1

    def get_data_example(self):
        return self.dataExample

    def _send_hb(self, s):
        send_data = 'A'
        s.sendto(send_data.encode('utf-8'), (self.Playstation_IP, self.SendPort))

    def get_last_data(self) -> GT_Data:
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

        if not data.in_race:
            return

        if data.is_paused:
            return

        if data.ride_height < self.session.min_body_height:
            self.session.min_body_height = data.ride_height

        if data.carSpeed > self.session.max_speed:
            self.session.max_speed = data.carSpeed

        if data.throttle == 100:
            self.current_lap.FullThrottleTicks += 1

        if data.brake == 100:
            self.current_lap.FullBrakeTicks += 1

        if data.brake == 0 and data.throttle == 0:
            self.current_lap.NoThrottleNoBrakeTicks += 1
            self.current_lap.DataCoasting.append(1)
        else:
            self.current_lap.DataCoasting.append(0)

        if data.brake > 0 and data.throttle > 0:
            self.current_lap.ThrottleAndBrakesTicks += 1

        self.current_lap.LapTicks += 1

        if data.tyre_temp_FL > 100 or data.tyre_temp_FR > 100 or data.tyre_temp_rl > 100 or data.tyre_temp_rr > 100:
            self.current_lap.TiresOverheatedTicks += 1

        self.current_lap.DataBraking.append(data.brake)
        self.current_lap.DataThrottle.append(data.throttle)
        self.current_lap.DataSpeed.append(data.carSpeed)
        self.current_lap.DataRPM.append(data.rpm)

        deltaDivisor = data.carSpeed
        if data.carSpeed == 0:
            deltaDivisor = 1

        deltaFL = data.tyreSpeedFL / deltaDivisor
        deltaFR = data.tyreSpeedFR / deltaDivisor
        deltaRL = data.tyreSpeedRL / deltaDivisor
        deltaRR = data.tyreSpeedFR / deltaDivisor

        if deltaFL > 1.1 or deltaFR > 1.1 or deltaRL > 1.1 or deltaRR > 1.1:
            self.current_lap.TiresSpinningTicks += 1

        self.current_lap.DataTires.append(deltaFL + deltaFR + deltaRL + deltaRR)

        # if not currentLap.LapTicks % 10 == 0:
        # 	return

        ## Log Position

        self.current_lap.PositionsX.append(data.pos_x)
        self.current_lap.PositionsY.append(data.pos_y)
        self.current_lap.PositionsZ.append(data.pos_z)

        # Adapted from https://www.gtplanet.net/forum/threads/gt7-is-compatible-with-motion-rig.410728/post-13810797
        self.current_lap.LapLiveTime = (self.current_lap.LapTicks * 1./60.) - (self.session.special_packet_time/1000.)

        self.current_lap.DataTime.append(self.current_lap.LapLiveTime)

    def _log_lap(self):
        # Sett info we only now after crossing the line
        self.current_lap.LapTime = self.last_data.last_lap
        self.current_lap.RemainingFuel = self.last_data.current_fuel
        self.current_lap.FuelAtEnd = self.last_data.current_fuel
        self.current_lap.FuelConsumed = self.current_lap.FuelAtStart - self.current_lap.FuelAtEnd
        self.current_lap.LapTime = self.current_lap.LapTime
        self.current_lap.Title = secondsToLaptime(self.current_lap.LapTime / 1000)
        self.current_lap.Number = self.last_data.current_lap - 1  # Is not counting the same way as the time table

    def reset(self):
        self.current_lap = Lap()
        self.session = Session()
        self.last_data = GT_Data(None)
        self.laps = []


# data stream decoding
def salsa20_dec(dat):
    KEY = b'Simulator Interface Packet GT7 ver 0.0'
    # Seed IV is always located here
    oiv = dat[0x40:0x44]
    iv1 = int.from_bytes(oiv, byteorder='little')
    # Notice DEADBEAF, not DEADBEEF
    iv2 = iv1 ^ 0xDEADBEAF
    IV = bytearray()
    IV.extend(iv2.to_bytes(4, 'little'))
    IV.extend(iv1.to_bytes(4, 'little'))
    ddata = Salsa20_xor(dat, bytes(IV), KEY[0:32])
    magic = int.from_bytes(ddata[0:4], byteorder='little')
    if magic != 0x47375330:
        return bytearray(b'')
    return ddata
