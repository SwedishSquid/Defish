from pathlib import Path
import struct
from byte_bit_buffer import ByteBitBuffer
from core_algorithms.huffman_core import HuffmanEncoderCore, HuffmanDecoderCore
from byte_level_algorithms.simple_huffman_bytes_converters import SimpleHuffmanBlockToBytesConverter, SimpleBytesToHuffmanBlockConverter
from core_algorithms.LZ77_core import LZ77EncoderCore, LZ77DecoderCore, LZ77Record


file_name = "cool_picture"
extension = ".bmp"

src_file = Path(r"/data_files/source_data", file_name + extension)

encoded_file = Path(r"/data_files/encoded", file_name + ".defish")

decoded_file = Path(r"/data_files/decoded", file_name + extension)


def read_file_stream(file_path):
    with open(file_path, 'rb') as f:
        buffer = ByteBitBuffer()
        step = 10000
        while True:
            if not buffer.has_bytes():
                buffer.append_bytes_str(f.read(step))
            if not buffer.has_bytes():
                break
            yield buffer.pop_byte()
    pass


def write_all_to_file(file_path, sequence):
    with open(file_path, 'wb') as f:
        byte_buffer = ByteBitBuffer()
        step = 1000
        while True:
            for i, byte in enumerate(sequence):
                byte_buffer.append_byte(byte)
                if i >= step:
                    break
            if not byte_buffer.has_bytes():
                break
            f.write(b''.join(byte_buffer.pop_all_bytes()))
    pass


format_two = '<B'
def LZ77Record_to_bytes_stream(record_stream):
    buffer = ByteBitBuffer()
    for r in record_stream:
        r: LZ77Record = r
        buffer.append_bytes_str(struct.pack(format_two, r.lookback_index))
        if r.lookback_index != 0:
            buffer.append_bytes_str(struct.pack(format_two, r.length))
        else:
            buffer.append_byte(r.item)
        while buffer.has_bytes():
            yield buffer.pop_byte()


def bytes_to_LZ77Record_stream(byte_stream):
    buffer = ByteBitBuffer()
    while True:
        try:
            buffer.append_byte(next(byte_stream))
            #buffer.append_byte(next(byte_stream))
            lookback_index = struct.unpack(format_two, b''.join(buffer.pop_n_bytes(1)))[0]
            if lookback_index != 0:
                buffer.append_byte(next(byte_stream))
                #buffer.append_byte(next(byte_stream))
                length = struct.unpack(format_two, b''.join(buffer.pop_n_bytes(1)))[0]
                yield LZ77Record(lookback_index, length)
            else:
                item = next(byte_stream)
                yield LZ77Record(lookback_index, 1, item)
        except StopIteration:
            break
    pass


window_width = 255
def encode(from_file, to_file):
    input_file_stream = read_file_stream(from_file)

    compressed_record_stream = LZ77EncoderCore(window_width, window_width).encode(input_file_stream)
    compressed_byte_stream = LZ77Record_to_bytes_stream(compressed_record_stream)

    block_len = 10000
    huffman_blocks_stream = HuffmanEncoderCore(block_len).encode(compressed_byte_stream)
    encoded_bytes_stream = SimpleHuffmanBlockToBytesConverter().encode(huffman_blocks_stream)
    write_all_to_file(to_file, encoded_bytes_stream)
    pass


def decode(from_file, to_file):
    encoded_bytes_stream = read_file_stream(from_file)
    huffman_blocks_stream = SimpleBytesToHuffmanBlockConverter().decode(encoded_bytes_stream)
    compressed_bytes_stream = HuffmanDecoderCore().decode(huffman_blocks_stream)
    compressed_record_stream = bytes_to_LZ77Record_stream(compressed_bytes_stream)
    output_bytes_stream = LZ77DecoderCore(window_width).decode(compressed_record_stream)
    write_all_to_file(to_file, output_bytes_stream)
    pass


encode(src_file, encoded_file)
print('decoding')
decode(encoded_file, decoded_file)
