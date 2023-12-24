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


class HuffmanCoder:
    def __init__(self):
        pass

    def _count_elements_distribution(self, arr):
        d = dict()
        for el in arr:
            if el in d:
                d[el] += 1
            else:
                d[el] = 1
        return d

    def _make_tree(self, distribution):
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

    def encode(self, arr):
        distribution = self._count_elements_distribution(arr)
        tree = self._make_tree(distribution)
        code_map = dict()
        self._fill_code_map(code_map, tree, [])
        coded_to_bits = []
        for el in arr:
            for bit in code_map[el]:
                coded_to_bits.append(bit)
        return coded_to_bits, code_map

    def decode(self, bit_sequence, code_to_value_pairs):

        pass

    def _fill_code_map(self, code_map, node: Node, path_to_node: list):
        if node is None:
            return
        if node.is_leaf:
            if len(path_to_node) == 0:
                path_to_node.append(False)
            code_map[node.value] = path_to_node.copy()
            return
        # to left -> 0
        path_to_node.append(False)
        self._fill_code_map(code_map, node.left, path_to_node)
        path_to_node.pop()
        # to right -> 1
        path_to_node.append(True)
        self._fill_code_map(code_map, node.right, path_to_node)
        path_to_node.pop()
        pass
    pass


coder = HuffmanCoder()

bits, code_map = coder.encode('sssrrt')

print(bits)

print(code_map)

