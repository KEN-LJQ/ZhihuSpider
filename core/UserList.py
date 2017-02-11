from core import DBConnector
import threading

# 已分析用户信息的用户 token 缓存列表大小
ANALYSED_CACHE_LIST_SIZE_MAX = 200
# 已分析用户信息的缓存列表保留大小
ANALYSED_CACHE_LIST_SIZE_REMAIN = 10
# 已分析用户信息的用户 token 缓存列表
analysed_cache_list = []
# 已分析用户信息的用户 token 缓存列表信息
analysed_cache_list_size = 0
analysed_cache_list_total = 0
# 已分析用户信息的用户缓存列表读写锁
analysed_cache_list_lock = threading.Lock()

# 未分析用户信息的用户 token 缓存列表大小
CACHE_LIST_SIZE_MAX = 200
# 未分析用户信息的用户 token 缓存列表保留大小
CACHE_LIST_SIZE_REMAIN = 10
# 未分析用户信息的用户 token 缓存列表
cache_list = []
# 未分析用户信息的用户 token 缓存列表信息
cache_list_size = 0
cache_list_total = 0
cache_list_lock = threading.Lock()


# 缓存列表初始化
def cache_list_init():
    global cache_list_total
    global cache_list
    global cache_list_size
    global analysed_cache_list_total
    global analysed_cache_list
    global analysed_cache_list_size

    print('正在配置 token 缓存...')
    # 配置未分析缓存列表
    cache_list_lock.acquire()
    cache_list_total = DBConnector.get_user_token_num()
    if cache_list_total > 0:
        add_into_list(get_token_from_db(CACHE_LIST_SIZE_REMAIN))
        cache_list_size = len(cache_list)
    cache_list_lock.release()

    # 配置已分析缓存列表
    analysed_cache_list_lock.acquire()
    analysed_cache_list_total = DBConnector.get_analysed_token_num()
    if analysed_cache_list_total > 0:
        add_into_analysed_list(get_analysed_token_from_db(ANALYSED_CACHE_LIST_SIZE_REMAIN))
        analysed_cache_list_size = len(analysed_cache_list)
    analysed_cache_list_lock.release()
    print('token 缓存配置成功!!!')


# 缓存列表关闭
def cache_list_close():
    if cache_list_size > 0:
        DBConnector.insert_user_token(cache_list)
    if analysed_cache_list_size > 0:
        DBConnector.insert_analysed_user_token(analysed_cache_list)


# 添加 token 到未分析列表中
def add_into_list(token_list):
    global cache_list
    global cache_list_size
    global cache_list_total

    if token_list is None:
        return

    # 判断是否需要将一部分的 token 存入数据库
    if cache_list_size + len(token_list) >= CACHE_LIST_SIZE_MAX:
        cache_list_lock.acquire()
        temp_list = cache_list[CACHE_LIST_SIZE_REMAIN:]
        cache_list[CACHE_LIST_SIZE_REMAIN:] = []
        cache_list_size = len(cache_list)
        cache_list_lock.release()
        DBConnector.insert_user_token(temp_list)

    # 添加 token
    cache_list_lock.acquire()
    for token in token_list:
        cache_list.append(token)
    cache_list_size += len(token_list)
    cache_list_total += len(token_list)
    cache_list_lock.release()


# 添加 token 到已分析列表中
def add_into_analysed_list(token_list):
    global analysed_cache_list
    global analysed_cache_list_size
    global analysed_cache_list_total

    if token_list is None:
        return

    # 判断是否需要将一部分的已分析 token 保存到数据库中
    if analysed_cache_list_size + len(token_list) >= ANALYSED_CACHE_LIST_SIZE_MAX:
        analysed_cache_list_lock.acquire()
        temp_list = analysed_cache_list[ANALYSED_CACHE_LIST_SIZE_REMAIN:]
        analysed_cache_list[ANALYSED_CACHE_LIST_SIZE_REMAIN:] = []
        analysed_cache_list_size = len(analysed_cache_list)
        analysed_cache_list_lock.release()
        DBConnector.insert_analysed_user_token(temp_list)

    # 添加 token
    analysed_cache_list_lock.acquire()
    for token in token_list:
        analysed_cache_list.append(token)

    # 更新已分析缓存列表信息
    analysed_cache_list_size += len(token_list)
    analysed_cache_list_total += len(token_list)
    analysed_cache_list_lock.release()


# 从未分析列表中取出一个 token
def get_from_list():
    global cache_list
    global cache_list_size
    global cache_list_total

    cache_list_lock.acquire()
    token = None
    if cache_list_size > 0:
        cache_list_size -= 1
        cache_list_total -= 1
        token = cache_list.pop()
    else:
        # 尝试从数据库中取出 token
        if DBConnector.get_user_token_num() > 0:
            add_into_list(get_token_from_db(CACHE_LIST_SIZE_REMAIN))

            cache_list_size -= 1
            cache_list_total -= 1
            token = cache_list.pop()
    cache_list_lock.release()
    return token


# 从已分析列表中取出一个token
def get_from_analysed_list():
    global analysed_cache_list
    global analysed_cache_list_size
    global analysed_cache_list_total

    analysed_cache_list_lock.acquire()
    token = None
    if analysed_cache_list_size > 0:
        analysed_cache_list_size -= 1
        analysed_cache_list_total -= 1
        token = analysed_cache_list.pop()
    else:
        # 尝试从数据库中取出
        if DBConnector.get_analysed_token_num() > 0:
            add_into_analysed_list(get_analysed_token_from_db(ANALYSED_CACHE_LIST_SIZE_REMAIN))
            analysed_cache_list_size -= 1
            analysed_cache_list_total -= 1
            token = analysed_cache_list.pop()
    analysed_cache_list_lock.release()
    return token


# 从数据库未分析列表取出指定数目的 token
def get_token_from_db(num):
    token_list = DBConnector.get_user_token(num)
    for token in token_list:
        DBConnector.delete_user_token(token)
    return token_list


# 从数据库已分析列表中取出指定数目的 token
def get_analysed_token_from_db(num):
    token_list = DBConnector.get_analysed_user_token(num)
    for token in token_list:
        DBConnector.delete_analysed_user_token(token)
    return token_list


# 获取剩余未分析的 token 数目
def get_token_number():
    return cache_list_total


# 获取剩余已分析的 token 数目
def get_analysed_token_number():
    return analysed_cache_list
