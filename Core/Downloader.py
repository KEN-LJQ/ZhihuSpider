from Proxy import proxyCore
from Core.Logger import log
import queue
import threading
import logging
import time
import requests

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# 请求头信息
requestHeader = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Encoding": "gzip, deflate, sdch, br",
                 "Accept-Language": "zh-CN,zh;q=0.8",
                 "Cache-Control": "max-age=0",
                 "Host": "www.zhihu.com",
                 "Upgrade-Insecure-Requests": "1",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
                               " Chrome/56.0.2924.87 Safari/537.36"}


# SessionPool 管理器
class SessionManager:
    __slots__ = ('session_pool_size', 'created_session_num', 'available_session_num', 'is_proxy_service_enable',
                 'account_manager', 'session_pool', 'proxy_service', 'available_session_lock', 'created_session_lock')

    # 初始化
    def __init__(self, session_pool_size, account_manager, is_proxy_service_enable):
        # session pool 大小
        self.session_pool_size = session_pool_size
        # 已经创建的session数量
        self.created_session_num = 0
        # 当前池中的session数量
        self.available_session_num = 0
        # 是否启用代理服务
        self.is_proxy_service_enable = is_proxy_service_enable
        # 账号认证管理器
        self.account_manager = account_manager

        # available session num 锁
        self.available_session_lock = threading.Lock()
        # created session num 锁
        self.created_session_lock = threading.Lock()

        # 创建 session pool
        self.session_pool = queue.Queue(session_pool_size)
        # 创建并启动代理服务
        if self.is_proxy_service_enable is True:
            self.proxy_service = proxyCore.ProxyService()
            self.proxy_service.start_proxy_service()

        if log.isEnabledFor(logging.INFO):
            log.info("Session Manager 启动成功")

    # 创建包含代理信息的 session
    def create_session_proxy(self, proxy_info):
        # 获取代理信息
        ip = proxy_info['ip']
        port = proxy_info['port']
        protocol = proxy_info['protocol'].lower()
        proxy = {protocol: ip + ':' + port}

        # 创建session
        session = requests.session()
        session.headers = requestHeader
        session.cookies.update(self.account_manager.get_auth_token())
        session.proxies = proxy

        # 将 session 放入到池中
        self.session_pool.put(session)
        self.created_session_num_change(1)
        self.available_session_num_change(1)

    # 创建不含代理信息的 session
    def create_session(self):
        # 创建session
        session = requests.session()
        session.cookies.update(self.account_manager.get_auth_token())
        session.headers = requestHeader

        # 将 session 放入池中
        self.session_pool.put(session)
        self.created_session_num_change(1)
        self.available_session_num_change(1)

    # 获取一个session连接
    def get_session_connection(self):

        # 辅助创建 session pool 中的 session
        if self.available_session_num <= 0 and self.created_session_num < self.session_pool_size:
            if self.is_proxy_service_enable is True:
                self.create_session_proxy(self.proxy_service.get_proxy())
            else:
                self.create_session()

        # 从 session pool 中获取
        session = self.session_pool.get()
        self.available_session_num_change(-1)
        return session

    # 归还一个 session 连接
    def return_session_connection(self, session_connection):
        self.session_pool.put(session_connection)
        self.available_session_num_change(1)

    # 归还并更换 session 的代理
    def return_and_switch_proxy(self, session_connection):
        # 更换代理信息
        if self.is_proxy_service_enable is True:
            proxy_info = self.proxy_service.get_proxy()
            ip = proxy_info['ip']
            port = proxy_info['port']
            protocol = proxy_info['protocol'].lower()
            proxy = {protocol: ip + ':' + port}
            session_connection.proxies = proxy
        # 归还
        self.return_session_connection(session_connection)

    # 修改 available_session_num 的值
    def available_session_num_change(self, num):
        self.available_session_lock.acquire()
        self.available_session_num += num
        self.available_session_lock.release()

    # 修改 available_session_num 的值
    def created_session_num_change(self, num):
        self.created_session_lock.acquire()
        self.created_session_num += num
        self.created_session_lock.release()


# 管理下载线程
class Downloader:
    __slots__ = ('download_thread_num', 'redis_connection', 'response_buffer', 'session_manager',
                 'NETWORK_RETRY_TIMES', 'account_manager',
                 'CONNECT_TIMEOUT', 'DOWNLOAD_INTERVAL', 'download_thread_list')

    # 初始化
    def __init__(self, redis_connection, response_buffer, account_manager, is_proxy_service_enable, session_pool_size,
                 download_thread_num, network_retry_times, connect_timeout, download_interval):
        # 设置下载线程的数量
        self.download_thread_num = download_thread_num
        # 设置 Redis 连接
        self.redis_connection = redis_connection
        # 设置 response 缓存队列
        self.response_buffer = response_buffer
        # 设置账户认证管理器
        self.account_manager = account_manager
        # 设置并启动sessionManager
        self.session_manager = SessionManager(session_pool_size, account_manager, is_proxy_service_enable)

        # 设置网络连接参数
        self.NETWORK_RETRY_TIMES = network_retry_times
        self.CONNECT_TIMEOUT = connect_timeout
        self.DOWNLOAD_INTERVAL = download_interval

        # 初始化下载线程
        self.download_thread_list = []
        for i in range(self.download_thread_num):
            download_thread = DownloadThread('thread' + str(i), self.session_manager, self.redis_connection,
                                             self.response_buffer, self.NETWORK_RETRY_TIMES, self.CONNECT_TIMEOUT,
                                             self.DOWNLOAD_INTERVAL)
            self.download_thread_list.append(download_thread)

        if log.isEnabledFor(logging.INFO):
            log.info("Downloader 模块初始化完毕")

    # 启动
    def start_downloader(self):
        # 启动下载线程
        for download_thread in self.download_thread_list:
            download_thread.start()

        if log.isEnabledFor(logging.INFO):
            log.info('Downloader 模块启动成功')

    # 检查并重启线程
    def check_and_restart(self):
        for download_thread in self.download_thread_list:
            if download_thread.thread_status == 'error':
                thread_id = download_thread.thread_id
                self.download_thread_list.remove(download_thread)
                download_thread = DownloadThread(thread_id, self.session_manager, self.redis_connection,
                                                 self.response_buffer, self.NETWORK_RETRY_TIMES, self.CONNECT_TIMEOUT,
                                                 self.DOWNLOAD_INTERVAL)
                self.download_thread_list.append(download_thread)
                download_thread.start()
                if log.isEnabledFor(logging.INFO):
                    log.info('数据下载线程' + thread_id + '重新启动')


