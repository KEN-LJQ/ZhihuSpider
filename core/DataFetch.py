import requests
from proxy import proxyCore
import time
import threading

# 请求头信息
requestHeader = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Encoding": "gzip, deflate, sdch, br",
                 "Accept-Language": "zh-CN,zh;q=0.8",
                 "Cache-Control": "max-age=0",
                 "Host": "www.zhihu.com",
                 "Upgrade-Insecure-Requests": "1",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
                               " Chrome/56.0.2924.87 Safari/537.36"}

# 当个代理最大请求次数
PROXY_USAGE_MAX = 10000
# 发生网络异常重试次数
NETWORK_RECONNECT_TIMES = 3
# 发生响应异常重试次数
RESPONSE_ERROR_RETRY_TIME = 5
# 网络连接超时（单位：秒）
CONNECT_TIMEOUT = 30


class DataFetchModule:
    def __init__(self, is_proxy_enable):
        self.is_proxy_enable = is_proxy_enable
        # 连接管理，每个线程注册的连接
        self.session_bind_list = {}
        # 连接使用计数
        self.session_count_list = {}
        # 读写锁
        self.thread_lock = threading.Lock()
        # 启动代理模块
        if self.is_proxy_enable is True:
            self.proxyService = proxyCore.ProxyService()

    # 为数据爬取线程绑定连接 session
    def thread_bind_session(self, thread_name):
        # 配置 session
        session = requests.session()
        session.headers = requestHeader

        # 配置 session 的代理
        if self.is_proxy_enable is True:
            # 获取可用的代理
            while True:
                proxy_info = self.proxyService.get_proxy()
                if proxy_info is not None:
                    break
                time.sleep(5)

            ip = proxy_info[proxyCore.PROXY_IP]
            port = proxy_info[proxyCore.PROXY_PORT]
            protocol = proxy_info[proxyCore.PROXY_PROTOCOL].lower()
            proxy = {protocol: ip + ':' + port}
            session.proxies = proxy

        # 绑定该 session
        self.thread_lock.acquire()
        self.session_bind_list.update({thread_name: session})
        self.session_count_list.update({thread_name: 0})
        self.thread_lock.release()

    # 更换代理
    def switch_proxy(self, thread_name):
        print('[' + str(thread_name) + ']' + '正在更换代理')
        # 获取绑定的session
        if thread_name in self.session_bind_list:
            self.thread_lock.acquire()
            session = self.session_bind_list[thread_name]
            self.thread_lock.release()
        else:
            # 重新绑定代理
            self.thread_bind_session(thread_name)
            return

        # 获取可用的 proxy
        while True:
            proxy_info = self.proxyService.get_proxy()
            if proxy_info is not None:
                break
            time.sleep(5)

        # 重新配置 session 的 proxy
        ip = proxy_info[proxyCore.PROXY_IP]
        port = proxy_info[proxyCore.PROXY_PORT]
        protocol = proxy_info[proxyCore.PROXY_PROTOCOL].lower()
        proxy = {protocol: ip + ':' + port}
        session.proxies = proxy

        # 更新
        self.thread_lock.acquire()
        self.session_bind_list.update({thread_name: session})
        self.session_count_list.update({thread_name: 0})
        self.thread_lock.release()
        print('[' + str(thread_name) + ']' + '代理更换成功')

    # 获取指定 URL 的数据
    def fetch_data_of_url(self, url, thread_name):
        if thread_name is None:
            return None

        # 获取该线程绑定的 session
        session = None
        session_count = None
        self.thread_lock.acquire()
        if thread_name in self.session_bind_list:
            session = self.session_bind_list[thread_name]
        if thread_name in self.session_count_list:
            session_count = self.session_count_list[thread_name]
            self.thread_lock.release()

        if session is None or session_count is None:
            self.thread_bind_session(thread_name)

        # 连接到指定的 URL
        network_reconnect_times = 0
        response_error_retry_time = 0
        while network_reconnect_times < NETWORK_RECONNECT_TIMES and response_error_retry_time < RESPONSE_ERROR_RETRY_TIME:
            # 若代理使用次数过多则更换
            if self.is_proxy_enable is True:
                if session_count >= PROXY_USAGE_MAX:
                    self.switch_proxy(thread_name)
                    session_count = 0
                    network_reconnect_times = 0
                    response_error_retry_time = 0

            # 尝试连接
            try:
                # 获取 URL 对应的数据
                response = session.get(url, timeout=CONNECT_TIMEOUT)

                # 判断是否获得了正确的响应
                if response.status_code == 200:
                    session_count += 1
                    self.thread_lock.acquire()
                    self.session_count_list.update({thread_name: session_count})
                    self.thread_lock.release()
                    return response
                elif response.status_code == 429:
                    print('[' + str(thread_name) + ']' + '访问太频繁，稍候重新访问，响应码为：' + str(response.status_code))
                    response_error_retry_time += 1
                    time.sleep(40)
                elif response.status_code == 404 or response.status_code == 410:
                    return None
                elif self.is_proxy_enable is True:
                    # 代理可能已被屏蔽, 重试
                    print('[' + str(thread_name) + ']' + '接收到不正确响应， 响应码为：' + str(response.status_code))
                    response_error_retry_time += 1
                    continue

            except Exception:
                # 网络异常重试
                network_reconnect_times += 1
                print('[' + str(thread_name) + ']' + '网络异常，正在重新连接...（第' + str(network_reconnect_times) + '次重试)')

        # 若达到最大的重试次数则更换代理
        if self.is_proxy_enable is True:
            self.switch_proxy(thread_name)

        # 要求调用方将该 token 重用
        return 'reuse'
