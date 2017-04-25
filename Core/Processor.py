import threading
import logging
import html
import json
import time
import queue
from Core.Logger import log
from bs4 import BeautifulSoup

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

# 关注关系字段
# 关注者
FOLLOW_FROM = 'followFrom'
# 被关注者
FOLLOW_TO = 'followTo'


# 下载数据处理器
class Processor:
    __slots__ = ('process_thread_num', 'redis_connection', 'token_filter', 'response_buffer',
                 'is_parser_following_list', 'is_parser_follower_list', 'processor_list', 'is_parser_follow_relation')

    # 初始化
    def __init__(self, process_thread_num, is_parser_following_list, is_parser_follower_list, is_parser_follow_relation,
                 redis_connection, response_buffer):
        # 设置数据处理器数量
        self.process_thread_num = process_thread_num
        # 设置 Redis 连接
        self.redis_connection = redis_connection
        # 创建 Token 过滤器
        self.token_filter = TokenFilter(self.redis_connection)
        # 设置 response 缓存队列
        self.response_buffer = response_buffer

        # 是否解析正在关注列表
        self.is_parser_following_list = is_parser_following_list
        # 是否解析关注者列表
        self.is_parser_follower_list = is_parser_follower_list
        # 是否解析关注关系
        self.is_parser_follow_relation = is_parser_follow_relation

        # 创建处理器
        self.processor_list = []
        for i in range(process_thread_num):
            process_thread = ProcessThread('thread' + str(i), self.redis_connection, self.token_filter,
                                           self.response_buffer, self.is_parser_following_list,
                                           self.is_parser_follower_list, self.is_parser_follow_relation)
            self.processor_list.append(process_thread)

        if log.isEnabledFor(logging.INFO):
            log.info('Processor 模块初始化完毕')

    # 载入初始 token
    def load_init_data(self, token_list):
        if token_list is None:
            return

        for token in token_list:
            # 封装 URL 信息
            url_info = ['info', URL_PUBLIC + token + URL_PINS, token]
            self.redis_connection.rpush('userInfoURLQueue', url_info)
            del url_info

        if log.isEnabledFor(logging.INFO):
            log.info('初始用户Token载入完毕')

    # 启动数据处理器
    def start_processor(self):
        # 启动处理线程
        for process_thread in self.processor_list:
            process_thread.start()

        if log.isEnabledFor(logging.INFO):
            log.info('Processor 模块启动成功')

    # 异常检查
    def check_and_restart(self):
        for process_thread in self.processor_list:
            if process_thread.thread_status == 'error':
                thread_id = process_thread.thread_id
                self.processor_list.remove(process_thread)
                del process_thread
                new_thread = ProcessThread(thread_id, self.redis_connection, self.token_filter,
                                           self.response_buffer, self.is_parser_following_list,
                                           self.is_parser_follower_list, self.is_parser_follow_relation)
                self.processor_list.append(new_thread)
                new_thread.start()

                if log.isEnabledFor(logging.ERROR):
                    log.error('数据处理器线程[' + thread_id + ']重新启动')

# URL 组件
URL_PUBLIC = 'https://www.zhihu.com/people/'
URL_PINS = '/pins'
str1 = 'https://www.zhihu.com/api/v4/members/'
str2 = '/followees?offset='
str3 = '/followers?offset='
str4 = '&limit='


