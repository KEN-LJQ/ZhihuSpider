import threading
import logging
import time
from Core.Logger import log

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


# 负责用户数据的持久化
class DataPersistent:
    __slots__ = ('persistent_cache_size', 'db_connection', 'redis_connection', 'persistent_thread')

    # 初始化
    def __init__(self, persistent_cache_size, db_connection, redis_connection):
        # 设置数据持久化缓存大小
        self.persistent_cache_size = persistent_cache_size
        # 设置数据库连接
        self.db_connection = db_connection
        # 设置Redis连接
        self.redis_connection = redis_connection
        # 创建数据库持久化线程
        self.persistent_thread = PersistentThread(self.db_connection, self.redis_connection, self.persistent_cache_size)

        if log.isEnabledFor(logging.INFO):
            log.info('DataPersistent 模块初始化完毕')

    def get_current_user_info_num(self):
        return self.persistent_thread.get_current_user_info_num()

    # 启动DataPersistent模块
    def start_data_persistent(self):
        # log.info('DataPersistent 模块启动成功')
        # 启动线程
        self.persistent_thread.start()

        if log.isEnabledFor(logging.INFO):
            log.info('DataPersistent 模块启动成功')

        # 线程异常检测并重启
    def check_and_restart(self):
        if self.persistent_thread.thread_status == 'error':
            self.persistent_thread = PersistentThread(self.db_connection, self.redis_connection,
                                                      self.persistent_cache_size)
            self.persistent_thread.start()
            if log.isEnabledFor(logging.INFO):
                log.info('DataPersistent模块持久化线程中重新启动')


# 数据插入SQL语句
INSERT_USER_INFO = 'insert ignore into user_info(user_avator_url, user_token, user_name, user_headline, ' \
                   'user_location, user_business, user_employments, user_educations, user_description, ' \
                   'user_gender, user_following_count, user_follower_count, user_answer_count, ' \
                   'user_question_count, user_voteup_count) values(%s,%s,%s,%s,%s,%s,%s,%s,' \
                   '%s,%s,%s,%s,%s,%s,%s)'
# 数据数量查询语句
COUNT_USER_INFO = 'select count(*) from user_info'


class PersistentThread(threading.Thread):
    def __init__(self, db_connection, redis_connection, persistent_cache_size):
        threading.Thread.__init__(self)
        # 设置数据库连接
        self.db_connection = db_connection
        # 设置Redis连接
        self.redis_connection = redis_connection
        # 设置缓存大小
        self.persistent_cache_size = persistent_cache_size
        # 数据持久化缓存队列名称
        self.persistent_cache = 'persistentCache'
        # 线程状态
        self.thread_status = 'working'
        # Operation Lock
        self.lock = threading.Lock()

    def get_current_user_info_num(self):
        self.lock.acquire()
        # 获取存放在数据库中的用户数量
        cursor = self.db_connection.cursor()
        cursor.execute(COUNT_USER_INFO)
        data = cursor.fetchone()
        cursor.close()
        user_num_db = data[0]

        # 获取缓存队列中的用户数量
        user_num_cache = self.redis_connection.llen(self.persistent_cache)
        self.lock.release()
        return user_num_cache + user_num_db

    def run(self):
        debug_info = None
        try:
            while True:
                current_cache_size = self.redis_connection.llen(self.persistent_cache)
                if current_cache_size >= self.persistent_cache_size:
                    cursor = self.db_connection.cursor()
                    for i in range(current_cache_size):
                        user_info = self.redis_connection.lpop(self.persistent_cache)
                        debug_info = user_info
                        if user_info is not None:
                            user_info = self.convert_user_info(eval(user_info.decode('utf-8')))
                            cursor.execute(INSERT_USER_INFO, [user_info[USER_AVATAR_URL_TEMPLATE],
                                                              user_info[USER_URL_TOKEN],
                                                              user_info[USER_NAME],
                                                              user_info[USER_HEADLINE],
                                                              user_info[USER_LOCATIONS],
                                                              user_info[USER_BUSINESS],
                                                              user_info[USER_EMPLOYMENTS],
                                                              user_info[USER_EDUCATIONS],
                                                              user_info[USER_DESCRIPTION],
                                                              user_info[USER_GENDER],
                                                              user_info[USER_FOLLOWING_COUNT],
                                                              user_info[USER_FOLLOWER_COUNT],
                                                              user_info[USER_ANSWER_COUNT],
                                                              user_info[USER_QUESTION_COUNT],
                                                              user_info[USER_VOTE_UP_COUNT]])
                    self.db_connection.commit()
                    cursor.close()

                # 检查时间间隔
                time.sleep(180)

        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error('用户数据持久化线程异常退出')
                log.exception(e)
            log.debug(debug_info)
            self.thread_status = 'error'

    # 将用户数据转换为适合数据库存储的格式
    @staticmethod
    def convert_user_info(user_info):
        # 将居住地转换为‘；’分隔的字符串
        locations_string = ';'.join(str(x) for x in user_info[USER_LOCATIONS])
        user_info[USER_LOCATIONS] = locations_string

        # 将职业经历转换为‘XXX（XXX）’，并以‘；’ 分隔的字符串
        employments_list = []
        for employment in user_info[USER_EMPLOYMENTS]:
            temp = ''
            if 'company' in employment:
                temp += str(employment['company'])
            if 'job' in employment:
                temp += '-' + str(employment['job'])
            employments_list.append(temp)
        employments_string = ';'.join(str(x) for x in employments_list)
        user_info[USER_EMPLOYMENTS] = employments_string

        # 将教育经历转换为‘；’分隔的字符串
        educations_string = ';'.join(str(x) for x in user_info[USER_EDUCATIONS])
        user_info[USER_EDUCATIONS] = educations_string

        return user_info
