import threading
import time
import logging
from Core.Logger import log


# URL 队列调度
class Scheduler(threading.Thread):
    __slots__ = ('redis_connection', 'url_rate', 'follow_info_url_queue', 'user_info_url_queue', 'url_queue_name')

    def __init__(self, redis_connection, url_rate):
        threading.Thread.__init__(self)
        # 设置Redis连接
        self.redis_connection = redis_connection
        # 设置 url 的调度比例
        self.url_rate = url_rate

        # Following & Follower URL 队列名称
        self.follow_info_url_queue = 'followInfoURLQueue'
        # User info URL 队列名称
        self.user_info_url_queue = 'userInfoURLQueue'
        # 待下载URL队列名称
        self.url_queue_name = 'urlQueue'

        if log.isEnabledFor(logging.INFO):
            log.info('Scheduler 模块初始化完毕')

    def run(self):

        if log.isEnabledFor(logging.INFO):
            log.info('Scheduler 模块启动成功')

        while True:
            # 当 urlQueue 队列中元素太多时，停止放入
            while self.redis_connection.llen(self.url_queue_name) > 500:
                time.sleep(180)

            # 当队列中均没有元素时，暂停添加
            follow_info_queue_length = self.redis_connection.llen(self.follow_info_url_queue)
            user_info_queue_length = self.redis_connection.llen(self.user_info_url_queue)
            if follow_info_queue_length == 0 and user_info_queue_length == 0:
                time.sleep(20)
                continue

            # 分别从两个队列中获取设定比例的数量的元素添加到下载URL队列
            for i in range(self.url_rate):
                url_info = self.redis_connection.lpop(self.user_info_url_queue)
                if url_info is not None:
                    self.redis_connection.rpush(self.url_queue_name, url_info)
                    del url_info

            for i in range(10 - self.url_rate):
                url_info = self.redis_connection.lpop(self.follow_info_url_queue)
                if url_info is not None:
                    self.redis_connection.rpush(self.url_queue_name, url_info)
                    del url_info
