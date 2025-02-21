import time
import sys
import ubinascii

import rp2
from machine import Pin


# GPIO pins on the GBA cartridge connector
# /CS = 26
# /RD = 27
# AD0...A23 = 0...23
class Dumper:
    BUFFER_SIZE = 1024 * 16

    def __init__(self):
        # init unused pins
        Pin(28, Pin.OUT, value=1)  # /WR
        Pin(24, Pin.OUT, value=1)  # /CS2
        Pin(25, Pin.OUT, value=0)  # IRQ

        # init used pins
        self.cs = Pin(26, Pin.OUT, value=1)
        self.rd = Pin(27, Pin.OUT, value=1)
        self.data_pins = []
        for pin in range(16):
            self.data_pins.append(Pin(pin, Pin.OUT, value=0))
        self.addr_pins = []
        for pin in range(16, 24):
            self.addr_pins.append(Pin(pin, Pin.OUT, value=0))

        # init PIO state machine and DMA
        self.sm = rp2.StateMachine(
            0,
            self._pio_read_data,
            freq=125_000_000,
            in_base=self.data_pins[0],  # 16 bit
            out_base=self.data_pins[0],  # 24 bit
            set_base=self.cs  # use CS and RD
        )
        self.dma = rp2.DMA()
        self.dma_ctrl = self.dma.pack_ctrl(
            size=1,  # 16 bit
            inc_read=False,
            treq_sel=4  # PIO(SM0) RX FIFO
        )

    def dump(self, addr_hex: str, size_str: str):
        addr = int(addr_hex, 16)
        size = int(size_str)
        print('send')
        self._read_and_send_data(addr, size)
        print('done')

    def _read_and_send_data(self, start_addr: int, rom_size: int):
        end_addr = start_addr + max(rom_size, self.BUFFER_SIZE) // 2  # [start, end) range

        self.sm.active(1)
        self.sm.put(start_addr)
        self.sm.put(end_addr)

        buffers = [bytearray(self.BUFFER_SIZE), bytearray(self.BUFFER_SIZE)]
        writing_buffer = 0
        sent_size = 0
        buffered_size = 0
        while sent_size < rom_size:
            if buffered_size < rom_size:
                # read rom data from GBA cart in PIO and copy to buffer with DMA asynchronously
                self.dma.config(read=self.sm,
                                write=buffers[writing_buffer],
                                count=self.BUFFER_SIZE // 2,
                                ctrl=self.dma_ctrl)
                self.dma.active(1)
            if sent_size < buffered_size:
                # send written data to host synchronously
                send_limit = min(rom_size - sent_size, self.BUFFER_SIZE)
                self._send_data(buffers[1 - writing_buffer][:send_limit])
                sent_size += send_limit
            if buffered_size < rom_size:
                while self.dma.active():
                    pass
                buffered_size += self.BUFFER_SIZE
            # flip buffers
            writing_buffer = 1 - writing_buffer
        self.sm.active(0)

    def _send_data(self, data: bytearray):
        b64_data = ubinascii.b2a_base64(data)
        print(len(b64_data))
        sys.stdout.write(b64_data)

    # noinspection PyStatementEffect,PyArgumentList,PyUnresolvedReferences
    @staticmethod
    @rp2.asm_pio(out_init=([rp2.PIO.OUT_LOW] * 24),
                 set_init=(rp2.PIO.OUT_HIGH, rp2.PIO.OUT_HIGH),
                 out_shiftdir=rp2.PIO.SHIFT_RIGHT)
    def _pio_read_data():
        pull()
        mov(x, invert(osr))  # copy start addr (inverted)
        pull()
        mov(y, invert(osr))  # copy end addr (inverted)
        label('loop')
        set(pins, 3)  # set CS to HIGH (rd,cs) = (1,1)
        mov(osr, invert(null))  # set OSR all bits to 1
        out(pindirs, 24)  # set addr pins to output
        mov(osr, invert(x))  # move start addr to OSR
        out(pins, 24).delay(12)  # send addr to GBA
        set(pins, 2)  # set CS to LOW (rd,cs) = (1,0)
        mov(osr, null)  # set OSR all bits to 0
        out(pindirs, 16).delay(12)  # set data pins to input
        set(pins, 0).delay(12)  # set RD to LOW (rd,cs) = (0,0)
        in_(pins, 16)  # read data from cart
        set(pins, 2)  # set RD to HIGH (rd,cs) = (1,0)
        push()  # push 2 byte to FIFO
        jmp(x_dec, 'post_dec')  # decrement inverted start addr (= increment start addr)
        label('post_dec')
        jmp(x_not_y, 'loop')
