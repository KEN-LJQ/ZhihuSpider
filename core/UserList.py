from core import DBConnector

# 用户 token 缓存列表大小
CACHE_LIST_SIZE_MAX = 500

# 缓存列表保留大小
CACHE_LIST_SIZE_REMAIN = 100

# 缓存列表
cache_list = []
# cache_list = set()
cache_list_size = 0
cache_list_total = 0


# 缓存列表初始化
def cache_list_init():
    global cache_list_total
    global cache_list
    global cache_list_size

    print('正在配置 token 缓存...')
    cache_list_total = DBConnector.get_user_token_num()
    if cache_list_total > 0:
        add_into_list(get_token_from_db(CACHE_LIST_SIZE_REMAIN))
        # cache_list = DBConnector.get_user_token(CACHE_LIST_SIZE_MAX)
        cache_list_size = len(cache_list)
    print('token缓存配置成功!!!')


# 缓存列表关闭
def cache_list_close():
    if cache_list_size > 0:
        DBConnector.insert_user_token(cache_list)


# 添加 token 到列表中
def add_into_list(token_list):
    global cache_list
    global cache_list_size
    global cache_list_total

    if token_list is None:
        return

    # 判断是否需要将一部分的 token 存入数据库
    if cache_list_size + len(token_list) >= CACHE_LIST_SIZE_MAX:
        temp_list = cache_list[CACHE_LIST_SIZE_REMAIN:]
        cache_list[CACHE_LIST_SIZE_REMAIN:] = []
        cache_list_size = len(cache_list)
        DBConnector.insert_user_token(temp_list)

    # 添加 token
    for token in token_list:
        cache_list.append(token)
    # cache_list.update(token_list)
    cache_list_size += len(token_list)
    cache_list_total += len(token_list)


# 从列表中取出一个 token
def get_from_list():
    global cache_list
    global cache_list_size
    global cache_list_total

    if cache_list_size > 0:
        cache_list_size -= 1
        cache_list_total -= 1
        return cache_list.pop()
    else:
        # 尝试从数据库中取出 token
        if DBConnector.get_user_token_num() > 0:
            add_into_list(get_token_from_db(CACHE_LIST_SIZE_REMAIN))
            # cache_list = DBConnector.get_user_token(CACHE_LIST_SIZE_MAX)
            # cache_list_size = len(cache_list)

            cache_list_size -= 1
            cache_list_total -= 1
            return cache_list.pop()
        else:
            return None


# 从数据库取出指定数目的 token
def get_token_from_db(num):
    token_list = DBConnector.get_user_token(num)
    for token in token_list:
        DBConnector.delete_user_token(token)
    return token_list


# 获取剩余待分析的 token 数目
def get_token_number():
    return cache_list_total


# test_data = ['yi-ya-68-77', 'xiao-xi-ya-17', 'chen-yu-63-80', 'fingerprints', 'hei-hai-27', 'liang-jia-yang', 'ran-xin-lin-23-27', 'twocold-27-52', 'nana-72-99', 'ling-bo-li-41', 'qi-hai-tao-57', 'xiao-gou-87', 'MyWorseHalf', 'elapse08', 'lizhenyi95', 'zhang-kai-rui-86', 'wuchangyexue', 'listening-43', 'hou-yu-wen-92', 'wang-xiao-yin-25-6']
# if __name__ == '__main__':
#     locations_string = ';'.join(str(x) for x in test_data)
#     print(locations_string)
#     add_into_list(test_data)
#     elem = get_from_list()
#     print(elem)
#     list1 = ['1', '2', '3']
#     list2 = ['a', 'b', 'c']
#     set1 = set(list2)
#     set1.update(list1)
#     print(set1)
#     print(set1.pop())
#     set_test = set()
#     set_test.add('a')
#     set_test.add('b')
#     set_test.add('c')
#     set_test.add('d')
#     # temp = set_test[1:]
#     # print(temp)
#     print(set_test[1:])
