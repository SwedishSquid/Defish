
test_text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'

test_data = test_text * 10

bytes_list_test_data = [char.encode() for char in test_data]


from core_algorithms.huffman_core import HuffmanEncoderCore, HuffmanDecoderCore, HuffmanDataBlock
from byte_level_algorithms.simple_huffman_bytes_converters import SimpleHuffmanBlockToBytesConverter, SimpleBytesToHuffmanBlockConverter


def simple_huffman_to_bytes_test():
    s = 'привЕт Мир'.encode()
    test_data_list = bytes_list_test_data
    # test_data_list = [s[i:i+1] for i in range(len(s))] # bytes_list_test_data
    print(f'test_data len = {len(test_data_list)}')
    print(b''.join(test_data_list))
    block_size = 10000
    print(f'block_size = {block_size}')
    huffman_blocks = list(HuffmanEncoderCore(block_size).encode(iter(test_data_list)))

    encoded_blocks = list((SimpleHuffmanBlockToBytesConverter().encode(huffman_blocks)))
    print(f'bytes len = {len(encoded_blocks)}')
    print(b''.join(encoded_blocks))

    print('decoding back')
    decoded_huffman_blocks = list(SimpleBytesToHuffmanBlockConverter().decode(encoded_blocks))

    block: HuffmanDataBlock = decoded_huffman_blocks[0]
    print('block')
    print(block.item_to_code)
    decoded_test_data_list = list(HuffmanDecoderCore().decode(decoded_huffman_blocks))
    print(decoded_test_data_list)

    print(b''.join(decoded_test_data_list).decode())
    print(f'are equal = {b"".join(test_data_list) == b"".join(decoded_test_data_list)}')
    pass


# simple_huffman_to_bytes_test()

import time


def gen():
    print('jahshshj')
    yield 101


def test_generators():
    generator = gen()
    time.sleep(1)
    for i in generator:
        print(i)

test_generators()