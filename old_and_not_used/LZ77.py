
class LZ77coder:
    def __init__(self, search_buffer_size=100, look_ahead_buffer_size=100):
        self.search_buffer_size = search_buffer_size
        self.look_ahead_buffer_size = look_ahead_buffer_size
        pass

    def _get_common_len(self, text, look_back_index, current_pointer,
                        search_buffer_size, look_ahead_buffer_size):
        look_back_pointer = current_pointer - look_back_index
        i = 0
        while i < look_back_index and current_pointer + i < len(text):
            if text[look_back_pointer + i] == text[current_pointer + i]:
                i += 1
                continue
            break
        return i

    def _get_char(self, text, index):
        if len(text) <= index:
            return None
        return text[index]

    def _long_tuples_to_short(self, tuples):
        res = []
        for t in tuples:
            if t[0] == 0 and t[1] == 0:
                res.append((t[0], t[2]))
            else:
                res.append((t[0], t[1]))
        return res

    def _short_tuples_to_array(self, s_tup):
        res = []
        for t in s_tup:
            res.append(t[0])
            res.append(t[1])
        return res

    def _tuples_to_array(self, long_tuples):
        return self._short_tuples_to_array(self._long_tuples_to_short(long_tuples))

    def _encode_to_long_tuples(self, text):
        search_buffer_size = self.search_buffer_size
        look_ahead_buffer_size = self.look_ahead_buffer_size

        current = 0
        result = []

        while current < len(text):
            look_back_index = 1
            D = 0  # смещение (deflection)
            L = 0  # lenght

            while look_back_index <= search_buffer_size and current - look_back_index >= 0:
                cl = self._get_common_len(text, look_back_index,
                                          current, search_buffer_size,
                                          look_ahead_buffer_size)
                if cl > L:
                    D = look_back_index
                    L = cl
                    pass
                look_back_index += 1
                pass

            if L == 0:
                r = (D, L, self._get_char(text, current))
                current += 1
            else:
                current += L
                r = (D, L, self._get_char(text, current))
                # current += 1
            result.append(r)
        return result

    def encode(self, text):
        data = self._tuples_to_array(self._encode_to_long_tuples(text))
        return data

    def _array_to_short_tuples(self, arr):
        res = []
        if len(arr) % 2 != 0:
            print('wrong cow')
        for i in range(0, len(arr), 2):
            res.append((arr[i], arr[i + 1]))
        return res

    def _decode_from_tuples(self, tuples):
        search_buffer_size = self.search_buffer_size
        look_ahead_buffer_size = self.look_ahead_buffer_size

        result = []
        for t in tuples:
            D = t[0]
            if D == 0:
                letter = t[1]
                result.append(letter)
                continue
            L = t[1]
            for i in range(L):
                cur = len(result) - D
                el = result[cur]
                result.append(el)
        return result

    def decode(self, arr_of_short_data):
        return self._decode_from_tuples(
            self._array_to_short_tuples(arr_of_short_data))
    pass


