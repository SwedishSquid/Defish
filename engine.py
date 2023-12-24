from pathlib import Path
import pickle
from byte_level_algorithms import file_handler
from core_algorithms.LZ77_core import LZ77EncoderCore, LZ77DecoderCore
from byte_level_algorithms.LZ77Record_to_bytes_converter import LZ77RecordToBytesConverter
from core_algorithms.huffman_core import HuffmanEncoderCore, HuffmanDecoderCore
from byte_level_algorithms.simple_huffman_bytes_converters import SimpleHuffmanBlockToBytesConverter, SimpleBytesToHuffmanBlockConverter
from byte_level_algorithms.cypher_stream import CypherStream
import struct
from byte_bit_buffer import ByteBitBuffer
from itertools import chain
import hashlib


class FileInfo:
    def __init__(self, name, path, start_position_bytes=None, length_bytes=None):
        self.name = name
        self.path = Path(path)
        self.start_position_bytes = start_position_bytes
        self.length_bytes = length_bytes
        self.initial_size = None
        pass

    def set_position_info(self, start_pos_bytes: int, length_bytes:int):
        self.start_position_bytes = start_pos_bytes
        self.length_bytes = length_bytes
        pass
    pass


class DirInfo:
    def __init__(self, name: str, files, dirs):
        self.files = files
        self.dirs = dirs
        self.name = name
        pass

    def get_all_files(self):
        result = self.files[:]
        for d in self.dirs:
            result += d.get_all_files()
        return result

    def remove_all_file_paths(self):
        for f in self.files:
            f.path = None
        for d in self.dirs:
            d.remove_all_file_paths()
        pass

    def set_new_file_paths(self, root):
        for f in self.files:
            f.path = Path(root, self.name, f.name)
        for d in self.dirs:
            d.set_new_file_paths(Path(root, self.name))
        pass
    pass


def construct_dir_tree(dir_path):
    dir_path = Path(dir_path)
    sub_dirs = []
    files = []
    for path in dir_path.iterdir():
        if path.is_dir():
            sub_dirs.append(construct_dir_tree(path))
        else:
            files.append(construct_file_info(path))
    return DirInfo(dir_path.name, files, sub_dirs)


def construct_file_info(path):
    path = Path(path)
    file_info = FileInfo(path.name, path)
    file_info.initial_size = path.stat().st_size
    return file_info


def construct_tree(path):
    path = Path(path)
    if path.is_dir():
        return construct_dir_tree(path)
    return DirInfo(path.name[:-len(path.suffix)], [construct_file_info(path)], [])


def decode_tree(tree_bytes, root_path):
    tree: DirInfo = pickle.loads(tree_bytes)
    tree.set_new_file_paths(root_path)
    return tree


def encode_tree(tree: DirInfo):
    tree.remove_all_file_paths()
    tree_s = pickle.dumps(tree)
    return tree_s


# def tree_serialization_test():
#     src_file = Path(r"E:\dev\PythonHomework\Pytask\Deflate\data_files\source_data")
#     init_tree = construct_tree(src_file)
#     enc_tree = encode_tree(init_tree)
#     print(enc_tree)
#     dec_tree = decode_tree(enc_tree)
#     print('finish')


class PasswordRequiredError(Exception):
    pass


class FlagsHandler:
    def __init__(self, flags_byte: bytes):
        if len(flags_byte) != 1:
            ValueError('wrong flags arg')
        self.flags_num = flags_byte[0]
        pass

    @property
    def use_password(self):
        return self.contain(1)

    @property
    def use_LZ77(self):
        return self.contain(2)

    def contain(self, flag_num):
        return (self.flags_num & 1 << flag_num) != 0

    def change(self, flag_num):
        self.flags_num ^= 1 << flag_num
        pass

    def to_byte(self):
        return struct.pack('<B', self.flags_num)
    pass


