import signal
import datetime
import socket
import sys
import struct
# pip3 install salsa20
from salsa20 import Salsa20_xor

pref = "\033["


def handler(signum, frame):
    print(f'{pref}?1049l')
    exit(1)

signal.signal(signal.SIGINT, handler)

print(f'{pref}?1049h')

#https://github.com/Nenkai/PDTools/blob/master/SimulatorInterface/SimulatorInterface.cs

ReceivePort = 33740
SendPort = 33739

if len(sys.argv) == 2:
    # Get "IP address of Server" and also the "port number" from
    ip = sys.argv[1]
else:
    print("Run like : python3 gt7racedata.py <playstation-ip>")
    exit(1)

# Create a UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = ('0.0.0.0', ReceivePort)
s.bind(server_address)
s.settimeout(10)

#https://github.com/Nenkai/PDTools/blob/master/PDTools.Crypto/SimulationInterface/SimulatorInterfaceCryptorGT7.cs
def salsa20_dec(dat):
  KEY = b'Simulator Interface Packet GT7 ver 0.0'
  oiv = dat[0x40:0x44]
  iv1 = int.from_bytes(oiv, byteorder='little') # Seed IV is always located there
  iv2 = iv1 ^ 0xDEADBEAF #// Notice DEADBEAF, not DEADBEEF
  """
  print("OIV: %d bytes" % len(oiv))
  print(' '.join(format(x, '02x') for x in oiv))
  print("IV1: %d bytes" % len(iv1.to_bytes(4, 'big')))
  print(' '.join(format(x, '02x') for x in iv1.to_bytes(4, 'big')))
  print("IV2: %d bytes" % len(iv2.to_bytes(4, 'big')))
  print(' '.join(format(x, '02x') for x in iv2.to_bytes(4, 'big')))
  """
  IV = bytearray()
  IV.extend(iv2.to_bytes(4, 'little'))
  IV.extend(iv1.to_bytes(4, 'little'))
  #print("IV: %d bytes" % len(IV))
  #print(' '.join(format(x, '02x') for x in IV))
  """
  // Magic should be "G7S0" when decrypted
  SpanReader sr = new SpanReader(data);
  int magic = sr.ReadInt32();
  if (magic != 0x47375330) // 0S7G - G7S0
  """
  ddata = Salsa20_xor(dat, bytes(IV), KEY[0:32])#.decode()
  #check magic number
  magic = int.from_bytes(ddata[0:4], byteorder='little')
  if magic != 0x47375330:
    return bytearray(b'')
  return ddata

def send_hb(s):
  #send HB
  send_data = 'A'
  s.sendto(send_data.encode('utf-8'), (ip, SendPort))
  #print('send heartbeat')

def printData(row,label,value,column=1):
	print('{}{};{}H{:<10}:{:>10}'.format(pref,row,column,label,value))

send_hb(s)

print('{}40;1HCtrl+C to exit the program'.format(pref))

