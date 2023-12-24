from collections import deque


class LZ77DecoderCore:
    def __init__(self, window_width):
        self.window_width = window_width
        self.buffer = deque()
        pass

    def pump_to_buffer(self, item):
        self.buffer.append(item)
        if len(self.buffer) > self.window_width:
            self.buffer.popleft()
        pass

    def decode(self, generator):
        """generator itself"""
        for r in generator:
            record: LZ77Record = r
            if record.lookback_index == 0:
                self.pump_to_buffer(record.item)
                yield record.item
            else:
                for _ in range(record.length):
                    item = self.buffer[-record.lookback_index]
                    self.pump_to_buffer(item)
                    yield item
        pass


class LZ77EncoderCore:
    def __init__(self, window_width, sequence_max_length):
        self.window_width = window_width
        self.sequence_max_length = sequence_max_length
        self.search_buffer = deque()
        self.look_ahead_buffer = deque()
        pass

    def encode(self, generator):
        """generator itself"""
        self.fill_buffers_initial(generator)
        while len(self.look_ahead_buffer) > 0:
            best_ref_index, best_len = self.find_optimal_reference_index()
            # print(best_len)
            if best_ref_index == 0:
                item = self.indexer(0)
                yield LZ77Record(lookback_index=0, length=1, item=item)
            else:
                yield LZ77Record(lookback_index=-best_ref_index, length=best_len)
            for _ in range(best_len):
                self.try_move_item_to_search_buffer(generator)
        pass

    def find_optimal_reference_index(self):
        """index where match is the longest or 0 if no match"""
        best_len = 1
        best_index = 0
        for i in range(1, 1 + len(self.search_buffer)):
            cur_index = -i
            cur_len = self.get_common_length(cur_index)
            if cur_len > best_len:
                best_index = cur_index
                best_len = cur_len
        # remember: best_index <= 0
        return best_index, best_len

    def get_common_length(self, search_position):
        """search_position = position in search buffer
        from right to left starting at -1 and going to -buffer_len"""
        length = 0
        while self.can_be_indexed(length) and length < self.sequence_max_length:
            search_item = self.indexer(search_position + length)
            ahead_item = self.indexer(length)
            if search_item == ahead_item:
                length += 1
            else:
                break
        return length

    def can_be_indexed(self, index):
        if index < 0:
            return len(self.search_buffer) >= abs(index)
        return len(self.look_ahead_buffer) > index

    def indexer(self, index):
        if not self.can_be_indexed(index):
            raise IndexError('out of range')
        if index < 0:
            return self.search_buffer[index]
        return self.look_ahead_buffer[index]

    def try_move_item_to_search_buffer(self, generator):
        if len(self.look_ahead_buffer) == 0:
            return False
        item = self.look_ahead_buffer.popleft()

        self.search_buffer.append(item)
        if len(self.search_buffer) > self.window_width:
            self.search_buffer.popleft()

        try:
            item = next(generator)
            self.look_ahead_buffer.append(item)
        except StopIteration:
            pass
        return True

    def fill_buffers_initial(self, generator):
        self.search_buffer.clear()
        self.look_ahead_buffer.clear()
        look_ahead_buffer_len = self.window_width
        for i, item in enumerate(generator):
            self.look_ahead_buffer.append(item)
            if i + 1 >= look_ahead_buffer_len:
                break
        pass

    pass


class LZ77Record:
    def __init__(self, lookback_index: int, length: int, item=None):
        if lookback_index < 0:
            raise ValueError('lookback index must be not negative')

        if lookback_index == 0 and item is None:
            raise ValueError('item must be not None if lookback index == 0')

        if item is not None:
            if lookback_index != 0:
                raise ValueError('if item specified, then lookback index must be 0')
            if length != 1:
                raise ValueError('item specified, and length != 1')
        self.lookback_index = lookback_index
        self.length = length
        self.item = item
        pass
    pass


def test():
    text = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'

    data = text * 10

    result = list(LZ77EncoderCore(1000, 800).encode(iter(data)))

    translated = []
    for record in result:
        translated.append(record.lookback_index)
        if record.lookback_index == 0:
            translated.append(record.item)
        else:
            translated.append(record.length)

    decoded_data = list(LZ77DecoderCore(1000).decode(iter(result)))

    print([letter for letter in data])
    print(translated)
    print(decoded_data)
