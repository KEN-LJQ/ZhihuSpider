import core.DBConnector as DBConnector
import core.DataFetch as DataFetch
import core.DataParser as DataParser
import core.UserList as UserList
import proxy.proxyCore as proxyCore
import time
import threading

# 默认关注与被关注列表每页的大小
PAGE_SIZE = 20
# 爬虫动作时间间隔（单位：秒）
SCRAPE_TIME_INTERVAL = 2
# 正在关注页面时最大爬取页面范围(若为负数则代表不作限制)
FOLLOWING_PAGE_MAX = 200
# 关注着页面最大爬取页面范围(若为负数则代表不作限制)
FOLLOWER_PAGE_MAX = 100
# 是否分析正在关注列表
ANALYSE_FOLLOWING_LIST = True
# 是否分析关注者列表
ANALYSE_FOLLOWER_LIST = True

# 用户信息抓取线程数量
USER_INFO_SCRAPE_THREAD_NUM = 8
# 用户列表抓取线程数量
USER_LIST_SCRAPE_THREAD_NUM = 13

# 是否使用代理
IS_PROXY_ENABLE = True

# 爬虫起始 token
start_token = None


# 用户信息分析线程
class UserInfoScrapeThread(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.status = 'running'

    def run(self):
        try:
            user_info_scrape(self.thread_name)
        except:
            self.status = 'error'


# 用户关注列表分析线程
class UserListScrapeThread(threading.Thread):
    def __init__(self, thread_name):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.status = 'running'

    def run(self):
        try:
            user_list_scrape(self.thread_name)
        except:
            self.status = 'error'


# 爬取用户信息
def user_info_scrape(thread_name):
    print('用户信息爬取线程[' + thread_name + ']正在等待连接...')

    # 为该线程绑定 session
    DataFetch.thread_bind_session(thread_name)

    print('用户信息爬取线程[' + thread_name + ']开始运行')
    while True:
        # 从未分析 token 缓存列表中获取一个可用的token
        while True:
            token = UserList.get_token_from_cache_queue()
            if token is not None:
                if is_token_available(token) is True:
                    break
            else:
                time.sleep(0.5)

        # 抓取 token 对应用户的个人信息，并保存
        response = DataFetch.fetch_data_of_url(generate_user_info_url(token), thread_name)

        # 判断返回的数据是否有效，若有效再继续对数据进行分析
        if response is not None:
            if response == 'reuse':
                # 将该 token 放回队列
                UserList.add_token_into_cache_queue([token])
            else:
                # 添加到待分析队列
                DataParser.add_data_into_user_info_cache_queue({DataParser.QUEUE_ELEM_HTML: response.text,
                                                                DataParser.QUEUE_ELEM_TOKEN: token,
                                                                DataParser.QUEUE_ELEM_THREAD_NAME: thread_name})

        # 爬取时间间隔
        time.sleep(SCRAPE_TIME_INTERVAL)


# 爬取用户列表
def user_list_scrape(thread_name):
    print('用户列表爬取线程[' + thread_name + ']正在等待连接...')

    # 为该线程绑定 session
    DataFetch.thread_bind_session(thread_name)

    print('用户列表爬取线程[' + thread_name + ']开始运行')
    while True:
        # 从已分析 token 缓存列表中获取一个可用的token
        while True:
            token = UserList.get_token_form_analysed_cache_queue()
            if token is not None:
                break
            time.sleep(0.5)

        # 获取该 token 对应的用户信息
        user_info = None
        retry = 3
        while retry > 0:
            user_info = DBConnector.select_user_info_by_token(token)
            if user_info is None:
                # print('is None')
                retry -= 1
                time.sleep(1)
            else:
                break

        if user_info is None:
            continue

        # 分析正在关注列表
        if ANALYSE_FOLLOWING_LIST is True:
            # 计算页码范围
            following_page_size = 1
            if DataParser.USER_FOLLOWING_COUNT in user_info:
                following_page_size = calculate_max_page(user_info[DataParser.USER_FOLLOWING_COUNT])
            if 0 < FOLLOWING_PAGE_MAX < following_page_size:
                following_page_size = FOLLOWING_PAGE_MAX

            # 开始分析
            cur_page = 1
            while cur_page <= following_page_size:
                # 获取数据
                following_list_response = DataFetch.fetch_data_of_url(
                    generate_following_list_url(token, cur_page), thread_name)

                # 判断返回的数据是否有效，若有效再对数据进行分析
                if following_list_response is not None:
                    # 添加到分析队列
                    DataParser.add_data_into_user_list_cache_queue({
                        DataParser.QUEUE_ELEM_HTML: following_list_response.text,
                        DataParser.QUEUE_ELEM_TOKEN: token,
                        DataParser.QUEUE_ELEM_THREAD_NAME: thread_name})
                    cur_page += 1

                time.sleep(SCRAPE_TIME_INTERVAL)

        # 分析关注者列表
        if ANALYSE_FOLLOWER_LIST is True:
            # 计算页码范围
            follower_page_size = 1
            if DataParser.USER_FOLLOWER_COUNT in user_info:
                follower_page_size = calculate_max_page(user_info[DataParser.USER_FOLLOWER_COUNT])
            if follower_page_size > FOLLOWER_PAGE_MAX > 0:
                follower_page_size = FOLLOWER_PAGE_MAX

            # 开始分析
            cur_page = 1
            while cur_page <= follower_page_size:
                # 获取数据
                follower_list_response = DataFetch.fetch_data_of_url(
                    generate_follower_list_url(token, cur_page), thread_name)

                # 判断返回的数据是否有效，若有效再继续对数据进行分析
                if follower_list_response is not None:
                    # 添加到待分析队列
                    DataParser.add_data_into_user_list_cache_queue({
                        DataParser.QUEUE_ELEM_HTML: follower_list_response.text,
                        DataParser.QUEUE_ELEM_TOKEN: token,
                        DataParser.QUEUE_ELEM_THREAD_NAME: thread_name})
                    cur_page += 1
                time.sleep(SCRAPE_TIME_INTERVAL)


# 判断 token 是否可用
def is_token_available(token):
    # 判断能否在数据库查询到该 token 对应的信息
    if DBConnector.select_user_info_by_token(token) is not None:
        return False
    else:
        return True


URL_PUBLIC = 'https://www.zhihu.com/people/'
URL_ANSWER = '/answers'
URL_FOLLOWING = '/following'
URL_FOLLOWER = '/followers'
URL_PAGE = '?page='


# 生成 token 对应用户的个人主页 URL
def generate_user_info_url(token):
    return URL_PUBLIC + token + URL_ANSWER


# 生成指定页码和 token 对应的正在关注列表 URL
def generate_following_list_url(token, page):
    return URL_PUBLIC + token + URL_FOLLOWING + URL_PAGE + str(page)


# 生成指定页码和 token 对应的关注者列表 URL
def generate_follower_list_url(token, page):
    return URL_PUBLIC + token + URL_FOLLOWER + URL_PAGE + str(page)


# 计算页码的范围最大值
def calculate_max_page(total):
    if total % PAGE_SIZE == 0:
        return total // PAGE_SIZE
    else:
        return total // PAGE_SIZE + 1


# 启动
def start_scrape():
    # 初始化
    DBConnector.connection_init()
    DataFetch.init_network(IS_PROXY_ENABLE)
    UserList.init_queue()

    # 放入爬虫起始 token
    if start_token is not None:
        UserList.add_token_into_cache_queue([start_token])

    # 启动数据解析线程
    user_info_parser_thread = DataParser.UserInfoDataParserThread()
    user_list_parser_thread = DataParser.UserListDataParserThread()
    user_info_parser_thread.start()
    user_list_parser_thread.start()

    # 用户信息爬取线程列表
    user_info_scrape_thread_list = []
    # 创建并启动用户信息爬取线程
    thread_count = 1
    while thread_count <= USER_INFO_SCRAPE_THREAD_NUM:
        user_info_scrape_thread = UserInfoScrapeThread('user-info-scrape-thread' + str(thread_count))
        user_info_scrape_thread_list.append(user_info_scrape_thread)
        user_info_scrape_thread.start()
        thread_count += 1

    # 用户列表爬取线程列表
    user_list_scrape_thread_list = []
    # 创建并启动用户列表爬取线程
    thread_count = 1
    while thread_count <= USER_LIST_SCRAPE_THREAD_NUM:
        user_list_scrape_thread = UserListScrapeThread('user-list-scrape-thread' + str(thread_count))
        user_list_scrape_thread_list.append(user_list_scrape_thread)
        user_list_scrape_thread.start()
        thread_count += 1

    # 检测线程是否出现异常停止，并重新启动
    while True:
        # 检测用户信息解析线程
        if user_info_parser_thread.status == 'error':
            user_info_parser_thread = DataParser.UserInfoDataParserThread()
            user_info_parser_thread.start()

        # 检测用户列表解析线程
        if user_list_parser_thread.status == 'error':
            user_list_parser_thread = DataParser.UserListDataParserThread()
            user_list_parser_thread.start()

        if IS_PROXY_ENABLE is True:
            if DataFetch.proxy_daemon.status == 'error':
                DataFetch.proxy_daemon = proxyCore.ProxyScraperDaemon()
                DataFetch.proxy_daemon.start()

        # 检测用户信息爬取线程
        for thread in user_info_scrape_thread_list:
            if thread.status == 'error':
                thread_name = thread.thread_name
                user_info_scrape_thread_list.remove(thread)
                new_thread = UserInfoScrapeThread(thread_name)
                user_info_scrape_thread_list.append(new_thread)
                print('[' + thread_name + ']重新启动线程')
                new_thread.start()

        # 检测用户列表爬取线程
        for thread in user_list_scrape_thread_list:
            if thread.status == 'error':
                thread_name = thread.thread_name
                user_list_scrape_thread_list.remove(thread)
                new_thread = UserListScrapeThread(thread_name)
                user_list_scrape_thread_list.append(new_thread)
                print('[' + thread_name + ']重新启动线程')
                new_thread.start()

        # 检测间隔
        time.sleep(180)
