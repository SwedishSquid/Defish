import argparse
from pathlib import Path
from engine import Engine, DirInfo, FileInfo
from collections import deque


class ConsoleInterface:
    def __init__(self):
        pass

    def run(self):
        parser = self.init_parser()
        args = parser.parse_args()
        mode = args.mode

        engine = Engine(src=self.resolve_path(args.src),
                        dst_folder=self.resolve_path(args.destination, is_dir=True),
                        password=args.password,
                        use_lz77=args.use_lz77,
                        writing_limit_megabytes=args.writing_limit)
        if mode == 'stat':
            tree = engine.read_dir_tree()
            self.pretty_print_tree(tree)
        elif mode == 'c':
            engine.compress()
            print('compressed')
        elif mode == 'd':
            src_path = self.resolve_path(args.src)
            if src_path.suffix != Engine.compressed_file_extension:
                print(
                    f'Wrong file warning!! selected file is not a {Engine.compressed_file_extension} file : {src_path}')
            engine.decompress()
            print('decompressed')
        else:
            raise ValueError(f'mode {mode} not supported')
        return

    def resolve_path(self, input_path_str, is_dir=False):
        if input_path_str is None:
            return None
        path = Path(input_path_str)
        if not path.is_absolute():
            path = Path(Path.cwd(), path)
        if not path.exists():
            raise FileNotFoundError(f'path {input_path_str} not found')
        if is_dir and not path.is_dir():
            raise NotADirectoryError(f'path {input_path_str} not a directory')
        return path

    def init_parser(self):
        parser = argparse.ArgumentParser(prog="defish",
                                         description="compress arbitrary data")
        parser.add_argument('src', type=str,
                            help='file or folder path that will be the source')
        parser.add_argument('mode', choices=['stat', 'c', 'd'],
                            help='stat == show statistics'
                                 'c == compress'
                                 'd == decompress')
        parser.add_argument('-wl', '--writing_limit', type=int,
                            help='limit on how much megabytes can be written to file;'
                                 'to prevent unlimited writing to file in case if something goes wrong'
                                 'default is 3')
        parser.add_argument('-dst', '--destination', type=str,
                            help='destination path == where to put results')
        parser.add_argument('-psw', '--password', type=str)
        parser.add_argument('--use_lz77', action='store_true', help='whether to use lz77 or not; my lz77 seems to be pretty slow and totally unproductive; thats pobably due to small window width (50 bytes) compared to standart 32Kb; bigger window, slower program; '
                                                                    'no need to specify this when decoding')
        return parser

    def pretty_print_tree(self, tree):
        queue = deque()
        queue.append((tree, 0))
        while len(queue) > 0:
            cur_dir, level = queue.popleft()
            cur_dir: DirInfo = cur_dir
            print(self.get_file_record(cur_dir.name, level, None))
            for f in cur_dir.files:
                file: FileInfo = f
                comp_ratio = None if (file.length_bytes is None
                                      or file.initial_size is None
                                      or file.initial_size == 0) \
                    else file.length_bytes / file.initial_size
                print(self.get_file_record(file.name, level+1, comp_ratio))
            for d in cur_dir.dirs:
                queue.append((d, level+1))
        pass

    def get_file_record(self, name, level, compression_ratio, offset=50):
        result = f'{"-"*level}{name}'
        if compression_ratio is not None:
            result += f"{' '*(max(10, offset-len(result)))}{compression_ratio*100} %"
        return result
    pass


if __name__ == "__main__":
    ConsoleInterface().run()
