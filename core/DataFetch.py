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
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}

# 当个代理最大请求次数
PROXY_REQUEST_MAX = 20000
# 发生网络错误时重新连接次数
NETWORK_RETRY_TIME = 3
# 网络连接超时（单位：秒）
NETWORK_TIMEOUT = 30

# # 用户信息分析连接 session
# user_info_session = None
# user_info_session_usage_times = 0
# # following & follower 列表分析连接 session
# user_list_session = None
# user_list_session_usage_times = 0

# 连接管理，每个线程注册的连接
session_bind_list = {}
# 连接使用计数
session_count_list = {}
# 读写锁
thread_lock = threading.Lock()

# 代理服务守护线程
proxy_daemon = proxyCore.ProxyScraperDaemon()


# 初始化基本网络配置
def init_network():
    print('正在初始化网络配置...')

    # 启动代理守护线程
    proxy_daemon.start()

    print('网络配置完毕')


# 为数据爬取线程绑定连接 session
def thread_bind_session(thread_name):
    # 获取可用的代理
    while True:
        proxy_info = proxyCore.get_proxy()
        if proxy_info is not None:
            break
        time.sleep(5)

    # 配置 session
    ip = proxy_info['ip']
    port = proxy_info['port']
    protocal = proxy_info['protocal'].lower()
    proxy = {protocal: ip + ':' + port}
    session = requests.session()
    session.headers = requestHeader
    session.proxies = proxy

    # 绑定该 session
    thread_lock.acquire()
    session_bind_list.update({thread_name: session})
    session_count_list.update({thread_name: 0})
    thread_lock.release()

    # print('信息抓取线程[' + str(thread_name) + ']' + '连接初始化完毕')


# 更换代理
def switch_proxy(thread_name):
    print('[' + str(thread_name) + ']' + '正在更换代理')

    # 获取绑定的session
    # session = None
    if thread_name in session_bind_list:
        thread_lock.acquire()
        session = session_bind_list[thread_name]
        thread_lock.release()
    else:
        print('[' + str(thread_name) + ']' + '代理更换失败')
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
        return None

    # 连接到指定的 URL
    retry_time = 0
    while retry_time <= NETWORK_RETRY_TIME:
        # 若代理使用次数过多则更换
        if session_count >= PROXY_REQUEST_MAX:
            switch_proxy(thread_name)

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
    return None


# # 配置基本网络设置
# def network_init():
#     global user_info_session
#     global user_list_session
#     print('正在配置网络...')
#     # proxyCore.proxy_init()
#     # 启动代理守护线程
#     proxy_daemon.start()
#
#     # 配置 user_info_session
#     user_info_session = requests.session()
#     user_info_session.headers = requestHeader
#     while True:
#         user_info_proxy = proxyCore.get_proxy()
#         if user_info_proxy is not None:
#             break
#         time.sleep(5)
#     ip = user_info_proxy['ip']
#     port = user_info_proxy['port']
#     protocal = user_info_proxy['protocal'].lower()
#     user_info_session.proxies = {protocal: ip + ":" + port}
#     print('用户信息抓取连接初始化完毕')
#
#     # 配置 user_list_session
#     user_list_session = requests.session()
#     user_list_session.headers = requestHeader
#     while True:
#         user_list_proxy = proxyCore.get_proxy()
#         if user_list_proxy is not None:
#             break
#         time.sleep(5)
#     ip = user_list_proxy['ip']
#     port = user_list_proxy['port']
#     protocal = user_list_proxy['protocal'].lower()
#     user_list_session.proxyies = {protocal: ip + ":" + port}
#     print('用户关注列表抓取连接初始化完毕')
#
#     print('配置网络成功!!!')
#
#
# # 更换 user_info_proxy 代理
# def change_user_info_proxy():
#     global user_info_session_usage_times
#     print('正在更换代理...')
#     while True:
#         proxy = proxyCore.get_proxy()
#         if proxy is not None:
#             break
#         time.sleep(5)
#     ip = proxy['ip']
#     port = proxy['port']
#     protocal = proxy['protocal'].lower()
#     user_info_session.proxies = {protocal: ip + ":" + port}
#     user_info_session_usage_times = 0
#     print("更换代理成功!!!")
#
#
# # 更换 user_list_proxy 代理
# def change_user_list_proxy():
#     global user_list_session_usage_times
#     print('正在更换代理...')
#     while True:
#         proxy = proxyCore.get_proxy()
#         if proxy is not None:
#             break
#         time.sleep(5)
#     ip = proxy['ip']
#     port = proxy['port']
#     protocal = proxy['protocal'].lower()
#     user_list_session.proxies = {protocal: ip + ":" + port}
#     user_list_session_usage_times = 0
#     print("更换代理成功!!!")
#
#
# # 获取用户信息,连接到指定的 URL 并返回数据
# def fetch_user_info_from_url(url):
#     global user_info_session_usage_times
#     retry_time = 0
#     while retry_time <= NETWORK_RETRY_TIME:
#         # 若代理使用次数过多则更换
#         if user_info_session_usage_times >= PROXY_REQUEST_MAX:
#             change_user_info_proxy()
#
#         # 尝试连接
#         try:
#             response = user_info_session.get(url, timeout=NETWORK_TIMEOUT)
#             user_info_session_usage_times += 1
#             return response
#         except requests.exceptions.RequestException:
#             # 重试
#             retry_time += 1
#             print('网络异常，正在重新连接...')
#         except Exception:
#             # 重试
#             retry_time += 1
#             print('网络异常，正在重新连接...')
#     return None
#
#
# # 获取用户列表,连接到指定的 URL 并返回数据
# def fetch_user_list_from_url(url):
#     global user_list_session_usage_times
#     retry_time = 0
#     while retry_time <= NETWORK_RETRY_TIME:
#         # 若代理使用次数过多则更换
#         if user_list_session_usage_times >= PROXY_REQUEST_MAX:
#             change_user_list_proxy()
#
#         # 尝试连接
#         try:
#             response = user_list_session.get(url, timeout=NETWORK_TIMEOUT)
#             user_list_session_usage_times += 1
#             return response
#         except requests.exceptions.RequestException:
#             # 重试
#             retry_time += 1
#             print('网络异常，正在重新连接...')
#         except Exception:
#             # 重试
#             retry_time += 1
#             print('网络异常，正在重新连接...')
#     return None

# if __name__ == '__main__':
#     dict_test = {'item1': 'value1', 'item2': 'value2'}
#     elem = dict_test['item1']
#     elem = 'test'
#     dict_test.update({'item1': elem})
#     print(dict_test)