class LZ77dataBuffer:
    def __init__(self, data_array):
        if len(data_array) % 2 != 0:
            raise ValueError("incorrect LZ77 encoding: array must contain even number of elements")
        self._data_array = data_array
        pass

    def get_data_array(self):
        return self._data_array

    @staticmethod
    def from_bytearray(arr: bytearray):
        if len(arr) % 8 != 0:
            raise ValueError("incorrect LZ77 byte encoding: bytearray must contain multiple-of-8 number of elements")
        data_arr = []
        for i in range(len(arr)//8):
            b = bytearray()
            for j in range(4):
                b.append(arr[i*8 + j])
            num = int.from_bytes(bytes(b), "big", signed=False)
            data_arr.append(num)
            b.clear()
            for j in range(4):
                b.append(arr[i*8 + 4 + j])
            if num == 0:
                ch: str = LZ77dataBuffer._retrify_ch_bytes(bytes(b)).decode('utf-8')
                data_arr.append(ch)
            else:
                num = int.from_bytes(bytes(b), "big", signed=False)
                data_arr.append(num)
        return LZ77dataBuffer(data_arr)

    @staticmethod
    def from_bytes(b: bytes):
        return LZ77dataBuffer.from_bytearray(bytearray(b))

    @staticmethod
    def _modify_ch_bytes(b):
        arr = bytearray(b)
        d = 4 - len(arr)
        return b'\x00' * d + b

    @staticmethod
    def _retrify_ch_bytes(b):
        arr = b
        i = 0
        for el in arr:
            if el == 0:
                i += 1
        if i >= len(arr):
            i = len(arr) - 1
        return bytes(arr[i:])

    def to_bytearray(self):
        buffer = []
        for i in range(len(self._data_array)//2):
            num: int = self._data_array[i*2]
            buffer.append(num.to_bytes(length=4, byteorder="big", signed=False))
            if num == 0:
                ch: str = self._data_array[i*2 + 1]
                buffer.append(self._modify_ch_bytes(ch.encode('utf-8')))
            else:
                num2: int = self._data_array[i*2 + 1]
                buffer.append(num2.to_bytes(length=4, byteorder="big", signed=False))
        res = bytearray()
        for b in buffer:
            for i in range(len(b)):
                res.append(b[i])
        return res

    def to_bytes(self):
        return bytes(self.to_bytearray())
    pass

#
# t = LZ77dataBuffer([0, 't', 123, 7, 7, 7])
#
# print(t.to_bytes())
#
# instance = LZ77dataBuffer.from_bytes(t.to_bytes())
#
# print(instance is t)
#
# print(instance._data_array)


# def get_common_len(text, look_back_index, current_pointer,
#                    search_buffer_size, look_ahead_buffer_size):
#     look_back_pointer = current_pointer - look_back_index
#     i = 0
#     while i < look_back_index and current_pointer + i < len(text):
#         if text[look_back_pointer + i] == text[current_pointer + i]:
#             i += 1
#             continue
#         break
#     return i


# def get_char(text, index):
#     if len(text) <= index:
#         return None
#     return text[index]
#
#
# def encode(text):
#     search_buffer_size = 100
#     look_ahead_buffer_size = 100
#
#     current = 0
#     result_core = []
#
#     while current < len(text):
#         look_back_index = 1
#         D = 0   # смещение (deflection)
#         L = 0   # lenght
#
#         while look_back_index <= search_buffer_size and current - look_back_index >= 0:
#             cl = get_common_len(text, look_back_index,
#                                 current, search_buffer_size,
#                                 look_ahead_buffer_size)
#             if cl > L:
#                 D = look_back_index
#                 L = cl
#                 pass
#             look_back_index += 1
#             pass
#
#         if L == 0:
#             r = (D, L, get_char(text, current))
#             current += 1
#         else:
#             current += L
#             r = (D, L, get_char(text, current))
#             #current += 1
#         result_core.append(r)
#     return result_core


# def long_tuples_to_short(tuples):
#     res = []
#     for t in tuples:
#         if t[0] == 0 and t[1] == 0:
#             res.append((t[0], t[2]))
#         else:
#             res.append((t[0], t[1]))
#     return res
#
#
# def short_tuples_to_array(s_tup):
#     res = []
#     for t in s_tup:
#         res.append(t[0])
#         res.append(t[1])
#     return res


# def array_to_short_tuples(arr_of_short_data):
#     res = []
#     if len(arr_of_short_data) % 2 != 0:
#         print('wrong cow')
#     for i in range(0, len(arr_of_short_data), 2):
#         res.append((arr_of_short_data[i], arr_of_short_data[i+1]))
#     return res



# def decode_from_tuples(tuples):
#     search_buffer_size = 100
#     look_ahead_buffer_size = 100
#
#     result_core = []
#     for t in tuples:
#         D = t[0]
#         if D == 0:
#             letter = t[1]
#             result_core.append(letter)
#             continue
#         L = t[1]
#         for i in range(L):
#             cur = len(result_core)-D
#             el = result_core[cur]
#             result_core.append(el)
#     return result_core
