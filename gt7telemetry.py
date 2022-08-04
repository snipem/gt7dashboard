import signal
from datetime import datetime as dt
from datetime import timedelta as td
import socket
import sys
import struct
# pip3 install salsa20
from salsa20 import Salsa20_xor

# ansi prefix
pref = "\033["

# ports for send and receive data
SendPort = 33739
ReceivePort = 33740

# ctrl-c handler
def handler(signum, frame):
	sys.stdout.write(f'{pref}?1049l')	# revert buffer
	sys.stdout.write(f'{pref}?25h')		# restore cursor
	sys.stdout.flush()
	exit(1)

# handle ctrl-c
signal.signal(signal.SIGINT, handler)

sys.stdout.write(f'{pref}?1049h')	# alt buffer
sys.stdout.write(f'{pref}?25l')		# hide cursor
sys.stdout.flush()

# get ip address from command line
if len(sys.argv) == 2:
    ip = sys.argv[1]
else:
    print('Run like : python3 gt7telemetry.py <playstation-ip>')
    exit(1)

# Create a UDP socket and bind it
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind(('0.0.0.0', ReceivePort))
s.settimeout(10)

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

# send heartbeat
def send_hb(s):
	send_data = 'A'
	s.sendto(send_data.encode('utf-8'), (ip, SendPort))
	#print('send heartbeat')

import os
showlimited = os.environ.get("GT7_LIMITED")
# generic print function, added with alawaysvisible flag to remain upstream compatability
def printAt(str, row=1, column=1, bold=0, underline=0, reverse=0, alwaysvisible=False):
	global showlimited
	if showlimited and not alwaysvisible:
		return
	elif showlimited:
		# Put everything up
		row = row-40

	sys.stdout.write('{}{};{}H'.format(pref, row, column))
	if reverse:
		sys.stdout.write('{}7m'.format(pref))
	if bold:
		sys.stdout.write('{}1m'.format(pref))
	if underline:
		sys.stdout.write('{}4m'.format(pref))
	if not bold and not underline and not reverse:
		sys.stdout.write('{}0m'.format(pref))
	sys.stdout.write(str)

def secondsToLaptime(seconds):
	remaining = seconds
	minutes = seconds // 60
	remaining = seconds % 60
	return '{:01.0f}:{:06.3f}'.format(minutes, remaining)


from gt7plot import plot_session_analysis, get_best_lap
def raceLog(lstlap, curlap, bestlap):
	# TODO add No Throttle per lap
	# TODO Add heavy breaking and heavy steering
	# TODO Add both throttle and braking pressee
	file_object = open('race.log', 'a')
	global currentLap
	global laps

	if lstlap < 0:
		return

	currentLap.LapTime = lstlap
	currentLap.Title = secondsToLaptime(lstlap / 1000)
	currentLap.Number = curlap - 1  # Is not counting the same way as the time table
	file_object.write('\n %s, %2d, %4dT, %4dB, %4dN' % (
	'{:>9}'.format(currentLap.Title), curlap,
	currentLap.FullThrottleTicks,
	currentLap.FullBrakeTicks,
	currentLap.NoThrottleNoBrakeTicks))
	# Add lap and reset lap
	laps.insert(0, currentLap)
	plot_session_analysis(laps)
	currentLap = Lap()

	printAt(' #  Time        Delta    F    T+B   B    0   Heat   S', 43, 1, underline=1, alwaysvisible=True)

	# Display lap times
	for idx, lap in enumerate(laps):
		lapColor = 39
		timeDiff = '{:>9}'.format("")

		if bestlap == lap.LapTime:
			lapColor = 35
		elif lap.LapTime < bestlap: # LapTime cannot be smaller than bestlap, bestlap is always the smallest. This can only mean that lap.LapTime is from an earlier race on a different track
			timeDiff = '{:^9}'.format("-")
		elif bestlap > 0:
			timeDiff = '{:>9}'.format(secondsToLaptime(-1 * (bestlap / 1000 - lap.LapTime / 1000)))

		printAt('\x1b[1;%dm%2d %1s %1s %4d %4d %4d %4d %4d %4d' % (
		lapColor,
		lap.Number,
		'{:>9}'.format(secondsToLaptime(lap.LapTime / 1000)),
		timeDiff,
		lap.FullThrottleTicks/lap.LapTicks*1000,
		lap.ThrottleAndBrakesTicks/lap.LapTicks*1000,
		lap.FullBrakeTicks/lap.LapTicks*1000,
		lap.NoThrottleNoBrakeTicks/lap.LapTicks*1000,
		lap.TiresOverheatedTicks/lap.LapTicks*1000,
		lap.TiresSpinningTicks/lap.LapTicks*1000
		), 44 + idx, 1, alwaysvisible=True)