# 下载线程
class DownloadThread(threading.Thread):
    __slots__ = ('thread_status', 'thread_id', 'session_manager', 'redis_connection', 'response_buffer',
                 'url_queue_name', 'response_queue_name', 'NETWORK_RETRY_TIMES', 'CONNECT_TIMEOUT',
                 'DOWNLOAD_INTERVAL')

    def __init__(self, thread_id, session_manager, redis_connection, response_buffer, network_retry_times,
                 connect_timeout, download_interval):
        threading.Thread.__init__(self)
        # 线程状态
        self.thread_status = 'working'
        # 线程ID
        self.thread_id = thread_id
        # 设置session manager
        self.session_manager = session_manager
        # 设置 redis 连接
        self.redis_connection = redis_connection
        # 设置 response 缓存队列
        self.response_buffer = response_buffer
        # 设置获取待下载URL队列名称
        self.url_queue_name = 'urlQueue'
        # 设置存放下载内容队列名称
        self.response_queue_name = 'responseQueue'

        # 设置网络连接的参数
        self.NETWORK_RETRY_TIMES = network_retry_times
        self.CONNECT_TIMEOUT = connect_timeout
        self.DOWNLOAD_INTERVAL = download_interval

    def run(self):
        if log.isEnabledFor(logging.INFO):
            log.info('数据下载线程' + self.thread_id + '启动')

        # 保存上一次未下载的url info
        previous_url_info = None
        while True:
            # 获取session
            session = self.session_manager.get_session_connection()

            # 尝试下载数据
            network_retry_times = 0
            while network_retry_times < self.NETWORK_RETRY_TIMES:
                try:
                    # 获取URL
                    if previous_url_info is None:
                        url_info = self.get_url_info_from_queue()
                        previous_url_info = url_info
                    else:
                        url_info = previous_url_info
                    url = url_info[1]

                    # 下载数据
                    response = session.get(url, timeout=self.CONNECT_TIMEOUT)

                    if log.isEnabledFor(logging.DEBUG):
                        log.debug(response.status_code)

                    # 检查返回结果
                    if response.status_code == 200:
                        # 封装下载的数据(包括原来的数据)
                        response_info = url_info
                        response_info[1] = response.text
                        self.put_response_info_to_queue(response_info)
                        previous_url_info = None
                        if log.isEnabledFor(logging.DEBUG):
                            log.debug('下载成功')
                        break
                    elif response.status_code == 403:
                        if log.isEnabledFor(logging.ERROR):
                            log.error('账号认证失败')
                        break
                    elif response.status_code == 429:
                        if log.isEnabledFor(logging.DEBUG):
                            log.debug('[' + str(self.thread_id) + ']' + '访问太频繁，稍候重新访问，响应码为：'
                                      + str(response.status_code))
                        previous_url_info = url_info
                        break
                    elif response.status_code == 404 or response.status_code == 410:
                        previous_url_info = None
                        break
                    else:
                        if log.isEnabledFor(logging.ERROR):
                            log.error(response.status_code)
                        network_retry_times += 1
                except Exception as e:
                    network_retry_times += 1
                    time.sleep(self.DOWNLOAD_INTERVAL)
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug('[' + str(self.thread_id) + ']' + '下载异常，正在重新连接...（第'
                                  + str(network_retry_times) + '次重试)')
                    if log.isEnabledFor(logging.DEBUG):
                        log.error(e)

            # 下载间隔
            time.sleep(self.DOWNLOAD_INTERVAL)

            # 归还session
            if network_retry_times < self.NETWORK_RETRY_TIMES:
                self.session_manager.return_session_connection(session)
            else:
                self.session_manager.return_and_switch_proxy(session)

    # 从队列中获取一个待下载的URL
    def get_url_info_from_queue(self):
        while True:
            url_info = self.redis_connection.blpop(self.url_queue_name, 10)
            if url_info is not None and len(url_info) >= 2:
                url_info = eval(url_info[1].decode('utf-8'))
                if url_info is not None:
                    return url_info

    # 将下载的网页内容放入到队列中
    def put_response_info_to_queue(self, response):
        self.response_buffer.put_response_to_buffer(response)
        del response
