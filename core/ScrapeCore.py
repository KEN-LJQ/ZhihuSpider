import core.DBConnector as DBConnector
import core.DataFetch as DataFetch
import core.DataParser as DataParser
import core.UserList as UserList
import time
import threading

# 默认关注与被关注列表每页的大小
PAGE_SIZE = 20
# 爬虫动作时间间隔（单位：秒）
SCRAPE_TIME_INTERVAL = 1
# 正在关注页面时最大爬取页面范围
FOLLOWING_PAGE_MAX = 150
# 关注着页面最大爬取页面范围
FOLLOWER_PAGE_MAX = 150
# 是否分析正在关注列表
ANALYSE_FOLLOWING_LIST = True
# 是否分析关注者列表
ANALYSE_FOLLOWER_LIST = False

# 爬虫起始 token
start_token = None


# 用户信息分析线程
class UserInfoScrapeThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        user_info_scrape()


# 用户关注列表分析线程
class UserListScrapeThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        user_list_scrape()


# 爬取用户信息
def user_info_scrape():
    while True:
        # 从未分析 token 缓存列表中获取一个可用的token
        while True:
            token = UserList.get_from_list()
            if token is not None:
                if is_token_available(token) is True:
                    # print('获取到了一个可用的未分析 token')
                    break
            else:
                time.sleep(0.5)

            # 分析 token 对应用户的个人信息，并保存
        response = DataFetch.fetch_user_info_from_url(generate_user_info_url(token))
        user_info = DataParser.parse_user_information(response.text, token)
        if user_info is None:
            continue

        # 保存该用户信息
        DBConnector.add_user_info(DataParser.convert_user_info(user_info))
        print("搜索到一个新的用户:" + user_info['name'])

        # 将该 token 放入到已分析缓存列表
        UserList.add_into_analysed_list([token])

        # 爬取时间间隔
        time.sleep(SCRAPE_TIME_INTERVAL)


# 爬取用户列表
def user_list_scrape():
    while True:
        # 从已分析 token 缓存列表中获取一个可用的token
        while True:
            # print('正在获取已分析的 token')
            token = UserList.get_from_analysed_list()
            if token is not None:
                break
            time.sleep(1)

        # 获取该 token 对应的用户信息
        user_info = None
        retry = 3
        while retry > 0:
            # print('获取 token 对应的用户信息')
            # print(token)
            user_info = DBConnector.select_user_info_by_token(token)
            # print(user_info)
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
            if following_page_size > FOLLOWING_PAGE_MAX:
                following_page_size = FOLLOWING_PAGE_MAX

            # 开始分析
            cur_page = 1
            while cur_page <= following_page_size:
                following_list_response = DataFetch.fetch_user_list_from_url(
                    generate_following_list_url(token, cur_page))
                following_list = DataParser.parse_user_list(following_list_response.text, token)
                UserList.add_into_list(following_list)
                cur_page += 1
                time.sleep(SCRAPE_TIME_INTERVAL)

        # 分析关注者列表
        if ANALYSE_FOLLOWER_LIST is True:
            # 计算页码范围
            follower_page_size = 1
            if DataParser.USER_FOLLOWER_COUNT in user_info:
                follower_page_size = calculate_max_page(user_info[DataParser.USER_FOLLOWER_COUNT])
            if follower_page_size > FOLLOWER_PAGE_MAX:
                follower_page_size = FOLLOWER_PAGE_MAX

            # 开始分析
            cur_page = 1
            while cur_page <= follower_page_size:
                # print('分析 token 对用用户的关注者列表,,页码：' + str(cur_page))
                follower_list_response = DataFetch.fetch_user_list_from_url(generate_follower_list_url(token, cur_page))
                follower_list = DataParser.parse_user_list(follower_list_response.text, token)
                UserList.add_into_list(follower_list)
                cur_page += 1
                time.sleep(SCRAPE_TIME_INTERVAL)


# # 爬虫核心进程
# def core_process():
#     # 初始化
#     DBConnector.connection_init()
#     DataFetch.network_init()
#     UserList.cache_list_init()
#
#     # 放入爬虫起始 token
#     if start_token is not None:
#         UserList.add_into_list([start_token])
#
#     # 开始爬虫
#     while UserList.get_token_number() > 0:
#         # 从 token 缓存列表中获取一个可用的token
#         while True:
#             token = UserList.get_from_list()
#             if is_token_available(token) is True:
#                 break
#
#         # 分析 token 对应用户的个人信息，并保存
#         response = DataFetch.fetch_user_info_from_url(generate_user_info_url(token))
#         user_info = DataParser.parse_user_information(response.text, token)
#         if user_info is None:
#             continue
#
#         # 保存该用户信息
#         DBConnector.add_user_info(DataParser.convert_user_info(user_info))
#         print("搜索到一个新的用户:" + user_info['name'])
#
#         # 分析正在关注列表
#         if ANALYSE_FOLLOWING_LIST is True:
#             # 计算页码范围
#             following_page_size = 1
#             if DataParser.USER_FOLLOWING_COUNT in user_info:
#                 following_page_size = calculate_max_page(user_info[DataParser.USER_FOLLOWING_COUNT])
#             if following_page_size > FOLLOWING_PAGE_MAX:
#                 following_page_size = FOLLOWING_PAGE_MAX
#
#             # 开始分析
#             cur_page = 1
#             while cur_page <= following_page_size:
#                 following_list_response = DataFetch.fetch_data_from_url(generate_following_list_url(token, cur_page))
#                 following_list = DataParser.parse_user_list(following_list_response.text, token)
#                 UserList.add_into_list(following_list)
#                 cur_page += 1
#                 time.sleep(SCRAPE_TIME_INTERVAL)
#
#         # 分析关注者列表
#         if ANALYSE_FOLLOWER_LIST is True:
#             # 计算页码范围
#             follower_page_size = 1
#             if DataParser.USER_FOLLOWER_COUNT in user_info:
#                 follower_page_size = calculate_max_page(user_info[DataParser.USER_FOLLOWER_COUNT])
#             if follower_page_size > FOLLOWER_PAGE_MAX:
#                 follower_page_size = FOLLOWER_PAGE_MAX
#
#             # 开始分析
#             cur_page = 1
#             while cur_page <= follower_page_size:
#                 # print('分析 token 对用用户的关注者列表,,页码：' + str(cur_page))
#                 follower_list_response = DataFetch.fetch_data_from_url(generate_follower_list_url(token, cur_page))
#                 follower_list = DataParser.parse_user_list(follower_list_response.text, token)
#                 UserList.add_into_list(follower_list)
#                 cur_page += 1
#                 time.sleep(SCRAPE_TIME_INTERVAL)
#
#     # 关闭资源
#     UserList.cache_list_close()
#     DataFetch.network_close()
#     DBConnector.connection_close()


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


# 运行线程
user_info_scrape_thread = UserInfoScrapeThread()
user_list_scrape_thread = UserListScrapeThread()


# 启动
def start_scrape():
    # core_process()
    # 初始化
    DBConnector.connection_init()
    DataFetch.network_init()
    UserList.cache_list_init()

    # 放入爬虫起始 token
    if start_token is not None:
        UserList.add_into_list([start_token])

    # 启动线程
    user_info_scrape_thread.start()
    user_list_scrape_thread.start()


if __name__ == '__main__':
    # 初始化
    DBConnector.connection_init()
    print(DBConnector.select_user_info_by_token('limi'))
