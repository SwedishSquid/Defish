import random
import struct


class CypherStream:
    def __init__(self, key):
        self.rand = random.Random()
        self.rand.seed(key, version=2)
        pass

    def encode(self, byte_sequence):
        rand = self.get_rand()
        for byte in byte_sequence:
            byte_int = struct.unpack('<B', byte)[0]
            byte_shifted = (byte_int + rand.randint(0, 255)) % 256
            yield struct.pack('<B', byte_shifted)
        pass

    def decode(self, byte_sequence):
        rand = self.get_rand()
        for byte in byte_sequence:
            byte_int = struct.unpack('<B', byte)[0]
            byte_shifted = (256 + byte_int - rand.randint(0, 255)) % 256
            yield struct.pack('<B', byte_shifted)
        pass

    def get_rand(self):
        return self.rand
    pass
