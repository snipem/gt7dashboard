from datetime import timedelta
import json
import struct


class GTData:
    def __init__(self, ddata):
        if not ddata:
            ddata = bytearray(0x124 + 4) 

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

        self.tyre_slip_ratio_FL = 0
        self.tyre_slip_ratio_FR = 0
        self.tyre_slip_ratio_RL = 0
        self.tyre_slip_ratio_RR = 0
        
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