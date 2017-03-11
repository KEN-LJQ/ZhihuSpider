import queue
import logging
from core.Logger import log

# 已分析用户信息的用户 token 缓存列表大小
MAX_ANALYSED_CACHE_QUEUE_SIZE = 1000
# 已分析用户信息的缓存列表保留大小
REMAIN_ANALYSED_CACHE_QUEUE_SIZE = 100
# 未分析用户信息的用户 token 缓存列表大小
MAX_CACHE_QUEUE_SIZE = 1000
# 未分析用户信息的用户 token 缓存列表保留大小
REMAIN_CACHE_QUEUE_SIZE = 100


class UserTokenCacheQueue:
    def __init__(self, db_connection):
        if log.isEnabledFor(logging.DEBUG):
            log.debug('正在配置用户 Token 缓存列表...')
        self.db_connection = db_connection
        self.analysed_cache_queue = queue.Queue(MAX_ANALYSED_CACHE_QUEUE_SIZE)
        self.cache_queue = queue.Queue(MAX_CACHE_QUEUE_SIZE)

        # 配置未分析用户信息列表
        token_total = self.db_connection.get_user_token_num()
        if token_total > 0:
            temp_list = self.get_token_from_db(REMAIN_CACHE_QUEUE_SIZE)
            for token in temp_list:
                self.cache_queue.put(token)
        # 配置已分析用户信息列表
        token_total = self.db_connection.get_analysed_token_num()
        if token_total > 0:
            temp_list = self.get_analysed_token_from_db(REMAIN_ANALYSED_CACHE_QUEUE_SIZE)
            for token in temp_list:
                self.analysed_cache_queue.put(token)
        if log.isEnabledFor(logging.DEBUG):
            log.debug('用户 Token 缓存列表配置完毕!!!')

    # 从数据库未分析列表取出指定数目的 token
    def get_token_from_db(self, num):
        token_list = self.db_connection.get_user_token(num)
        for token in token_list:
            self.db_connection.delete_user_token(token)
        return token_list

    # 从数据库已分析列表中取出指定数目的 token
    def get_analysed_token_from_db(self, num):
        token_list = self.db_connection.get_analysed_user_token(num)
        for token in token_list:
            self.db_connection.delete_analysed_user_token(token)
        return token_list

    # 添加 Token 到 cache_queue 中
    def add_token_into_cache_queue(self, token_list):
        # 判断队列中是否有足够位置存放，否则将一部分放入内存
        if self.cache_queue.qsize() + len(token_list) >= MAX_CACHE_QUEUE_SIZE:
            temp_list = []
            while self.cache_queue.qsize() > REMAIN_CACHE_QUEUE_SIZE:
                temp_list.append(self.cache_queue.get())
            self.db_connection.insert_user_token(temp_list)

        # 将该 Token 加入到队列中
        for token in token_list:
            self.cache_queue.put(token)

    # 添加 Token 到 analysed_cache_queue 中
    def add_token_into_analysed_cache_queue(self, token_list):
        # 判断队列中是否有足够位置存放，否则将一部分放入内存
        if self.analysed_cache_queue.qsize() + len(token_list) >= MAX_ANALYSED_CACHE_QUEUE_SIZE:
            temp_list = []
            while self.analysed_cache_queue.qsize() > REMAIN_ANALYSED_CACHE_QUEUE_SIZE:
                temp_list.append(self.analysed_cache_queue.get())
            self.db_connection.insert_analysed_user_token(temp_list)

        # 将该 Token 加入到队列中
        for token in token_list:
            self.analysed_cache_queue.put(token)

    # 从 cache_queue 中取出一个 Token
    def get_token_from_cache_queue(self):
        if self.cache_queue.qsize() > 0:
            # 直从队列中取出
            return self.cache_queue.get()
        elif self.db_connection.get_user_token_num() > 0:
            # 队列为空，先从数据库中取出一部分数据
            temp_list = self.get_token_from_db(REMAIN_CACHE_QUEUE_SIZE)
            for token in temp_list:
                self.cache_queue.put(token)
            return self.cache_queue.get()
        else:
            return None

    # 从analysed_cache_queue 中取出一个 Token
    def get_token_form_analysed_cache_queue(self):
        if self.analysed_cache_queue.qsize() > 0:
            # 直接从队列中取出
            return self.analysed_cache_queue.get()
        elif self.db_connection.get_analysed_token_num() > 0:
            # 队列为空，先从数据库中取出一部分数据
            temp_list = self.get_analysed_token_from_db(REMAIN_ANALYSED_CACHE_QUEUE_SIZE)
            for token in temp_list:
                self.analysed_cache_queue.put(token)
            return self.analysed_cache_queue.get()
        else:
            return None