class Engine:
    int_format = '>I'
    compressed_file_extension = '.defish'

    def __init__(self, src, dst_folder=None, password=None, use_lz77=False, writing_limit_megabytes=None):
        self.src = Path(src)
        if dst_folder is None:
            self.dst_folder = self.src
        else:
            self.dst_folder = Path(dst_folder)

        if writing_limit_megabytes is None:
            writing_limit_megabytes = 3
        self.writing_limit_bytes = writing_limit_megabytes * 1024 * 1024

        self.flags_handler = FlagsHandler(b'\x00')
        if password is not None:
            self.flags_handler.change(1)
        if use_lz77:
            self.flags_handler.change(2)


        self.cypher = CypherStream(self.hash_password(password))
        pass

    def compress(self):
        """
        -flags 1B
        -tree_pointer 4B
        -data ?B
        -tree_length_in_bytes 4B
        -Tree
        """
        if self.flags_handler.use_password:
            print('compressing with password')

        flags = self.flags_handler.to_byte()

        tree_pointer_mock = [b'\x00', b'\x00', b'\x00', b'\x00']

        tree = construct_tree(self.src)
        files = tree.get_all_files()

        compressed_data_stream = chain([flags] + tree_pointer_mock,
                                       self.make_one_big_files_stream(5, files),
                                       self.make_encoded_tree_stream(tree))

        dst_path = Path(self.dst_folder, tree.name + self.compressed_file_extension)
        file_handler.write_to_file_limited(dst_path, compressed_data_stream, self.writing_limit_bytes)

        tree_pointer_int = 5
        if len(files) > 0:
            last_file: FileInfo = files[-1]
            tree_pointer_int = last_file.start_position_bytes + last_file.length_bytes

        with open(dst_path, 'rb+') as f:
            f.seek(1)
            f.write(struct.pack(self.int_format, tree_pointer_int))
        pass

    def make_encoded_tree_stream(self, tree):
        enc_tree = encode_tree(tree)
        buffer = ByteBitBuffer()
        buffer.append_bytes_str(struct.pack(self.int_format, len(enc_tree)))
        buffer.append_bytes_str(enc_tree)
        while buffer.has_bytes():
            yield buffer.pop_byte()
        pass

    def make_one_big_files_stream(self, offset: int, files_info: list):
        current_start_position = offset
        for f in files_info:
            f: FileInfo = f
            length = 0
            for byte in self.make_compressed_file_stream(f.path):
                length += 1
                yield byte
            f.set_position_info(current_start_position, length)
            current_start_position += length
        pass

    def make_compressed_file_stream(self, filepath):
        filepath = Path(filepath)

        input_byte_stream = file_handler.read_file_stream(file_path=filepath)

        current_stream = input_byte_stream
        if self.flags_handler.use_password:
            # print('compressing with password')
            current_stream = self.cypher.encode(current_stream)

        if self.flags_handler.use_LZ77:
            window_width = 50
            compressed_record_stream = \
                LZ77EncoderCore(window_width, window_width).encode(
                    input_byte_stream)
            compressed_byte_stream = \
                LZ77RecordToBytesConverter().encode(compressed_record_stream)
            current_stream = compressed_byte_stream

        block_len = 10000
        huffman_blocks_stream = HuffmanEncoderCore(block_len).encode(
            current_stream)
        encoded_bytes_stream = SimpleHuffmanBlockToBytesConverter().encode(
            huffman_blocks_stream)
        return encoded_bytes_stream

    def decompress(self):
        self.read_flags()
        if self.flags_handler.use_password:
            print('decompressing with password')

        tree = self.read_dir_tree()
        files = tree.get_all_files()
        for file in files:
            file: FileInfo = file
            output_bytes_stream =\
                self.make_decompressed_file_stream(self.src, file.start_position_bytes, file.length_bytes)
            folder = file.path.parent
            if not folder.exists():
                folder.mkdir()
            self.writing_limit_bytes =\
                file_handler.write_to_file_limited(file_path = file.path,
                                                   sequence=output_bytes_stream,
                                                   limit_in_bytes=self.writing_limit_bytes)
        pass

    def make_decompressed_file_stream(self, archive_file_path, start_pos, length):
        encoded_bytes_stream = file_handler.read_file_segment_stream(archive_file_path, start_pos, length)
        huffman_blocks_stream = SimpleBytesToHuffmanBlockConverter().decode(encoded_bytes_stream)
        current_stream = HuffmanDecoderCore().decode(huffman_blocks_stream)

        if self.flags_handler.use_LZ77:
            compressed_record_stream = LZ77RecordToBytesConverter().decode(current_stream)
            current_stream = LZ77DecoderCore(window_width=50).decode(compressed_record_stream)

        if self.flags_handler.use_password:
            current_stream = self.cypher.decode(current_stream)
        return current_stream

    def read_dir_tree(self):
        with open(self.src, 'rb') as f:
            flags = f.read(1)
            tree_pointer = struct.unpack(self.int_format, f.read(4))[0]
            f.seek(tree_pointer)
            tree_length = struct.unpack(self.int_format, f.read(4))[0]
            tree_bytes_str = f.read(tree_length)
        return decode_tree(tree_bytes_str, self.dst_folder)

    def read_flags(self):
        with open(self.src, 'rb') as f:
            flags = f.read(1)
        self.flags_handler = FlagsHandler(flags)
        pass

    def hash_password(self, password: bytes | str):
        if password is None:
            return 0
        if type(password) == str:
            password = password.encode()
        return hashlib.sha256(password).digest()[:4]
    pass