pknt = 0
while True:
  try:
    data, address = s.recvfrom(4096)
    pknt = pknt + 1
    ddata = salsa20_dec(data)
    if len(ddata) > 0:

      #https://github.com/Nenkai/PDTools/blob/master/PDTools.SimulatorInterface/SimulatorPacketGT7.cs

      printData(1,'Car ID',struct.unpack('i', ddata[0x124:0x124+4])[0])
      printData(1,'Ticks',struct.unpack('i', ddata[0x70:0x70+4])[0], column=30)
      printData(1,'Time',str(datetime.timedelta(seconds=round(struct.unpack('i', ddata[0x80:0x80+4])[0] / 1000))), column=60)

      printData(2,'RPM',round(struct.unpack('f', ddata[0x3C:0x3C+4])[0]))
      printData(2,'Speed km/h','{:.1f}'.format(60 * 60 * struct.unpack('f', ddata[0x4C:0x4C+4])[0] / 1000), column=30)

      printData(3,'Throttle',struct.unpack('B', ddata[0x91:0x91+1])[0])
      printData(3,'Brake',struct.unpack('B', ddata[0x92:0x92+1])[0], column=30)

      printData(4,'Best lap','{:.3f}'.format(struct.unpack('i', ddata[0x78:0x78+4])[0] / 1000))
      printData(4,'Last lap','{:.3f}'.format(struct.unpack('i', ddata[0x7C:0x7C+4])[0] / 1000), column=30)

      printData(5,'Gear',struct.unpack('B', ddata[0x90:0x90+1])[0] & 0b00001111)
      printData(5,'Suggested',struct.unpack('B', ddata[0x90:0x90+1])[0] >> 4, column=30)

      printData(6,'Lap',struct.unpack('h', ddata[0x74:0x74+2])[0])
      printData(6,'Race laps',struct.unpack('h', ddata[0x76:0x76+2])[0], column=30)

      printData(7,'Race pos',struct.unpack('h', ddata[0x84:0x84+2])[0])
      printData(7,'Total',struct.unpack('h', ddata[0x86:0x86+2])[0], column=30)

      printData(8,'Boost',round(struct.unpack('f', ddata[0x50:0x50+4])[0] - 1, 2))
      printData(8,'Oil Pr',struct.unpack('f', ddata[0x54:0x54+4])[0], column=30)
      printData(8,'Oil Temp',struct.unpack('f', ddata[0x5C:0x5C+4])[0], column=60)
      printData(9,'Water Temp',struct.unpack('f', ddata[0x58:0x58+4])[0], column=60)

      printData(9,'Ride Ht',round(struct.unpack('f', ddata[0x38:0x38+4])[0]))

      printData(10,'Temp LF','{:.1f}'.format(struct.unpack('f', ddata[0x60:0x60+4])[0]))
      printData(10,'Temp RF','{:.1f}'.format(struct.unpack('f', ddata[0x64:0x64+4])[0]), column=30)
      printData(11,'Temp LR','{:.1f}'.format(struct.unpack('f', ddata[0x68:0x68+4])[0]))
      printData(11,'Temp RR','{:.1f}'.format(struct.unpack('f', ddata[0x6C:0x6C+4])[0]), column=30)

      printData(12,'WhSp LF','{:.1f}'.format(-1 * 60 * 60 * struct.unpack('f', ddata[0xB4:0xB4+4])[0] * struct.unpack('f', ddata[0xA4:0xA4+4])[0] / 1000))
      printData(12,'WhSp RF','{:.1f}'.format(-1 * 60 * 60 * struct.unpack('f', ddata[0xB8:0xB8+4])[0] * struct.unpack('f', ddata[0xA8:0xA8+4])[0] / 1000), column=30)
      printData(13,'WhSp LR','{:.1f}'.format(-1 * 60 * 60 * struct.unpack('f', ddata[0xBC:0xBC+4])[0] * struct.unpack('f', ddata[0xAC:0xAC+4])[0] / 1000))
      printData(13,'WhSp RR','{:.1f}'.format(-1 * 60 * 60 * struct.unpack('f', ddata[0xC0:0xC0+4])[0] * struct.unpack('f', ddata[0xB0:0xB0+4])[0] / 1000), column=30)

      printData(14,'TiRa LF','{:.3f}'.format(struct.unpack('f', ddata[0xb4:0xB4+4])[0]))
      printData(14,'TiRa RF','{:.3f}'.format(struct.unpack('f', ddata[0xB8:0xB8+4])[0]), column=30)
      printData(15,'TiRa LR','{:.3f}'.format(struct.unpack('f', ddata[0xBC:0xBC+4])[0]))
      printData(15,'TiRa RR','{:.3f}'.format(struct.unpack('f', ddata[0xC0:0xC0+4])[0]), column=30)

      printData(17,'Susp LF','{:.3f}'.format(struct.unpack('f', ddata[0xC4:0xC4+4])[0]))
      printData(17,'Susp RF','{:.3f}'.format(struct.unpack('f', ddata[0xC8:0xC8+4])[0]), column=30)
      printData(18,'Susp LR','{:.3f}'.format(struct.unpack('f', ddata[0xCC:0xCC+4])[0]))
      printData(18,'Susp RR','{:.3f}'.format(struct.unpack('f', ddata[0xD0:0xD0+4])[0]), column=30)

      printData(20,'Clutch','{:.3f}'.format(struct.unpack('f', ddata[0xF4:0xF4+4])[0]))
      printData(20,'Clutch Eng','{:.3f}'.format(struct.unpack('f', ddata[0xF8:0xF8+4])[0]), column=30)
      printData(20,'Clutch RPM','{:.3f}'.format(struct.unpack('f', ddata[0xFC:0xFC+4])[0]), column=60)

      printData(4,'1st Gear','{:.3f}'.format(struct.unpack('f', ddata[0x104:0x104+4])[0]), column=90)
      printData(5,'2nd Gear','{:.3f}'.format(struct.unpack('f', ddata[0x108:0x108+4])[0]), column=90)
      printData(6,'3rd Gear','{:.3f}'.format(struct.unpack('f', ddata[0x10C:0x10C+4])[0]), column=90)
      printData(7,'4th Gear','{:.3f}'.format(struct.unpack('f', ddata[0x110:0x110+4])[0]), column=90)
      printData(8,'5th Gear','{:.3f}'.format(struct.unpack('f', ddata[0x114:0x114+4])[0]), column=90)
      printData(9,'6th Gear','{:.3f}'.format(struct.unpack('f', ddata[0x118:0x118+4])[0]), column=90)
      printData(10,'7th Gear','{:.3f}'.format(struct.unpack('f', ddata[0x11C:0x11C+4])[0]), column=90)
      printData(11,'8th Gear','{:.3f}'.format(struct.unpack('f', ddata[0x120:0x120+4])[0]), column=90)
      printData(12,'Gear ???','{:.3f}'.format(struct.unpack('f', ddata[0x100:0x100+4])[0]), column=90)

      printData(24,'Pos X','{:.3f}'.format(struct.unpack('f', ddata[0x04:0x04+4])[0]))
      printData(24,'Pos Y','{:.3f}'.format(struct.unpack('f', ddata[0x08:0x08+4])[0]), column=30)
      printData(24,'Pos Z','{:.3f}'.format(struct.unpack('f', ddata[0x0C:0x0C+4])[0]), column=60)

      printData(25,'Velocity X','{:.3f}'.format(struct.unpack('f', ddata[0x10:0x10+4])[0]))
      printData(25,'Velocity Y','{:.3f}'.format(struct.unpack('f', ddata[0x14:0x14+4])[0]), column=30)
      printData(25,'Velocity Z','{:.3f}'.format(struct.unpack('f', ddata[0x18:0x18+4])[0]), column=60)

      printData(26,'Rotation X','{:.3f}'.format(struct.unpack('f', ddata[0x1C:0x1C+4])[0]))
      printData(26,'Rotation Y','{:.3f}'.format(struct.unpack('f', ddata[0x20:0x20+4])[0]), column=30)
      printData(26,'Rotation Z','{:.3f}'.format(struct.unpack('f', ddata[0x24:0x24+4])[0]), column=60)
      printData(26,'Rot N/S','{:.3f}'.format(struct.unpack('f', ddata[0x28:0x28+4])[0]), column=90)

      printData(27,'Angular X','{:.3f}'.format(struct.unpack('f', ddata[0x2C:0x2C+4])[0]))
      printData(27,'Angular Y','{:.3f}'.format(struct.unpack('f', ddata[0x30:0x30+4])[0]), column=30)
      printData(27,'Angular Z','{:.3f}'.format(struct.unpack('f', ddata[0x34:0x34+4])[0]), column=60)

      printData(31,'0x48 FLOAT',struct.unpack('f', ddata[0x48:0x48+4])[0])
      printData(34,'0x88 SHORT',struct.unpack('h', ddata[0x88:0x88+2])[0])
      printData(35,'0x8A SHORT',struct.unpack('h', ddata[0x8A:0x8A+2])[0])
      printData(36,'0x8C SHORT',struct.unpack('h', ddata[0x8C:0x8C+2])[0])
      printData(37,'0x8E BITS',bin(struct.unpack('B', ddata[0x8E:0x8E+1])[0]))
      printData(37,'0x8F BITS',bin(struct.unpack('B', ddata[0x8F:0x8F+1])[0]), column=30)
      printData(38,'0x93 BITS',bin(struct.unpack('B', ddata[0x93:0x93+1])[0]))

      printData(31,'0x94 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0x94:0x94+4])[0]), column=30)
      printData(32,'0x98 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0x98:0x98+4])[0]), column=30)
      printData(33,'0x9C FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0x9C:0x9C+4])[0]), column=30)
      printData(34,'0xA0 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xA0:0xA0+4])[0]), column=30)

      printData(31,'0xD4 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xD4:0xD4+4])[0]), column=60)
      printData(32,'0xD8 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xD8:0xD8+4])[0]), column=60)
      printData(33,'0xDC FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xDC:0xDC+4])[0]), column=60)
      printData(34,'0xE0 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xE0:0xE0+4])[0]), column=60)

      printData(31,'0xE4 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xE4:0xE4+4])[0]), column=90)
      printData(32,'0xE8 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xE8:0xE8+4])[0]), column=90)
      printData(33,'0xEC FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xEC:0xEC+4])[0]), column=90)
      printData(34,'0xF0 FLOAT','{:.5f}'.format(struct.unpack('f', ddata[0xF0:0xF0+4])[0]), column=90)

    if pknt > 100:
      send_hb(s)
      pknt = 0
  except Exception as e:
    printData(41, 'Exception', e)
    send_hb(s)
    pknt = 0
    pass

