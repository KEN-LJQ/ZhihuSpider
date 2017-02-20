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
PROXY_REQUEST_MAX = 5000
# 发生网络异常重试次数
NETWORK_ERROR_RETRY_TIME = 3
# 发生响应异常重试次数
RESPONSE_ERROR_RETRY_TIME = 10
# 网络连接超时（单位：秒）
NETWORK_TIMEOUT = 30

# 连接管理，每个线程注册的连接
session_bind_list = {}
# 连接使用计数
session_count_list = {}
# 读写锁
thread_lock = threading.Lock()

# 是否启用代理
is_proxy_enable = True

# 代理服务守护线程
proxy_daemon = proxyCore.ProxyScraperDaemon()


# 初始化基本网络配置
def init_network(proxy_setting):
    print('正在初始化网络配置...')
    global is_proxy_enable
    is_proxy_enable = proxy_setting

    # 启动代理守护线程
    if is_proxy_enable is True:
        proxy_daemon.start()

    print('网络配置完毕')


# 为数据爬取线程绑定连接 session
def thread_bind_session(thread_name):
    # 配置 session
    session = requests.session()
    session.headers = requestHeader

    # 配置 session 的代理
    if is_proxy_enable is True:
        # 获取可用的代理
        while True:
            proxy_info = proxyCore.get_proxy()
            if proxy_info is not None:
                break
            time.sleep(5)

        ip = proxy_info['ip']
        port = proxy_info['port']
        protocal = proxy_info['protocal'].lower()
        proxy = {protocal: ip + ':' + port}
        session.proxies = proxy

    # 绑定该 session
    thread_lock.acquire()
    session_bind_list.update({thread_name: session})
    session_count_list.update({thread_name: 0})
    thread_lock.release()


# 更换代理
def switch_proxy(thread_name):
    print('[' + str(thread_name) + ']' + '正在更换代理')

    # 获取绑定的session
    if thread_name in session_bind_list:
        thread_lock.acquire()
        session = session_bind_list[thread_name]
        thread_lock.release()
    else:
        # print('[' + str(thread_name) + ']' + '代理更换失败')
        # return
        # 重新绑定代理
        thread_bind_session(thread_name)
        return

    # 获取可用的 proxy
    while True:
        proxy_info = proxyCore.get_proxy()
        if proxy_info is not None:
            break
        time.sleep(5)

    # 重新配置 session 的 proxy
    ip = proxy_info['ip']
    port = proxy_info['port']
    protocal = proxy_info['protocal'].lower()
    proxy = {protocal: ip + ':' + port}
    session.proxies = proxy

    # 更新
    thread_lock.acquire()
    session_bind_list.update({thread_name: session})
    session_count_list.update({thread_name: 0})
    thread_lock.release()

    print('[' + str(thread_name) + ']' + '代理更换成功')


# 获取指定 URL 的数据
def fetch_data_of_url(url, thread_name):
    if thread_name is None:
        return None

    # 获取该线程绑定的 session
    session = None
    session_count = None
    thread_lock.acquire()
    if thread_name in session_bind_list:
        session = session_bind_list[thread_name]
    if thread_name in session_count_list:
        session_count = session_count_list[thread_name]
    thread_lock.release()

    if session is None or session_count is None:
        thread_bind_session(thread_name)

    # 连接到指定的 URL
    network_error_retry_time = 0
    response_error_retry_time = 0
    while network_error_retry_time < NETWORK_ERROR_RETRY_TIME and response_error_retry_time < RESPONSE_ERROR_RETRY_TIME:
        # 若代理使用次数过多则更换
        if is_proxy_enable is True:
            if session_count >= PROXY_REQUEST_MAX:
                switch_proxy(thread_name)
                session_count = 0
                network_error_retry_time = 0
                response_error_retry_time = 0

        # 尝试连接
        try:
            # 获取 URL 对应的数据
            response = session.get(url, timeout=NETWORK_TIMEOUT)

            # 判断是否获得了正确的响应
            if response.status_code == 200:
                session_count += 1
                thread_lock.acquire()
                session_count_list.update({thread_name: session_count})
                thread_lock.release()
                return response
            elif response.status_code == 429:
                print('[' + str(thread_name) + ']' + '访问太频繁， 响应码为：' + str(response.status_code))
                response_error_retry_time += 1
                time.sleep(40)
            elif response.status_code == 404 or response.status_code == 410:
                return None
            elif is_proxy_enable is True:
                # 代理可能已被屏蔽, 重试
                print('[' + str(thread_name) + ']' + '接收到不正确响应， 响应码为：' + str(response.status_code))
                response_error_retry_time += 1
                continue

        except Exception:
            # 网络异常重试
            network_error_retry_time += 1
            print('[' + str(thread_name) + ']' + '网络异常，正在重新连接...（第' + str(network_error_retry_time) + '次重试)')

    # 若达到最大的重试次数则更换代理
    if is_proxy_enable is True:
        switch_proxy(thread_name)

    # 要求调用方将该 token 重用
    return 'reuse'
