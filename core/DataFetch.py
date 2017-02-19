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
PROXY_REQUEST_MAX = 20000
# 发生网络错误时重新连接次数
NETWORK_RETRY_TIME = 3
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
    count = session_count_list[thread_name]
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
    retry_time = 0
    while retry_time < NETWORK_RETRY_TIME:
        # 若代理使用次数过多则更换
        if is_proxy_enable is True:
            if session_count >= PROXY_REQUEST_MAX:
                switch_proxy(thread_name)
                session_count = 0

        # 尝试连接
        try:
            response = session.get(url, timeout=NETWORK_TIMEOUT)
            session_count += 1
            thread_lock.acquire()
            session_count_list.update({thread_name: session_count})
            thread_lock.release()
            return response
        except requests.exceptions.RequestException:
            # 重试
            retry_time += 1
            print('[' + str(thread_name) + ']' + '网络异常，正在重新连接...(第' + str(retry_time) + '次重试)')
        except Exception:
            # 重试
            retry_time += 1
            print('[' + str(thread_name) + ']' + '网络异常，正在重新连接...（第' + str(retry_time) + '次重试)')

    # 若达到最大的重试次数则更换代理并返回 None
    if is_proxy_enable is True:
        switch_proxy(thread_name)

    return None