minBodyHeight = 9999999
maxSpeed = 0

laps = []


from gt7lap import Lap
currentLap = Lap()


def trackData(ddata):

	global minBodyHeight
	global maxSpeed
	global currentLap

	printAt('{:<100}'.format('Getting Faster'), 41, 1, reverse=1, bold=1, alwaysvisible=True)
	printAt('MaxSpeed/Sess.:            kph', 43, 65, alwaysvisible=True)
	printAt('MinBodyHeight/Sess.:       mm', 44, 65, alwaysvisible=True)
	printAt('Heat Tires Quota/Lap:      ', 45, 65, alwaysvisible=True)
	printAt('Tires Spinning Quota/Lap:  ', 46, 65, alwaysvisible=True)

	printAt('{:6.0f}'.format(maxSpeed), 43, 85, alwaysvisible=True)
	printAt('{:6.0f}'.format(minBodyHeight), 44, 85, alwaysvisible=True)
	printAt('{:6.0f}'.format(currentLap.TiresOverheatedTicks/currentLap.LapTicks*1000), 45, 85, alwaysvisible=True)
	printAt('{:6.0f}'.format(currentLap.TiresSpinningTicks/currentLap.LapTicks*1000), 46, 85, alwaysvisible=True)

	isPaused = bin(struct.unpack('B', ddata[0x8E:0x8E+1])[0])[-2] == '1'

	if isPaused:
		return

	currentBodyHeight = 1000 * struct.unpack('f', ddata[0x38:0x38 + 4])[0]
	currentSpeed = 3.6 * struct.unpack('f', ddata[0x4C:0x4C + 4])[0]

	currentThrottle = struct.unpack('B', ddata[0x91:0x91 + 1])[0] / 2.55
	currentBrake = struct.unpack('B', ddata[0x92:0x92 + 1])[0] / 2.55

	if currentBodyHeight < minBodyHeight:
		minBodyHeight = currentBodyHeight

	if currentSpeed > maxSpeed:
		maxSpeed = currentSpeed

	if currentThrottle == 100:
		currentLap.FullThrottleTicks += 1

	if currentBrake == 100:
		currentLap.FullBrakeTicks += 1

	if currentBrake == 0 and currentThrottle == 0:
		currentLap.NoThrottleNoBrakeTicks += 1

	if currentBrake > 0 and currentThrottle > 0:
		currentLap.ThrottleAndBrakesTicks += 1

	currentLap.LapTicks += 1

	fl_tire_temp = struct.unpack('f', ddata[0x60:0x60+4])[0]
	fr_tire_temp = struct.unpack('f', ddata[0x64:0x64+4])[0]

	rl_tire_temp = struct.unpack('f', ddata[0x68:0x68+4])[0]
	rr_tire_temp = struct.unpack('f', ddata[0x6C:0x6C+4])[0]

	if fl_tire_temp > 100 or fr_tire_temp > 100 or rl_tire_temp > 100 or rr_tire_temp > 100:
		currentLap.TiresOverheatedTicks += 1

	global deltaFL
	global deltaFR
	global deltaRL
	global deltaRR
	global carSpeed

	currentLap.DataBraking.append(currentBrake)
	currentLap.DataThrottle.append(currentThrottle)
	currentLap.DataSpeed.append(carSpeed)

	if carSpeed > 0:
		deltaFL = tyreSpeedFL / carSpeed
		deltaFR = tyreSpeedFR / carSpeed
		deltaRL = tyreSpeedRL / carSpeed
		deltaRR = tyreSpeedRR / carSpeed

		if deltaFL > 1.1 or deltaFR > 1.1 or deltaRL > 1.1 or deltaRR > 1.1:
			currentLap.TiresSpinningTicks += 1

	# if not currentLap.LapTicks % 10 == 0:
	# 	return

	## Log Position
	x = struct.unpack('f', ddata[0x04:0x04+4])[0]
	y = struct.unpack('f', ddata[0x08:0x08+4])[0]
	z = struct.unpack('f', ddata[0x0C:0x0C+4])[0]

	currentLap.PositionsX.append(x)
	currentLap.PositionsY.append(y)
	currentLap.PositionsZ.append(z)


