import serial
import base64
import hashlib
import re
from tqdm import tqdm
import binascii


def main():
    ROM_SIZE = 16 * 1024 * 1024
    print('connecting to serial port...')
    ser = serial.Serial('COM4')
    print('connected')
    print('read rom header')
    raw_header = dump_header(ser)
    print(binascii.hexlify(raw_header))
    header = Header(raw_header)
    print(header)
    print('ROM header received')
    print('dump rom data')
    rom_data = dump_rom(ser, ROM_SIZE)
    print('ROM data received')
    md5 = hashlib.md5(rom_data).hexdigest()
    print(f'MD5 is {md5}')
    print('writing rom data to file...')
    title = re.sub('[^a-zA-Z0-9]', '_', header.title)
    with open(f'{title}.gba', 'wb') as f:
        f.write(rom_data)
    print('done')


class Header:
    def __init__(self, data):
        self.title = data[160:172].decode('ascii').strip('\x00')
        self.game_code = data[172:176].decode('ascii').strip('\x00')

    def __str__(self):
        return f'Title: {self.title}, Game Code: {self.game_code}'


def dump_rom(ser: serial, rom_size: int):
    start_addr = 0
    ser.write(f'dump 0x{start_addr:06x} {rom_size}\n'.encode('ascii'))
    rom_data = receive(ser, rom_size, show_progress=True)
    return rom_data


def dump_header(ser: serial):
    header_addr = 0
    size = 192
    ser.write(f'dump 0x{header_addr:06x} {size}\n'.encode('ascii'))
    header_data = receive(ser, size)
    return header_data


def receive(ser: serial, size: int, show_progress: bool = False) -> bytes:
    data = bytearray()
    bar = tqdm(total=size, unit='B', unit_scale=True, disable=not show_progress)
    while True:
        line = ser.readline()
        if line == b'done\r\n':
            break
        elif line.strip().isdigit():
            chunk = read_data(ser, line)
            bar.update(len(chunk))
            data += chunk
        elif line == b'wait\r\n':
            print('wait')
        else:
            # print('client> ' + line.decode('ascii'), end='')
            pass
    return data


def read_data(ser: serial, size_str: str) -> bytes:
    size = int(size_str)
    b64_data = ser.read(size + 1)  # converted \n -> \r\n in serial port
    return base64.b64decode(b64_data)


if __name__ == '__main__':
    main()
