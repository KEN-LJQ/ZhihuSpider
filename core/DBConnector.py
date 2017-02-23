import pymysql
import threading

# 知乎用户信息字段
# 用户头像
USER_AVATAR_URL_TEMPLATE = 'avatarUrlTemplate'
# 用户标识
USER_URL_TOKEN = 'urlToken'
# 用户名
USER_NAME = 'name'
# 用户自我介绍
USER_HEADLINE = 'headline'
# 用户居住地
USER_LOCATIONS = 'locations'
# 用户所在行业
USER_BUSINESS = 'business'
# 用户职业经历
USER_EMPLOYMENTS = 'employments'
# 用户教育经历
USER_EDUCATIONS = 'educations'
# 用户个人描述
USER_DESCRIPTION = 'description'
# 用户新浪微博 URL
USER_SINAWEIBO_URL = 'sinaWeiboUrl'
# 用户性别
USER_GENDER = 'gender'
# 正在关注用户的数目
USER_FOLLOWING_COUNT = 'followingCount'
# 关注者的数目
USER_FOLLOWER_COUNT = 'followerCount'
# 该用户回答问题的数目
USER_ANSWER_COUNT = 'answerCount'
# 用户提问数目
USER_QUESTION_COUNT = 'questionCount'
# 用户获得赞同的数目
USER_VOTE_UP_COUNT = 'voteupCount'

# 数据库配置
DB_HOST = 'localhost'
DB_USERNAME = 'root'
DB_PASSWORD = 'XXX'
DB_DATABASE = 'zhihu_spider'
DB_CHARSET = 'utf8'

# SQL
# 未分析 token
INSERT_TOKEN = 'insert ignore into user_list_cache(user_token) values (%s)'
SELECT_TOKEN = 'select user_token from user_list_cache limit %s'
DELETE_TOKEN = 'delete from user_list_cache where user_token = %s'
COUNT_TOKEN = 'select count(*) from user_list_cache'
# 已分析 token
INSERT_ANALYSED_TOKEN = 'insert ignore into analysed_user_list_cache(user_token) values (%s)'
SELECT_ANALYSED_TOKEN = 'select user_token from analysed_user_list_cache limit %s'
DELETE_ANALYSED_TOKEN = 'delete from analysed_user_list_cache where user_token = %s'
COUNT_ANALYSED_TOKEN = 'select count(*) from analysed_user_list_cache'

SELECT_USER_INFO_BY_TOKEN = 'select user_avator_url, user_token, user_name, user_headline, user_location, ' \
                            'user_business, user_employments, user_educations, user_description, user_sinaweibo_url, ' \
                            'user_gender, user_following_count, user_follower_count, user_answer_count, ' \
                            'user_question_count, user_voteup_count from user_info where user_token = %s'
INSERT_USER_INFO = 'insert ignore into user_info(user_avator_url, user_token, user_name, user_headline, ' \
                   'user_location, user_business, user_employments, user_educations, user_description, ' \
                   'user_sinaweibo_url, user_gender, user_following_count, user_follower_count, user_answer_count, ' \
                   'user_question_count, user_voteup_count) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,' \
                   '%s,%s,%s,%s,%s,%s,%s)'

# 数据库连接
connection = None

connection_lock = threading.Lock()


# 数据库连接初始化
def connection_init():
    global connection
    connection = pymysql.connect(host=DB_HOST,
                                 user=DB_USERNAME,
                                 passwd=DB_PASSWORD,
                                 db=DB_DATABASE,
                                 charset=DB_CHARSET)


# 销毁数据库连接
def connection_close():
    if connection is not None:
        connection.close()


# 保存未分析用户 token 到数据库
def insert_user_token(token_list):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    for token in token_list:
        cur.execute(INSERT_TOKEN, [token])
    connection.commit()
    cur.close()
    connection_lock.release()


# 从数据库中获取指定数目的 token
def get_user_token(num):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(SELECT_TOKEN, [num])
    token_list = []
    for token in cur.fetchall():
        token_list.append(token[0])
    cur.close()
    connection_lock.release()
    return token_list


# 从数据库中删除指定 token 的记录
def delete_user_token(token):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(DELETE_TOKEN, [token])
    connection.commit()
    cur.close()
    connection_lock.release()


# 获得数据库中未分析 token 的数目
def get_user_token_num():
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(COUNT_TOKEN)
    data = cur.fetchone()
    cur.close()
    connection_lock.release()
    return data[0]


# 获取指定数目的已分析 token
def get_analysed_user_token(num):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(SELECT_ANALYSED_TOKEN, [num])
    token_list = []
    for token in cur.fetchall():
        token_list.append(token[0])
    cur.close()
    connection_lock.release()
    return token_list


# 从数据库中删除指定 token 的记录
def delete_analysed_user_token(token):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(DELETE_ANALYSED_TOKEN, [token])
    connection.commit()
    cur.close()
    connection_lock.release()


# 保存已分析用户 token
def insert_analysed_user_token(token_list):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    for token in token_list:
        cur.execute(INSERT_ANALYSED_TOKEN, [token])
    connection.commit()
    cur.close()
    connection_lock.release()


# 获取数据库中已分析 token 的数目
def get_analysed_token_num():
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(COUNT_ANALYSED_TOKEN)
    data = cur.fetchone()
    cur.close()
    connection_lock.release()
    return data[0]


# 查询指定 token 对应的用户信息
def select_user_info_by_token(token):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(SELECT_USER_INFO_BY_TOKEN, [token])
    elem = cur.fetchone()
    data = None
    if elem is not None:
        data = {USER_AVATAR_URL_TEMPLATE: elem[0],
                USER_URL_TOKEN: elem[1],
                USER_NAME: elem[2],
                USER_HEADLINE: elem[3],
                USER_LOCATIONS: elem[4],
                USER_BUSINESS: elem[5],
                USER_EMPLOYMENTS: elem[6],
                USER_EDUCATIONS: elem[7],
                USER_DESCRIPTION: elem[8],
                USER_SINAWEIBO_URL: elem[9],
                USER_GENDER: elem[10],
                USER_FOLLOWING_COUNT: elem[11],
                USER_FOLLOWER_COUNT: elem[12],
                USER_ANSWER_COUNT: elem[13],
                USER_QUESTION_COUNT: elem[14],
                USER_VOTE_UP_COUNT: elem[15]}
    cur.close()
    connection_lock.release()
    return data


# 保存用户信息
def add_user_info(user_info):
    if connection is None:
        return None
    connection_lock.acquire()
    cur = connection.cursor()
    cur.execute(INSERT_USER_INFO, [user_info[USER_AVATAR_URL_TEMPLATE],
                                   user_info[USER_URL_TOKEN],
                                   user_info[USER_NAME],
                                   user_info[USER_HEADLINE],
                                   user_info[USER_LOCATIONS],
                                   user_info[USER_BUSINESS],
                                   user_info[USER_EMPLOYMENTS],
                                   user_info[USER_EDUCATIONS],
                                   user_info[USER_DESCRIPTION],
                                   user_info[USER_SINAWEIBO_URL],
                                   user_info[USER_GENDER],
                                   user_info[USER_FOLLOWING_COUNT],
                                   user_info[USER_FOLLOWER_COUNT],
                                   user_info[USER_ANSWER_COUNT],
                                   user_info[USER_QUESTION_COUNT],
                                   user_info[USER_VOTE_UP_COUNT]])
    connection.commit()
    cur.close()
    connection_lock.release()
