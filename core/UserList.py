from core import DBConnector
# import threading
import queue


# 使用 Queue 实现
# 已分析用户信息的用户 token 缓存列表大小
MAX_ANALYSED_CACHE_QUEUE_SIZE = 1000
# 已分析用户信息的缓存列表保留大小
MIN_ANALYSED_CACHE_QUEUE_SIZE = 1
# 已分析用户信息的用户 token 缓存列表
analysed_cache_queue = queue.Queue(MAX_ANALYSED_CACHE_QUEUE_SIZE)

# 未分析用户信息的用户 token 缓存列表大小
MAX_CACHE_QUEUE_SIZE = 1000
# 未分析用户信息的用户 token 缓存列表保留大小
MIN_CACHE_QUEUE_SIZE = 1
# 未分析用户信息的用户 token 缓存列表
cache_queue = queue.Queue(MAX_CACHE_QUEUE_SIZE)


# 初始化队列
def init_queue():
    print('正在配置用户 Token 缓存列表...')
    # 配置未分析用户信息列表
    token_total = DBConnector.get_user_token_num()
    if token_total > 0:
        temp_list = get_token_from_db(MIN_CACHE_QUEUE_SIZE)
        for token in temp_list:
            cache_queue.put(token)

    # 配置已分析用户信息列表
    token_total = DBConnector.get_analysed_token_num()
    if token_total > 0:
        temp_list = get_analysed_token_from_db(MIN_ANALYSED_CACHE_QUEUE_SIZE)
        for token in temp_list:
            analysed_cache_queue.put(token)
    print('用户 Token 缓存列表配置完毕!!!')


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


# 添加 Token 到 cache_queue 中
def add_token_into_cache_queue(token_list):
    # 判断队列中是否有足够位置存放，否则将一部分放入内存
    if cache_queue.qsize() + len(token_list) >= MAX_CACHE_QUEUE_SIZE:
        temp_list = []
        while cache_queue.qsize() > MIN_CACHE_QUEUE_SIZE:
            temp_list.append(cache_queue.get())
        DBConnector.insert_user_token(temp_list)

    # 将该 Token 加入到队列中
    for token in token_list:
        cache_queue.put(token)


# 添加 Token 到 analysed_cache_queue 中
def add_token_into_analysed_cache_queue(token_list):
    # 判断队列中是否有足够位置存放，否则将一部分放入内存
    if analysed_cache_queue.qsize() + len(token_list) >= MAX_ANALYSED_CACHE_QUEUE_SIZE:
        temp_list = []
        while analysed_cache_queue.qsize() > MIN_ANALYSED_CACHE_QUEUE_SIZE:
            temp_list.append(analysed_cache_queue.get())
        DBConnector.insert_analysed_user_token(temp_list)

    # 将该 Token 加入到队列中
    for token in token_list:
        analysed_cache_queue.put(token)


# 从 cache_queue 中取出一个 Token
def get_token_from_cache_queue():
    if cache_queue.qsize() > 0:
        # 直从队列中取出
        return cache_queue.get()
    elif DBConnector.get_user_token_num() > 0:
        # 队列为空，先从数据库中取出一部分数据
        temp_list = get_token_from_db(MIN_CACHE_QUEUE_SIZE)
        for token in temp_list:
            cache_queue.put(token)
        return cache_queue.get()
    else:
        return None


# 从analysed_cache_queue 中取出一个 Token
def get_token_form_analysed_cache_queue():
    if analysed_cache_queue.qsize() > 0:
        # 直接从队列中取出
        return analysed_cache_queue.get()
    elif DBConnector.get_analysed_token_num() > 0:
        # 队列为空，先从数据库中取出一部分数据
        temp_list = get_analysed_token_from_db(MIN_ANALYSED_CACHE_QUEUE_SIZE)
        for token in temp_list:
            analysed_cache_queue.put(token)
        return analysed_cache_queue.get()
    else:
        return None
