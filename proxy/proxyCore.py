from proxy import validateData
from proxy import fetchData
from proxy import parseData
import time
import threading

# 当前存在的代理IP总数
proxy_total = 0

# 代理网页检索起始页
start_page = 1
# 代理网页检索最大截至页
end_page = 3
# 当前检索页面
current_page = start_page

# 代理IP缓存列表大小
PROXY_LIST_SIZE = 5
# 代理IP缓存列表
proxy_list = []
proxy_list_temp = []
# 缓存列表同步锁
proxy_list_lock = threading.Lock()
# 缓存列表扫描更新间隔
PROXY_LIST_SCAN_INTERVAL = 60

PROXY_ID = 'id'
PROXY_IP = 'ip'
PROXY_PORT = 'port'
PROXY_ADDRESS = 'address'
PROXY_PROTOCAL = 'protocal'
PROXY_ALIVE_TIME = 'aliveTime'
PROXY_VALIDATE_TIME = 'validateTime'


# 代理IP爬虫
def proxy_scrape_core():
    global current_page
    global proxy_total

    # 设置检索页面
    if current_page > end_page:
        current_page = start_page

    # 开始检索新的代理IP
    current_proxy_list = []
    while proxy_total < PROXY_LIST_SIZE:
        # 当前待验证列表中无代理IP时，再次检索
        if len(current_proxy_list) <= 0:
            # print("开始检索代理IP，当前检索页面：" + str(current_page) + "\n")
            current_proxy_list = parseData.parse_data(fetchData.scrape_data(current_page))
            current_page += 1

        # 对当前列表中的代理进行验证
        time.sleep(1)
        if len(current_proxy_list) > 0:
            current_proxy_info = current_proxy_list.pop()
            # 检查是否存在
            is_exist = is_proxy_exist(current_proxy_info)
            if is_exist is False:
                # 检查是否存活
                is_available = validateData.validate_proxy_ip(current_proxy_info)
                if is_available is True:
                    proxy_list_lock.acquire()
                    proxy_list.append(current_proxy_info)
                    proxy_total += 1
                    proxy_list_lock.release()
                    # print('验证成功，代理IP有效，并保存到数据库\n')
                # else:
                #     print('验证失败，代理IP无效\n')
            # else:
            #     print("验证失败，代理IP已经存在\n")


# 代理爬虫守护线程
class ProxyScraperDaemon(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        print('代理IP服务守护线程启动')
        start_proxy_scrape()


# 启动代理爬虫
def start_proxy_scrape():
    # 初始化
    global proxy_total
    global proxy_list
    global proxy_list_temp
    proxy_total = 0

    # 运行进程
    while True:
        # 对缓存列表中的代理进行存活性检查
        # print('开始存活检查')
        proxy_list_lock.acquire()
        for proxy in proxy_list:
            is_alive = validateData.validate_proxy_ip(proxy)
            if is_alive is True:
                proxy_list_temp.append(proxy)
        proxy_list = proxy_list_temp
        proxy_total = len(proxy_list)
        proxy_list_temp = []
        proxy_list_lock.release()

        # 判断是否需要获取新的代理
        if len(proxy_list) < PROXY_LIST_SIZE:
            # print('需要获取新代理')
            proxy_scrape_core()

        print('更新代理缓存列表成功')
        # 线程睡眠
        time.sleep(PROXY_LIST_SCAN_INTERVAL)


# 判断指定的代理是否已经存在
def is_proxy_exist(proxy):
    if proxy is None:
        return True

    if proxy in proxy_list:
        return True
    else:
        return False


# 返回一条代理信息,若无则返回空
def get_proxy():
    global proxy_total
    global proxy_list

    proxy = None
    proxy_list_lock.acquire()
    if len(proxy_list) > 0:
        proxy = proxy_list.pop()
        proxy_total -= 1
    proxy_list_lock.release()
    return proxy
