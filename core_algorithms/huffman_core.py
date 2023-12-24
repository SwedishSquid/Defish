import heapq


class Node:
    def __init__(self, value, left=None, right=None):
        self.value = value
        self.left = left
        self.right = right
        pass

    @property
    def is_leaf(self):
        return self.left is None and self.right is None

    pass


class HuffmanEncoderCore:
    def __init__(self, block_length):
        self.block_length = block_length
        self.buffer = []
        pass

    def encode(self, iterator):
        """generator itself"""
        while True:
            self.pump_to_buffer(iterator)
            if len(self.buffer) == 0:
                break
            yield self.encode_buffer()
        pass

    def encode_buffer(self):
        block_distribution = self.calculate_distribution_in_buffer()
        tree_root = self.build_tree(block_distribution)
        code_map = self.get_code_map(tree_root)
        block_data = []
        for item in self.buffer:
            block_data.append(code_map[item])
        item_to_code = []
        for k, v in code_map.items():
            item_to_code.append((k, v))
        return HuffmanDataBlock(item_to_code, block_data)

    def get_code_map(self, tree_root: Node):
        code_map_raw = dict()
        self._fill_code_map_recursively(code_map_raw, tree_root, [])
        return code_map_raw

    def _fill_code_map_recursively(self, code_map: dict, node: Node,
                                   path_to_node: list):
        if node is None:
            return
        if node.is_leaf:
            cur_path = path_to_node.copy()
            if len(cur_path) == 0:  # possible only if alphabet of 1 letter
                cur_path.append(False)
            code_map[node.value] = cur_path
            return
        # to left -> 0
        path_to_node.append(False)
        self._fill_code_map_recursively(code_map, node.left, path_to_node)
        path_to_node.pop()
        # to right -> 1
        path_to_node.append(True)
        self._fill_code_map_recursively(code_map, node.right, path_to_node)
        path_to_node.pop()
        pass

    def build_tree(self, distribution: dict):
        p_queue = []
        i = 0
        for k, v in distribution.items():
            p_queue.append((v, i, Node(k)))
            i += 1
        heapq.heapify(p_queue)
        while len(p_queue) > 1:
            weight1, _, node1 = heapq.heappop(p_queue)
            weight2, _, node2 = heapq.heappop(p_queue)
            heapq.heappush(p_queue,
                           (weight1 + weight2, i, Node(None, node1, node2)))
            i += 1
        _, _, root = heapq.heappop(p_queue)
        return root

    def calculate_distribution_in_buffer(self):
        distribution = dict()
        for item in self.buffer:
            if item in distribution:
                distribution[item] += 1
            else:
                distribution[item] = 1
        return distribution

    def pump_to_buffer(self, iterator):
        self.buffer.clear()
        for _ in range(self.block_length):
            try:
                item = next(iterator)
                self.buffer.append(item)
            except StopIteration:
                break
        pass

    pass


class HuffmanDataBlock:
    def __init__(self, item_to_code: list, data: list):
        self.item_to_code = item_to_code
        self.data = data
        pass

    pass


class HuffmanDecoderCore:
    def decode(self, iterator, hasher=None):
        """generator itself"""
        for block in iterator:
            for item in self.decode_block(block, hasher):
                yield item
        pass

    def decode_block(self, block: HuffmanDataBlock, hasher=None):
        code_to_item = dict()
        if hasher is None:
            hasher = lambda x: x
        for item, c in block.item_to_code:
            code = hasher(c)
            code_to_item[code] = item
        for c in block.data:
            code = hasher(c)
            yield code_to_item[code]
        pass