# start by sending heartbeat
send_hb(s)

printAt('GT7 Telemetry Display 0.7 (ctrl-c to quit)', 1, 1, bold=1)
printAt('Packet ID:', 1, 73)

printAt('{:<92}'.format('Current Track Data'), 3, 1, reverse=1, bold=1)
printAt('Time on track:', 3, 41, reverse=1)
printAt('Laps:    /', 5, 1)
printAt('Position:   /', 5, 21)
printAt('Best Lap Time:', 7, 1)
printAt('Current Lap Time: ', 7, 31)
printAt('Last Lap Time:', 8, 1)

printAt('{:<92}'.format('Current Car Data'), 10, 1, reverse=1, bold=1)
printAt('Car ID:', 10, 41, reverse=1)
printAt('Throttle:    %', 12, 1)
printAt('RPM:        rpm', 12, 21)
printAt('Speed:        kph', 12, 41)
printAt('Brake:       %', 13, 1)
printAt('Gear:   ( )', 13, 21)
printAt('Boost:        kPa', 13, 41)
printAt('Rev Warning       rpm', 12, 71)
printAt('Rev Limiter       rpm', 13, 71)
printAt('Max:', 14, 21)
printAt('Est. Speed        kph', 14, 71)

printAt('Clutch:       /', 15, 1)
printAt('RPM After Clutch:        rpm', 15, 31)

printAt('Oil Temperature:       °C', 17, 1)
printAt('Water Temperature:       °C', 17, 31)
printAt('Oil Pressure:          bar', 18, 1)
printAt('Body/Ride Height:        mm', 18, 31)

printAt('Tyre Data', 20, 1, underline=1)
printAt('FL:        °C', 21, 1)
printAt('FR:        °C', 21, 21)
printAt('ø:      /       cm', 21, 41)
printAt('           kph', 22, 1)
printAt('           kph', 22, 21)
printAt('Δ:      /       ', 22, 41)
printAt('RL:        °C', 25, 1)
printAt('RR:        °C', 25, 21)
printAt('ø:      /       cm', 25, 41)
printAt('           kph', 26, 1)
printAt('           kph', 26, 21)
printAt('Δ:      /       ', 26, 41)

printAt('Gearing', 29, 1, underline=1)
printAt('1st:', 30, 1)
printAt('2nd:', 31, 1)
printAt('3rd:', 32, 1)
printAt('4th:', 33, 1)
printAt('5th:', 34, 1)
printAt('6th:', 35, 1)
printAt('7th:', 36, 1)
printAt('8th:', 37, 1)
printAt('???:', 39, 1)

printAt('Positioning (m)', 29, 21, underline=1)
printAt('X:', 30, 21)
printAt('Y:', 31, 21)
printAt('Z:', 32, 21)

