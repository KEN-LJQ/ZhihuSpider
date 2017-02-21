from proxy import validateData
from proxy import fetchData
from proxy import parseData
import time
import threading
import queue

PROXY_ID = 'id'
PROXY_IP = 'ip'
PROXY_PORT = 'port'
PROXY_ADDRESS = 'address'
PROXY_PROTOCAL = 'protocal'
PROXY_ALIVE_TIME = 'aliveTime'
PROXY_VALIDATE_TIME = 'validateTime'

# 代理网页检索起始页
FETCH_START_PAGE = 1
# 代理网页检索最大截至页
FETCH_END_PAGE = 5

# 代理池大小
PROXY_POOL_SIZE = 10
# 缓存列表扫描更新间隔
PROXY_LIST_SCAN_INTERVAL = 300
# 代理验证线程数
VALIDATE_THREAD_NUM = 3

# 待验证的代理信息列表
unchecked_proxy_list = queue.LifoQueue(300)
# 可用的代理池
proxy_pool = queue.Queue(100)

# 标志量，是否正在扫描代理池
is_scanning = False


# 启动代理服务
def start_proxy_core():
    # 启动代理检验线程
    validate_thread_list = []
    for i in range(VALIDATE_THREAD_NUM):
        validate_thread = ProxyValidateThread()
        validate_thread_list.append(validate_thread)
        validate_thread.start()

    # 启动代理池扫描线程
    scan_thread = ProxyPoolScanThread()
    scan_thread.start()


# 代理检验线程
class ProxyValidateThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        # print('代理验证线程启动')
        while True:
            # 若正在扫描代理池，则暂停
            while is_scanning:
                time.sleep(3)

            if proxy_pool.qsize() < PROXY_POOL_SIZE and unchecked_proxy_list.qsize() > 0:
                unchecked_proxy = unchecked_proxy_list.get()
                is_available = validateData.validate_proxy_ip(unchecked_proxy)
                if is_available is True:
                    proxy_pool.put(unchecked_proxy)
                    # print(unchecked_proxy)
                time.sleep(1)
            else:
                time.sleep(5)


# 代理池扫描线程，去除代理池中不可用的代理
class ProxyPoolScanThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        # print('代理池扫描线程启动')
        while True:
            if proxy_pool.qsize() < PROXY_POOL_SIZE and unchecked_proxy_list.qsize() < PROXY_POOL_SIZE:
                fetch_and_parse_proxy()
            elif proxy_pool.qsize() == PROXY_POOL_SIZE:
                # print('更新代理池')
                scan_proxy_pool()
                time.sleep(PROXY_LIST_SCAN_INTERVAL)
            else:
                time.sleep(60)


# 扫描代理池中的代理
def scan_proxy_pool():
    # 由于待验证线程是先进后出队列，故对代理池进行扫描只需要将其添加到未检查列表，
    # 由代理检验线程对其重新验证并加入回代理池

    global is_scanning
    is_scanning = True
    while proxy_pool.qsize() > 0:
        unchecked_proxy_list.put(proxy_pool.get())
    is_scanning = False


current_page = 1


# 爬取并解析代理
def fetch_and_parse_proxy():
    global current_page
    if current_page > FETCH_END_PAGE:
        current_page = FETCH_START_PAGE

    response_data = fetchData.fetch_proxy_data(current_page)
    proxy_data = parseData.parse_data(response_data)
    current_page += 1

    # 将解析到的代理添加到待验证的代理列表
    for proxy in proxy_data:
        unchecked_proxy_list.put(proxy)


# 从代理池中获取一个代理
def get_proxy():
    return proxy_pool.get()
