from proxy import validateData
from proxy import fetchData
from proxy import parseData
import time
import threading
import queue
import configparser

# 代理信息键值字段
PROXY_ID = 'id'
PROXY_IP = 'ip'
PROXY_PORT = 'port'
PROXY_ADDRESS = 'address'
PROXY_PROTOCOL = 'protocol'
PROXY_ALIVE_TIME = 'aliveTime'
PROXY_VALIDATE_TIME = 'validateTime'

# 代理网页检索起始页
FETCH_START_PAGE = 1
# 代理网页检索最大截至页
FETCH_END_PAGE = 5

# 代理池大小
PROXY_POOL_SIZE = 10
# 代理池扫描更新间隔
PROXY_POOL_SCAN_INTERVAL = 300
# 代理验证线程数
PROXY_VALIDATE_THREAD_NUM = 3

# 待验证的代理信息列表
unchecked_proxy_list = queue.LifoQueue(300)
# 可用的代理池
proxy_pool = queue.Queue(100)

# 标志量，是否正在扫描代理池
is_scanning = False


# 代理服务守护线程
class ProxyDaemonThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        # 初始化配置
        self.init()

        # 启动代理检验线程
        validate_thread_list = []
        for i in range(PROXY_VALIDATE_THREAD_NUM):
            validate_thread = ProxyValidateThread()
            validate_thread_list.append(validate_thread)
            validate_thread.start()

        # 启动代理池扫描线程
        scan_thread = ProxyPoolScanThread()
        scan_thread.start()

        # 检查是否有线程出现异常并将其重启
        while True:
            # 检查代理验证线程
            for thread in validate_thread_list:
                if thread.status == 'error':
                    validate_thread_list.remove(thread)
                    thread = ProxyValidateThread()
                    validate_thread_list.append(thread)
                    thread.start()
                    print('[info]代理验证线程重新启动')

            # 检查代理池扫描线程
            if scan_thread.status == 'error':
                scan_thread = ProxyPoolScanThread()
                scan_thread.start()
                print('[info]代理池扫描线程重新启动')

            time.sleep(180)

    # 初始化，读取配置文件并配置
    @staticmethod
    def init():
        section = "proxy_core"
        config = configparser.ConfigParser()
        config.read('proxy/proxyConfiguration.conf', encoding='utf8')

        validateData.CONNECT_TIMEOUT = int(config.get(section, "proxyValidate_connectTimeout"))
        validateData.NETWORK_RECONNECT_TIMES = int(config.get(section, "proxyValidate_networkReconnectTimes"))
        fetchData.CONNECT_TIMEOUT = int(config.get(section, "dataFetch_connectTimeout"))
        fetchData.NETWORK_RECONNECT_INTERVAL = int(config.get(section, "dataFetch_networkReconnectInterval"))
        fetchData.NETWORK_RETRY_TIMES = int(config.get(section, "dataFetch_networkReconnectionTimes"))
        global FETCH_START_PAGE
        global FETCH_END_PAGE
        global PROXY_POOL_SIZE
        global PROXY_POOL_SCAN_INTERVAL
        global PROXY_VALIDATE_THREAD_NUM
        FETCH_START_PAGE = int(config.get(section, "proxyCore_fetchStartPage"))
        FETCH_END_PAGE = int(config.get(section, "proxyCore_fetchEndPage"))
        PROXY_POOL_SIZE = int(config.get(section, "proxyCore_proxyPoolSize"))
        PROXY_POOL_SCAN_INTERVAL = int(config.get(section, "proxyCore_proxyPoolScanInterval"))
        PROXY_VALIDATE_THREAD_NUM = int(config.get(section, "proxyCore_proxyValidateThreadNum"))


# 代理检验线程
class ProxyValidateThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.status = 'running'
        # 创建代理验证实例
        self.dataValidateModule = validateData.DataValidateModule()

    def run(self):
        try:
            # print('代理验证线程启动')
            while True:
                # 若正在扫描代理池，则暂停
                while is_scanning:
                    time.sleep(3)

                if proxy_pool.qsize() < PROXY_POOL_SIZE and unchecked_proxy_list.qsize() > 0:
                    unchecked_proxy = unchecked_proxy_list.get()
                    is_available = self.dataValidateModule.validate_proxy_ip(unchecked_proxy)
                    if is_available is True:
                        proxy_pool.put(unchecked_proxy)
                        # print(unchecked_proxy)
                    time.sleep(1)
                else:
                    time.sleep(5)
        except Exception as e:
            print('[error]代理验证线程抛出了一个异常：')
            print(e)
            self.status = 'error'


# 代理池扫描线程，去除代理池中不可用的代理
class ProxyPoolScanThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.status = 'running'
        self.current_page = 1
        # 创建数据抓取模块
        self.dataFetchModule = fetchData.DataFetchModule()
        # 创建数据解析模块
        self.dataParseModule = parseData.DataParseModule()

    def run(self):
        try:
            # print('代理池扫描线程启动')
            while True:
                if proxy_pool.qsize() < PROXY_POOL_SIZE and unchecked_proxy_list.qsize() < PROXY_POOL_SIZE:
                    self.fetch_and_parse_proxy()
                elif proxy_pool.qsize() == PROXY_POOL_SIZE:
                    # print('更新代理池')
                    self.scan_proxy_pool()
                    time.sleep(PROXY_POOL_SCAN_INTERVAL)
                else:
                    time.sleep(60)
        except Exception as e:
            print('[error]代理池扫描线程抛出了一个异常：')
            print(e)
            self.status = 'error'

    # 扫描代理池中的代理
    @staticmethod
    def scan_proxy_pool():
        # 由于待验证线程是先进后出队列，故对代理池进行扫描只需要将其添加到未检查列表，
        # 由代理检验线程对其重新验证并加入回代理池

        global is_scanning
        is_scanning = True
        while proxy_pool.qsize() > 0:
            unchecked_proxy_list.put(proxy_pool.get())
        is_scanning = False

    # 爬取并解析代理
    def fetch_and_parse_proxy(self):
        if self.current_page > FETCH_END_PAGE:
            self.current_page = FETCH_START_PAGE

        response_data = self.dataFetchModule.fetch_proxy_data(self.current_page)
        proxy_data = self.dataParseModule.parse_data(response_data)
        self.current_page += 1

        # 将解析到的代理添加到待验证的代理列表
        for proxy in proxy_data:
            unchecked_proxy_list.put(proxy)


class ProxyService:
    def __init__(self):
        proxy_daemon_thread = ProxyDaemonThread()
        proxy_daemon_thread.start()

    @staticmethod
    def get_proxy():
        return proxy_pool.get()


# if __name__ == '__main__':
#     proxyService = ProxyService()
#     while True:
#         print(proxyService.get_proxy())