printAt('Velocity (m/s)', 29, 41, underline=1)
printAt('X:', 30, 41)
printAt('Y:', 31, 41)
printAt('Z:', 32, 41)

printAt('Rotation', 34, 21, underline=1)
printAt('P:', 35, 21)
printAt('Y:', 36, 21)
printAt('R:', 37, 21)

printAt('Angular (r/s)', 34, 41, underline=1)
printAt('X:', 35, 41)
printAt('Y:', 36, 41)
printAt('Z:', 37, 41)

printAt('N/S:', 39, 21)

sys.stdout.flush()

prevlap = -1
pktid = 0
pknt = 0
while True:
	try:
		data, address = s.recvfrom(4096)
		pknt = pknt + 1
		ddata = salsa20_dec(data)
		if len(ddata) > 0 and struct.unpack('i', ddata[0x70:0x70+4])[0] > pktid:
			pktid = struct.unpack('i', ddata[0x70:0x70+4])[0]

			bstlap = struct.unpack('i', ddata[0x78:0x78+4])[0]
			lstlap = struct.unpack('i', ddata[0x7C:0x7C+4])[0]
			curlap = struct.unpack('h', ddata[0x74:0x74+2])[0]
			if curlap > 0:
				dt_now = dt.now()
				if curlap != prevlap:
					# New lap
					prevlap = curlap
					dt_start = dt_now
					raceLog(lstlap, curlap, bstlap)
				curLapTime = dt_now - dt_start
				printAt('{:>9}'.format(secondsToLaptime(curLapTime.total_seconds())), 7, 49)
			else:
				curLapTime = 0
				printAt('{:>9}'.format(''), 7, 49)

			cgear = struct.unpack('B', ddata[0x90:0x90+1])[0] & 0b00001111
			sgear = struct.unpack('B', ddata[0x90:0x90+1])[0] >> 4
			if cgear < 1:
				cgear = 'R'
			if sgear > 14:
				sgear = '–'

			fuelCapacity = struct.unpack('f', ddata[0x48:0x48+4])[0]
			isEV = False if fuelCapacity > 0 else True
			if isEV:
				printAt('Charge:', 14, 1)
				printAt('{:3.0f} kWh'.format(struct.unpack('f', ddata[0x44:0x44+4])[0]), 14, 11)		# charge remaining
				printAt('??? kWh'.format(struct.unpack('f', ddata[0x48:0x48+4])[0]), 14, 29)			# max battery capacity
			else:
				printAt('Fuel:  ', 14, 1)
				printAt('{:3.0f} lit'.format(struct.unpack('f', ddata[0x44:0x44+4])[0]), 14, 11)		# fuel
				printAt('{:3.0f} lit'.format(struct.unpack('f', ddata[0x48:0x48+4])[0]), 14, 29)		# max fuel

			boost = struct.unpack('f', ddata[0x50:0x50+4])[0] - 1
			hasTurbo = True if boost > -1 else False


			tyreDiamFL = struct.unpack('f', ddata[0xB4:0xB4+4])[0]
			tyreDiamFR = struct.unpack('f', ddata[0xB8:0xB8+4])[0]
			tyreDiamRL = struct.unpack('f', ddata[0xBC:0xBC+4])[0]
			tyreDiamRR = struct.unpack('f', ddata[0xC0:0xC0+4])[0]

			tyreSpeedFL = abs(3.6 * tyreDiamFL * struct.unpack('f', ddata[0xA4:0xA4+4])[0])
			tyreSpeedFR = abs(3.6 * tyreDiamFR * struct.unpack('f', ddata[0xA8:0xA8+4])[0])
			tyreSpeedRL = abs(3.6 * tyreDiamRL * struct.unpack('f', ddata[0xAC:0xAC+4])[0])
			tyreSpeedRR = abs(3.6 * tyreDiamRR * struct.unpack('f', ddata[0xB0:0xB0+4])[0])

			carSpeed = 3.6 * struct.unpack('f', ddata[0x4C:0x4C+4])[0]

			if carSpeed > 0:
				tyreSlipRatioFL = '{:6.2f}'.format(tyreSpeedFL / carSpeed)
				tyreSlipRatioFR = '{:6.2f}'.format(tyreSpeedFR / carSpeed)
				tyreSlipRatioRL = '{:6.2f}'.format(tyreSpeedRL / carSpeed)
				tyreSlipRatioRR = '{:6.2f}'.format(tyreSpeedRR / carSpeed)
			else:
				tyreSlipRatioFL = '  –  '
				tyreSlipRatioFR = '  –  '
				tyreSlipRatioRL = '  -  '
				tyreSlipRatioRR = '  –  '

			printAt('{:>8}'.format(str(td(seconds=round(struct.unpack('i', ddata[0x80:0x80+4])[0] / 1000)))), 3, 56, reverse=1)	# time of day on track

			printAt('{:3.0f}'.format(curlap), 5, 7)															# current lap
			printAt('{:3.0f}'.format(struct.unpack('h', ddata[0x76:0x76+2])[0]), 5, 11)						# total laps

			printAt('{:2.0f}'.format(struct.unpack('h', ddata[0x84:0x84+2])[0]), 5, 31)						# current position
			printAt('{:2.0f}'.format(struct.unpack('h', ddata[0x86:0x86+2])[0]), 5, 34)						# total positions

			if bstlap != -1:
				printAt('{:>9}'.format(secondsToLaptime(bstlap / 1000)), 7, 16)		# best lap time
			else:
				printAt('{:>9}'.format(''), 7, 16)
			if lstlap != -1:
				printAt('{:>9}'.format(secondsToLaptime(lstlap / 1000)), 8, 16)		# last lap time
			else:
				printAt('{:>9}'.format(''), 8, 16)

			printAt('{:5.0f}'.format(struct.unpack('i', ddata[0x124:0x124+4])[0]), 10, 48, reverse=1)		# car id

			printAt('{:3.0f}'.format(struct.unpack('B', ddata[0x91:0x91+1])[0] / 2.55), 12, 11)				# throttle
			printAt('{:7.0f}'.format(struct.unpack('f', ddata[0x3C:0x3C+4])[0]), 12, 25)					# rpm
			printAt('{:7.1f}'.format(carSpeed), 12, 47)														# speed kph
			printAt('{:5.0f}'.format(struct.unpack('H', ddata[0x88:0x88+2])[0]), 12, 83)					# rpm rev warning

			printAt('{:3.0f}'.format(struct.unpack('B', ddata[0x92:0x92+1])[0] / 2.55), 13, 11)				# brake
			printAt('{}'.format(cgear), 13, 27)																# actual gear
			printAt('{}'.format(sgear), 13, 30)																# suggested gear

			if hasTurbo:
				printAt('{:7.2f}'.format(struct.unpack('f', ddata[0x50:0x50+4])[0] - 1), 13, 47)			# boost
			else:
				printAt('{:>7}'.format('–'), 13, 47)														# no turbo

			printAt('{:5.0f}'.format(struct.unpack('H', ddata[0x8A:0x8A+2])[0]), 13, 83)					# rpm rev limiter

			printAt('{:5.0f}'.format(struct.unpack('h', ddata[0x8C:0x8C+2])[0]), 14, 83)					# estimated top speed

			printAt('{:5.3f}'.format(struct.unpack('f', ddata[0xF4:0xF4+4])[0]), 15, 9)						# clutch
			printAt('{:5.3f}'.format(struct.unpack('f', ddata[0xF8:0xF8+4])[0]), 15, 17)					# clutch engaged
			printAt('{:7.0f}'.format(struct.unpack('f', ddata[0xFC:0xFC+4])[0]), 15, 48)					# rpm after clutch

			printAt('{:6.1f}'.format(struct.unpack('f', ddata[0x5C:0x5C+4])[0]), 17, 17)					# oil temp
			printAt('{:6.1f}'.format(struct.unpack('f', ddata[0x58:0x58+4])[0]), 17, 49)					# water temp

			printAt('{:6.2f}'.format(struct.unpack('f', ddata[0x54:0x54+4])[0]), 18, 17)					# oil pressure
			printAt('{:6.0f}'.format(1000 * struct.unpack('f', ddata[0x38:0x38+4])[0]), 18, 49)				# ride height

			printAt('{:6.1f}'.format(struct.unpack('f', ddata[0x60:0x60+4])[0]), 21, 5)						# tyre temp FL
			printAt('{:6.1f}'.format(struct.unpack('f', ddata[0x64:0x64+4])[0]), 21, 25)					# tyre temp FR
			printAt('{:6.1f}'.format(200 * tyreDiamFL), 21, 43)												# tyre diameter FL
			printAt('{:6.1f}'.format(200 * tyreDiamFR), 21, 50)												# tyre diameter FR

			printAt('{:6.1f}'.format(tyreSpeedFL), 22, 5)													# tyre speed FL
			printAt('{:6.1f}'.format(tyreSpeedFR), 22, 25)													# tyre speed FR
			printAt(tyreSlipRatioFL, 22, 43)																# tyre slip ratio FL
			printAt(tyreSlipRatioFR, 22, 50)																# tyre slip ratio FR

			printAt('{:6.3f}'.format(struct.unpack('f', ddata[0xC4:0xC4+4])[0]), 23, 5)						# suspension FL
			printAt('{:6.3f}'.format(struct.unpack('f', ddata[0xC8:0xC8+4])[0]), 23, 25)					# suspension FR

			printAt('{:6.1f}'.format(struct.unpack('f', ddata[0x68:0x68+4])[0]), 25, 5)						# tyre temp RL
			printAt('{:6.1f}'.format(struct.unpack('f', ddata[0x6C:0x6C+4])[0]), 25, 25)					# tyre temp RR
			printAt('{:6.1f}'.format(200 * tyreDiamRL), 25, 43)												# tyre diameter RL
			printAt('{:6.1f}'.format(200 * tyreDiamRR), 25, 50)												# tyre diameter RR

			printAt('{:6.1f}'.format(tyreSpeedRL), 26, 5)													# tyre speed RL
			printAt('{:6.1f}'.format(tyreSpeedRR), 26, 25)													# tyre speed RR
			printAt(tyreSlipRatioRL, 26, 43)																# tyre slip ratio RL
			printAt(tyreSlipRatioRR, 26, 50)																# tyre slip ratio RR

			printAt('{:6.3f}'.format(struct.unpack('f', ddata[0xCC:0xCC+4])[0]), 27, 5)						# suspension RL
			printAt('{:6.3f}'.format(struct.unpack('f', ddata[0xD0:0xD0+4])[0]), 27, 25)					# suspension RR

			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x104:0x104+4])[0]), 30, 5)					# 1st gear
			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x108:0x108+4])[0]), 31, 5)					# 2nd gear
			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x10C:0x10C+4])[0]), 32, 5)					# 3rd gear
			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x110:0x110+4])[0]), 33, 5)					# 4th gear
			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x114:0x114+4])[0]), 34, 5)					# 5th gear
			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x118:0x118+4])[0]), 35, 5)					# 6th gear
			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x11C:0x11C+4])[0]), 36, 5)					# 7th gear
			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x120:0x120+4])[0]), 37, 5)					# 8th gear

			printAt('{:7.3f}'.format(struct.unpack('f', ddata[0x100:0x100+4])[0]), 39, 5)					# ??? gear

			printAt('{:11.4f}'.format(struct.unpack('f', ddata[0x04:0x04+4])[0]), 30, 23)					# pos X
			printAt('{:11.4f}'.format(struct.unpack('f', ddata[0x08:0x08+4])[0]), 31, 23)					# pos Y
			printAt('{:11.4f}'.format(struct.unpack('f', ddata[0x0C:0x0C+4])[0]), 32, 23)					# pos Z

			printAt('{:11.4f}'.format(struct.unpack('f', ddata[0x10:0x10+4])[0]), 30, 43)					# velocity X
			printAt('{:11.4f}'.format(struct.unpack('f', ddata[0x14:0x14+4])[0]), 31, 43)					# velocity Y
			printAt('{:11.4f}'.format(struct.unpack('f', ddata[0x18:0x18+4])[0]), 32, 43)					# velocity Z

			printAt('{:9.4f}'.format(struct.unpack('f', ddata[0x1C:0x1C+4])[0]), 35, 23)					# rot Pitch
			printAt('{:9.4f}'.format(struct.unpack('f', ddata[0x20:0x20+4])[0]), 36, 23)					# rot Yaw
			printAt('{:9.4f}'.format(struct.unpack('f', ddata[0x24:0x24+4])[0]), 37, 23)					# rot Roll

			printAt('{:9.4f}'.format(struct.unpack('f', ddata[0x2C:0x2C+4])[0]), 35, 43)					# angular velocity X
			printAt('{:9.4f}'.format(struct.unpack('f', ddata[0x30:0x30+4])[0]), 36, 43)					# angular velocity Y
			printAt('{:9.4f}'.format(struct.unpack('f', ddata[0x34:0x34+4])[0]), 37, 43)					# angular velocity Z

			printAt('{:7.4f}'.format(struct.unpack('f', ddata[0x28:0x28+4])[0]), 39, 25)					# rot ???

			printAt('0x8E BITS  =  {:0>8}'.format(bin(struct.unpack('B', ddata[0x8E:0x8E+1])[0])[2:]), 23, 71)	# various flags (see https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketG7S0.cs)
			printAt('0x8F BITS  =  {:0>8}'.format(bin(struct.unpack('B', ddata[0x8F:0x8F+1])[0])[2:]), 24, 71)	# various flags (see https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketG7S0.cs)
			printAt('0x93 BITS  =  {:0>8}'.format(bin(struct.unpack('B', ddata[0x93:0x93+1])[0])[2:]), 25, 71)	# 0x93 = ???

			printAt('0x94 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0x94:0x94+4])[0]), 27, 71)			# 0x94 = ???
			printAt('0x98 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0x98:0x98+4])[0]), 28, 71)			# 0x98 = ???
			printAt('0x9C FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0x9C:0x9C+4])[0]), 29, 71)			# 0x9C = ???
			printAt('0xA0 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xA0:0xA0+4])[0]), 30, 71)			# 0xA0 = ???

			printAt('0xD4 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xD4:0xD4+4])[0]), 32, 71)			# 0xD4 = ???
			printAt('0xD8 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xD8:0xD8+4])[0]), 33, 71)			# 0xD8 = ???
			printAt('0xDC FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xDC:0xDC+4])[0]), 34, 71)			# 0xDC = ???
			printAt('0xE0 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xE0:0xE0+4])[0]), 35, 71)			# 0xE0 = ???

			printAt('0xE4 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xE4:0xE4+4])[0]), 36, 71)			# 0xE4 = ???
			printAt('0xE8 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xE8:0xE8+4])[0]), 37, 71)			# 0xE8 = ???
			printAt('0xEC FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xEC:0xEC+4])[0]), 38, 71)			# 0xEC = ???
			printAt('0xF0 FLOAT {:11.5f}'.format(struct.unpack('f', ddata[0xF0:0xF0+4])[0]), 39, 71)			# 0xF0 = ???

			printAt('{:>10}'.format(pktid), 1, 83)						# packet id

			trackData(ddata)

		if pknt > 100:
			send_hb(s)
			pknt = 0
	except Exception as e:
		printAt('Exception: {}'.format(e), 41, 1, reverse=1)
		send_hb(s)
		pknt = 0
		pass

	sys.stdout.flush()
