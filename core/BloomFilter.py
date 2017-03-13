from BitVector import *
import cmath
import threading


def is_prime(n):
    if n == 9:
        return False
    for i in range(3, int(n ** 0.5)):
        if n % i == 0:
            return False
    return True


def find_prime(n):  # 找到从5开始的n个素书，使用素书筛法
    prime = []
    i = 5
    while len(prime) != n:
        flag = False
        for j in prime:
            if i % j == 0:
                flag = True
                i += 1
                break
        if flag:  # 如果能被素书整除就跳过一轮循环
            continue

        if is_prime(i):
            prime.append(i)
        i += 1

    return prime


class SimpleHash:  # 这里使用了bkdrhash的哈希算法
    def __init__(self, cap, seed):
        self.cap = cap
        self.seed = seed

    def hash(self, value):
        ret = 0
        for i in range(len(value)):
            ret += self.seed * ret + ord(value[i])
        return (self.cap - 1) & ret  # 控制哈系函数的值域


class BloomFilter:

    def __init__(self, amount=1 << 22):
        # self.container_size = (-1) * amount * cmath.log(0.001) / (cmath.log(2) * cmath.log(2))  # 计算最佳空间大小
        # self.container_size = int(self.container_size.real)  # 取整
        #
        # self.hash_amount = cmath.log(2) * self.container_size / amount
        # self.hash_amount = int(self.hash_amount.real)
        #
        # self.container = BitVector(size=int(self.container_size))  # 分配内存
        #
        # self.hash_seeds = find_prime(self.hash_amount)
        #
        # self.hash = []
        # for i in range(int(self.hash_amount)):  # 生成哈希函数
        #     self.hash.append(SimpleHash(self.container_size, self.hash_seeds[i]))
        self.token_set = set()
        # self.set_lock = threading.Lock()

    def exists(self, value):
        # if value is None:
        #     return False
        # for func in self.hash:
        #     if self.container[func.hash(str(value))] == 0:
        #         return False
        #     return True
        # self.set_lock.acquire()
        result = self.token_set.__contains__(value)
        # self.set_lock.release()
        return result

    def mark_value(self, value):
        # for func in self.hash:
        #     self.container[func.hash(str(value))] = 1
        # self.set_lock.acquire()
        self.token_set.add(value)
        # self.set_lock.release()
