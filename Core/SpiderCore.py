import configparser
import logging
import redis
import time
import pymysql
import gc
from Core.Logger import log
from Core.Downloader import Downloader
from Core.Scheduler import Scheduler
from Core.Processor import Processor
from Core.DataPersistent import DataPersistent
from Core.EmailService import EmailService
from Core.Processor import ResponseBuffer
from Core.AccountLogin import AccountManager


class SpiderCore:
    def __init__(self):
        # 默认配置
        # downloader 模块配置
        self.is_proxy_service_enable = False
        self.session_pool_size = 20
        self.download_thread_num = 10
        self.network_retry_times = 3
        self.connect_timeout = 30
        self.download_interval = 3

        # Processor 模块配置
        self.process_thread_num = 2
        self.is_parser_following_list = True
        self.is_parser_follower_list = False
        self.is_parser_follow_relation = False

        # Scheduler 模块配置
        self.url_rate = 8

        # DataPersistent 模块配置
        self.persistent_cache_size = 1000
        self.follow_relation_persistent_cache_size = 1000

        # 邮件服务配置
        self.is_email_service_enable = False
        self.smtp_server_host = ''
        self.smtp_server_port = 25
        self.smtp_server_password = ''
        self.smtp_from_addr = ''
        self.smtp_to_addr = ''
        self.smtp_email_header = ''
        self.smtp_send_interval = 3600

        # redis 数据库配置
        self.redis_host = ''
        self.redis_port = 6379
        self.redis_db = 0
        self.redis_password = ''

        # MySQL 数据库配置
        self.mysql_host = ''
        self.mysql_username = ''
        self.mysql_password = ''
        self.mysql_database = ''
        self.mysql_charset = 'utf8'

        # 知乎账户配置
        self.is_login_by_cookie = True
        self.z_c0 = ''
        self.login_token = ''
        self.password = ''

        # 初始 Token
        self.init_token = []

        # 载入用户自定义配置
        self.load_config()

        # 模块实例
        self.redis_connection = None
        self.mysql_connection = None
        self.response_buffer = None
        self.account_manager = None
        self.downloader = None
        self.processor = None
        self.schedule = None
        self.dataPersistent = None
        self.email_service = None

    # 启动Spider
    def start_spider_core(self):
        if log.isEnabledFor(logging.INFO):
            log.info('Spider 开始启动')

        try:
            # 创建Redis连接
            redis_connect_retry_times = 3
            while redis_connect_retry_times > 0:
                self.redis_connection = redis.StrictRedis(host=self.redis_host,
                                                          port=self.redis_port,
                                                          db=self.redis_db,
                                                          password=self.redis_password)
                ping = self.redis_connection.ping()
                if ping is True:
                    if log.isEnabledFor(logging.INFO):
                        log.info('Redis 服务器连接成功')
                    break
                else:
                    if log.isEnabledFor(logging.INFO):
                        log.info('Redis 服务器连接失败')
                    redis_connect_retry_times -= 1
                    time.sleep(5)

            # 若连接不成功则退出
            if redis_connect_retry_times <= 0:
                raise Exception()

            # 创建MySQL连接
            self.mysql_connection = pymysql.connect(host=self.mysql_host,
                                                    user=self.mysql_username,
                                                    passwd=self.mysql_password,
                                                    db=self.mysql_database,
                                                    charset=self.mysql_charset)

        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error('Redis 启动失败')
                log.exception(e)
            return

        # 创建 response 缓存队列
        self.response_buffer = ResponseBuffer()

        # 启动账户管理器并登陆
        self.account_manager = AccountManager(self.login_token,
                                              self.password,
                                              self.is_login_by_cookie,
                                              self.z_c0)
        self.account_manager.login()

        # 启动Downloader
        self.downloader = Downloader(self.redis_connection,
                                     self.response_buffer,
                                     self.account_manager,
                                     self.is_proxy_service_enable,
                                     self.session_pool_size,
                                     self.download_thread_num,
                                     self.network_retry_times,
                                     self.connect_timeout,
                                     self.download_interval)
        self.downloader.start_downloader()

        # 启动Scheduler
        self.schedule = Scheduler(self.redis_connection, self.url_rate)
        self.schedule.start()

        # 启动 DataPersistent
        self.dataPersistent = DataPersistent(self.persistent_cache_size,
                                             self.follow_relation_persistent_cache_size,
                                             self.mysql_connection,
                                             self.redis_connection)
        self.dataPersistent.start_data_persistent()

        # 启动Processor
        self.processor = Processor(self.process_thread_num,
                                   self.is_parser_following_list,
                                   self.is_parser_follower_list,
                                   self.is_parser_follow_relation,
                                   self.redis_connection,
                                   self.response_buffer)
        self.processor.start_processor()
        self.processor.load_init_data(self.init_token)

        # 启动邮件服务
        if self.is_email_service_enable is True:
            self.email_service = EmailService(self.smtp_server_host,
                                              self.smtp_server_port,
                                              self.smtp_server_password,
                                              self.smtp_from_addr,
                                              self.smtp_to_addr,
                                              self.smtp_email_header,
                                              self.smtp_send_interval,
                                              self.dataPersistent)
            self.email_service.start_email_service()
            self.email_service.send_message('Spider 启动完毕')

        if log.isEnabledFor(logging.INFO):
            log.info('Spider 启动完毕')

        # 模块异常检查
        while True:
            # Downloader模块异常检查
            self.downloader.check_and_restart()
            # EmailService 模块异常检查
            if self.is_email_service_enable is True:
                self.email_service.check_and_restart()
            # DataPersistent 模块异常检查
            self.dataPersistent.check_and_restart()
            # Scheduler 模块异常检查
            # Processor 模块异常检查
            self.processor.check_and_restart()
            # 检查间隔
            time.sleep(180)
            gc.collect()

    # 加载自定义配置信息
    def load_config(self):
        section = "spider_core"
        config = configparser.ConfigParser()
        config.read("Core/Config/SpiderCoreConfig.conf", encoding="utf8")

        # 读取 downloader 模块配置
        self.is_proxy_service_enable = True if int(config.get(section, 'isProxyServiceEnable')) == 1 else False
        self.session_pool_size = int(config.get(section, 'sessionPoolSize'))
        self.download_thread_num = int(config.get(section, 'downloadThreadNum'))
        self.network_retry_times = int(config.get(section, 'networkRetryTimes'))
        self.connect_timeout = int(config.get(section, 'connectTimeout'))
        self.download_interval = int(config.get(section, 'downloadInterval'))

        # 读取 Processor 模块配置
        self.process_thread_num = int(config.get(section, 'processThreadNum'))
        self.is_parser_following_list = True if int(config.get(section, 'isParserFollowingList')) == 1 else False
        self.is_parser_follower_list = True if int(config.get(section, 'isParserFollowerList')) == 1 else False
        self.is_parser_follow_relation = True if int(config.get(section, 'isParserFollowRelation')) == 1 else False

        # 读取 Scheduler 模块配置
        self.url_rate = int(config.get(section, 'urlRate'))

        # 读取 DataPersistent 模块配置
        self.persistent_cache_size = int(config.get(section, 'persistentCacheSize'))
        self.follow_relation_persistent_cache_size = int(config.get(section, 'followRelationPersistentCacheSize'))

        # 读取邮件服务配置
        self.is_email_service_enable = True if int(config.get(section, 'isEmailServiceEnable')) == 1 else False
        self.smtp_server_host = config.get(section, 'smtpServerHost')
        self.smtp_server_port = int(config.get(section, 'smtpServerPort'))
        self.smtp_server_password = config.get(section, 'smtpServerPassword')
        self.smtp_from_addr = config.get(section, 'smtpFromAddr')
        self.smtp_to_addr = config.get(section, 'smtpToAddr')
        self.smtp_email_header = config.get(section, 'smtpEmailHeader')
        self.smtp_send_interval = int(config.get(section, 'smtpSendInterval'))

        # 读取 Redis 数据库配置
        self.redis_host = config.get(section, 'redisHost')
        self.redis_port = int(config.get(section, 'redisPort'))
        self.redis_db = int(config.get(section, 'redisDB'))
        self.redis_password = config.get(section, 'redisPassword')

        # 读取 MySQL 数据库配置
        self.mysql_host = config.get(section, 'mysqlHost')
        self.mysql_username = config.get(section, 'mysqlUsername')
        self.mysql_password = config.get(section, 'mysqlPassword')
        self.mysql_database = config.get(section, 'mysqlDatabase')
        self.mysql_charset = config.get(section, 'mysqlCharset')

        # 读取知乎账户配置
        self.is_login_by_cookie = True if int(config.get(section, 'isLoginByCookie')) == 1 else False
        self.z_c0 = config.get(section, 'z_c0')
        self.login_token = config.get(section, 'loginToken')
        self.password = config.get(section, 'password')

        # 读取初始token
        token_list = config.get(section, 'initToken')
        for token in token_list.split(','):
            self.init_token.append(str(token).strip())

        if log.isEnabledFor(logging.INFO):
            log.info('配置文件读取并配置完毕')
