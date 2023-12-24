from byte_bit_buffer import ByteBitBuffer
from core_algorithms.huffman_core import HuffmanDataBlock
import struct


class SimpleHuffmanBlockToBytesConverter:
    """converts HuffmanDataBlock sequence to byte sequence
    caution: works only if keys in code map are bytes!
    FORMAT of a block
    -Code_table(+)
    --table_length_bytes 4B
    --Table(+)
    ---repeated:
    ----Code_record:
    -----byte_value 1B
    -----code_length_in_bits 1B
    -----code [ceil(code_length_in_bits/8)]B
    -Data(+)
    --data_length_bytes 4B
    --filler_bits_count 1B
    --Encoded_data(+)
    ---repeated
    ----code ?bits
    --zero_filler_bits [?<8]bits
    """
    def __init__(self, int_format='>'):
        """int format defaults to big-endian"""
        self.int_format = int_format
        self.buffer = ByteBitBuffer()
        pass

    def encode(self, sequence):
        for block in sequence:
            self.check_block_format(block)
            self.encode_block(block)
            while self.buffer.has_bytes():
                yield self.buffer.pop_byte()
        pass

    def check_block_format(self, block: HuffmanDataBlock):
        for item, code in block.item_to_code:
            if type(item) != bytes:
                raise ValueError(f'blocks with items of non byte type'
                                 f' unsupported; got item of type {type(item)}')
            if len(item) != 1:
                raise ValueError(f'bytes items of len != 1 unsupported; '
                                 f'got item={item} of len {len(item)}')
            if len(code) == 0:
                raise ValueError(f'each item must have code of non-zero length '
                                 f'found {item} with code length of {len(code)}')
        pass

    def encode_block(self, block: HuffmanDataBlock):
        if not self.buffer.can_append_byte():
            raise ValueError('why are there bits in buffer??!')
        self.write_code_table_section(block)
        self.write_data_section(block)
        pass

    def write_code_table_section(self, block: HuffmanDataBlock):
        table_buffer = ByteBitBuffer()
        for value, code in block.item_to_code:
            self.write_code_table_record_to(table_buffer, value, code)
        table_length = table_buffer.get_full_bytes_len()
        length_bytes = struct.pack(f'{self.int_format}I', table_length)
        self.buffer.append_bytes_str(length_bytes)
        while table_buffer.has_bytes():
            self.buffer.append_byte(table_buffer.pop_byte())
        pass

    def write_code_table_record_to(self, buffer: ByteBitBuffer,
                                   value: bytes, code: list):
        buffer.append_byte(value)
        len_of_code = struct.pack('<B', len(code))
        buffer.append_byte(len_of_code)
        for bit in code:
            buffer.append_bit(bit)
        buffer.flush_bit_buffer()
        pass

    def write_data_section(self, block: HuffmanDataBlock):
        data_buffer = ByteBitBuffer()
        for code in block.data:
            for bit in code:
                data_buffer.append_bit(bit)
        filler_bits_count = (8 - data_buffer.flush_bit_buffer()) % 8
        data_length = data_buffer.get_full_bytes_len()
        length_bytes = struct.pack(f'{self.int_format}I', data_length)
        self.buffer.append_bytes_str(length_bytes)
        filler_bits_length_in_byte = struct.pack(f'<B', filler_bits_count)
        self.buffer.append_byte(filler_bits_length_in_byte)
        while data_buffer.has_bytes():
            self.buffer.append_byte(data_buffer.pop_byte())
        pass
    pass


class SimpleBytesToHuffmanBlockConverter:
    def __init__(self, int_format='>'):
        """int format defaults to big-endian"""
        self.int_format = int_format
        self.buffer = ByteBitBuffer()
        pass

    def decode(self, sequence):
        sequence = iter(sequence)
        while True:
            try:
                yield self.decode_block(sequence)
            except StopIteration:
                break
        pass

    def decode_block(self, sequence):
        value_to_code = self.read_code_table(sequence)
        possible_codes = set([pair[1] for pair in value_to_code])
        data = self.read_data(possible_codes, sequence)
        return HuffmanDataBlock(value_to_code, data)

    def read_code_table(self, sequence):
        """fill buffer only with code table bytes before this!!!!"""
        if self.buffer.has_bytes():
            raise ValueError('buffer must be empty here')
        code_table_byte_length = self.read_int_four(sequence)
        self.read_n_bytes_to_buffer(code_table_byte_length, sequence)

        value_to_code_table = []
        while self.buffer.has_bytes() > 0:
            value = self.buffer.pop_byte()
            code_bit_len = struct.unpack('>B', self.buffer.pop_byte())[0]
            code_array = []
            for i in range(code_bit_len):
                code_array.append(self.buffer.pop_bit())
            self.buffer.discard_bits_in_output_bit_buffer()
            code = self.code_arr_to_str(code_array)
            value_to_code_table.append((value, code))
        return value_to_code_table

    def read_data(self, possible_codes: set, sequence):
        if self.buffer.has_bytes():
            raise ValueError('buffer must be empty here')
        data_segment_byte_length = self.read_int_four(sequence)
        filler_bits_count = self.read_int_one(sequence)
        self.read_n_bytes_to_buffer(data_segment_byte_length, sequence)

        data_encoded = []
        current_code_arr = []
        while self.buffer.has_bits(filler_bits_count):
            current_code_arr.append(self.buffer.pop_bit())
            current_code_str = self.code_arr_to_str(current_code_arr)
            if len(current_code_arr) > 255:
                ValueError(f'code not found "{current_code_str}"')
            if current_code_str in possible_codes:
                data_encoded.append(current_code_str)
                current_code_arr.clear()
                continue
        self.buffer.discard_bits_in_output_bit_buffer()
        return data_encoded

    def read_int_four(self, sequence):
        byte_data = [next(sequence) for _ in range(4)]
        data = b''.join(byte_data)
        return struct.unpack(f'{self.int_format}I', data)[0]

    def read_int_one(self, sequence):
        data = next(sequence)
        return struct.unpack('<B', data)[0]

    def read_n_bytes_to_buffer(self, n, sequence):
        for i in range(n):
            self.buffer.append_byte(next(sequence))
        pass

    def code_arr_to_str(self, code_array):
        return ''.join(('1' if value else '0' for value in code_array))
    pass