# 处理线程
class ProcessThread(threading.Thread):
    __slots__ = ('thread_id', 'thread_status', 'redis_connection', 'token_filter', 'response_buffer',
                 'user_info_url_queue', 'follow_info_url_queue', 'persistent_cache', 'is_parser_following_list',
                 'is_parser_follower_list', 'follow_relation_persistent_cache', 'is_parser_follow_relation')

    def __init__(self, thread_id, redis_connection, token_filter, response_buffer, is_parser_following_list,
                 is_parser_follower_list, is_parser_follow_relation):
        threading.Thread.__init__(self)
        # 设置线程名称
        self.thread_id = thread_id
        # 设置线程状态
        self.thread_status = 'working'
        # 设置 Redis 连接
        self.redis_connection = redis_connection
        # 设置 token 过滤器
        self.token_filter = token_filter

        # 是否解析正在关注列表
        self.is_parser_following_list = is_parser_following_list
        # 是否解析关注者列表
        self.is_parser_follower_list = is_parser_follower_list
        # 是否解析关注列表
        self.is_parser_follow_relation = is_parser_follow_relation

        # 下载数据队列
        self.response_buffer = response_buffer
        # user info url 队列名称
        self.user_info_url_queue = 'userInfoURLQueue'
        # follower & following list url 队列名称
        self.follow_info_url_queue = 'followInfoURLQueue'
        # 用户信息数据数据持久化缓存队列名称
        self.persistent_cache = 'persistentCache'
        # 关注关系持久化缓存队列名称
        self.follow_relation_persistent_cache = 'followRelationPersistentCache'

    def run(self):
        if log.isEnabledFor(logging.INFO):
            log.info('数据处理线程' + self.thread_id + '启动')

        try:
            while True:
                # 获取Response数据
                response = self.response_buffer.get_response_from_buffer()

                if response is None or len(response) < 2:
                    continue

                # 判断Response类型
                response_type = response[0]

                # 分派给对应的处理方法
                if response_type == 'info':
                    self.parse_user_info(response)
                elif response_type == 'list':
                    self.parse_follow_info(response)
                time.sleep(0.1)

        except Exception as e:
            self.thread_status = 'error'
            if log.isEnabledFor(logging.ERROR):
                log.exception(e)

    # 解析用户信息(生成的Follow URL Info内容[list, url, token, followingList/followerList])
    def parse_user_info(self, response_info):
        # 获取ResponseInfo中的信息
        data = response_info[1]
        token = response_info[2]

        # 提取JSON信息
        user_info_entities = None
        try:
            bs_obj = BeautifulSoup(data, 'html.parser')
            data_json = bs_obj.find('div', attrs={'id': 'data'})
            if data_json is None:
                return
            else:
                data_json = data_json['data-state']

            # 字符串处理
            # 处理转义字符
            data_json = html.unescape(data_json)
            # 处理html标签
            data_json = BeautifulSoup(data_json, 'html.parser').text

            # 转换为JSON对象
            data_json = json.loads(data_json)

            # 提取实体
            if 'entities' not in data_json:
                return
            entities = data_json['entities']

            # 提取用户信息
            if 'users' not in entities:
                return
            users = entities['users']

            # 提取目标用户信息
            if token not in users:
                return
            user_info = users[token]

            # 提取目标用户的个人信息
            avatar_url_template = None
            name = None
            headline = None
            locations = []
            business = None
            employments = []
            educations = []
            description = None
            gender = None
            following_count = None
            follower_count = None
            answer_count = None
            question_count = None
            voteup_count = None
            if USER_AVATAR_URL_TEMPLATE in user_info:
                avatar_url_template = user_info[USER_AVATAR_URL_TEMPLATE]

            if USER_NAME in user_info:
                name = user_info[USER_NAME]

            if USER_HEADLINE in user_info:
                headline = user_info[USER_HEADLINE]

            if USER_LOCATIONS in user_info:
                for location in user_info[USER_LOCATIONS]:
                    locations.append(location['name'])

            if USER_BUSINESS in user_info:
                business = user_info[USER_BUSINESS]['name']

            if USER_EMPLOYMENTS in user_info:
                for employment in user_info[USER_EMPLOYMENTS]:
                    elem = {}
                    if 'job' in employment:
                        job = employment['job']['name']
                        elem.update({'job': job})
                    if 'company' in employment:
                        company = employment['company']['name']
                        elem.update({'company': company})
                    employments.append(elem)

            if USER_EDUCATIONS in user_info:
                for education in user_info[USER_EDUCATIONS]:
                    if 'school' in education:
                        school = education['school']['name']
                        educations.append(school)

            if USER_DESCRIPTION in user_info:
                description = user_info[USER_DESCRIPTION]

            if USER_GENDER in user_info:
                gender = user_info[USER_GENDER]

            if USER_FOLLOWING_COUNT in user_info:
                following_count = user_info[USER_FOLLOWING_COUNT]

            if USER_FOLLOWER_COUNT in user_info:
                follower_count = user_info[USER_FOLLOWER_COUNT]

            if USER_ANSWER_COUNT in user_info:
                answer_count = user_info[USER_ANSWER_COUNT]

            if USER_QUESTION_COUNT in user_info:
                question_count = user_info[USER_QUESTION_COUNT]

            if USER_VOTE_UP_COUNT in user_info:
                voteup_count = user_info[USER_VOTE_UP_COUNT]

            # 构造用户信息实体
            user_info_entities = {USER_AVATAR_URL_TEMPLATE: avatar_url_template,
                                  USER_URL_TOKEN: token,
                                  USER_NAME: name,
                                  USER_HEADLINE: headline,
                                  USER_LOCATIONS: locations,
                                  USER_BUSINESS: business,
                                  USER_EMPLOYMENTS: employments,
                                  USER_EDUCATIONS: educations,
                                  USER_DESCRIPTION: description,
                                  USER_GENDER: gender,
                                  USER_FOLLOWING_COUNT: following_count,
                                  USER_FOLLOWER_COUNT: follower_count,
                                  USER_ANSWER_COUNT: answer_count,
                                  USER_QUESTION_COUNT: question_count,
                                  USER_VOTE_UP_COUNT: voteup_count}

        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error('User info 数据解析错误')
                log.exception(e)

        # 处理提取的信息
        if user_info_entities is None:
            return

        # 再次检查用户是否已经添加,若已经添加则不再继续
        if self.token_filter.check_token(token) is True:
            return

        # 标记提取的用户信息
        self.token_filter.mark_token(token)

        # 生成 Following List URL
        if self.is_parser_following_list is True:
            pipe = self.redis_connection.pipeline()
            following_count = user_info_entities[USER_FOLLOWING_COUNT]
            if following_count is not None:
                offset = 0
                limit = 20
                while offset < following_count:
                    url_info = ['list', self.generate_following_info_url(token, offset, limit), token, 'followingList']
                    offset += limit
                    pipe.rpush(self.follow_info_url_queue, url_info)
                pipe.execute()

        # 生成 Follower List URL
        if self.is_parser_follower_list is True:
            pipe = self.redis_connection.pipeline()
            follower_count = user_info_entities[USER_FOLLOWER_COUNT]
            if follower_count is not None:
                offset = 0
                limit = 20
                while offset < follower_count:
                    url_info = ['list', self.generate_follower_info_url(token, offset, limit), token, 'followerList']
                    offset += limit
                    pipe.rpush(self.follow_info_url_queue, url_info)
                pipe.execute()

        # 保存提取到的用户信息
        if log.isEnabledFor(logging.DEBUG):
            log.info('成功获取一个用户的详细信息')
        self.redis_connection.rpush(self.persistent_cache, user_info_entities)

    # 解析follower & following 信息(生成的User URLInfo内容格式[info, url, token])
    def parse_follow_info(self, response_info):
        # 获取ResponseInfo中的信息
        data = response_info[1]

        # 提取JSON
        follow_list_token = []
        try:
            # 转为JSON 对象
            json_data = json.loads(data)

            # 提取用户列表信息
            if 'data' not in json_data:
                return
            data = json_data['data']

            # 提取用户 token
            for follow_info in data:
                if 'url_token' in follow_info:
                    token = follow_info['url_token']
                    # 检查重复并添加
                    if self.token_filter.check_token(token) is False:
                        follow_list_token.append(token)

        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error('Follower & Following List 数据解析错误')
            if log.isEnabledFor(logging.DEBUG):
                log.exception(e)
            return

        # 添加token url 到队列中
        for token in follow_list_token:
            # 封装 URL 信息(List)
            url_info = ['info', self.generate_user_info_url(token), token]
            self.redis_connection.rpush(self.user_info_url_queue, url_info)

        # 提取用户的关注关系(即 following)
        # (返回的Response内容[info, data, token, followingList/followerList])
        if self.is_parser_follow_relation is True:
            # 关注列表类型
            follow_list_type = response_info[3]
            # 用户Token
            token = response_info[2]
            if follow_list_type == 'followingList':
                pipe = self.redis_connection.pipeline()
                for following_token in follow_list_token:
                    # 封装关注关系
                    follow_relation = {FOLLOW_FROM: token,
                                       FOLLOW_TO: following_token}
                    pipe.rpush(self.follow_relation_persistent_cache, follow_relation)
                pipe.execute()

    # 生成user info url
    @staticmethod
    def generate_user_info_url(token):
        return "{0}{1}{2}".format(URL_PUBLIC, token, URL_PINS)

    # 生成 follower url
    @staticmethod
    def generate_follower_info_url(token, offset, limit):
        return "{0}{1}{2}{3}{4}{5}".format(str1, token, str3, str(offset), str4, str(limit))

    # 生成 following url
    @staticmethod
    def generate_following_info_url(token, offset, limit):
        return "{0}{1}{2}{3}{4}{5}".format(str1, token, str2, str(offset), str4, str(limit))


# Token 过滤器
class TokenFilter:
    __slots__ = ('redis_connection', 'token_set_name')

    def __init__(self, redis_connection):
        # Redis 连接
        self.redis_connection = redis_connection
        # Token Set 名称
        self.token_set_name = 'tokenFilterSet'

    # 标记 Token
    def mark_token(self, token):
        self.redis_connection.sadd(self.token_set_name, token)

    # 检查 Token 是否已经存在
    def check_token(self, token):
        return self.redis_connection.sismember(self.token_set_name, token)

    # 从数据库中导入已经存在的Token
    def import_data(self):
        pass


# response 数据缓存
class ResponseBuffer:
    __slots__ = 'response_buffer'

    def __init__(self):
        self.response_buffer = queue.Queue(500)

    def get_response_from_buffer(self):
        return self.response_buffer.get()

    def put_response_to_buffer(self, response):
        self.response_buffer.put(response)
        del response
