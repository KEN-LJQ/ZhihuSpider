import datetime
import threading
import smtplib
import logging
import time
from email.header import Header
from email.mime.text import MIMEText
from Core.Logger import log


class EmailService:
    __slots__ = ('data_persistent', 'smtp_server_host', 'smtp_server_port', 'smtp_server_password',
                 'smtp_from_addr', 'smtp_to_addr', 'smtp_email_header', 'smtp_send_interval', 'email_service_thread')

    def __init__(self, smtp_server_host, smtp_server_port, smtp_server_password,
                 smtp_from_addr, smtp_to_addr, smtp_email_header, smtp_send_interval, data_persistent):
        self.data_persistent = data_persistent
        # 设置参数
        self.smtp_server_host = smtp_server_host
        self.smtp_server_port = smtp_server_port
        self.smtp_server_password = smtp_server_password
        self.smtp_from_addr = smtp_from_addr
        self.smtp_to_addr = smtp_to_addr
        self.smtp_email_header = smtp_email_header
        self.smtp_send_interval = smtp_send_interval

        # 创建邮件定时发送线程
        self.email_service_thread = EmailServiceThread(self.smtp_server_host,
                                                       self.smtp_server_port,
                                                       self.smtp_server_password,
                                                       self.smtp_from_addr,
                                                       self.smtp_to_addr,
                                                       self.smtp_email_header,
                                                       self.smtp_send_interval,
                                                       self.data_persistent)

        if log.isEnabledFor(logging.INFO):
            log.info('EmailService 模块初始化完毕')

    # 启动邮件定时发送线程
    def start_email_service(self):
        # 启动线程
        self.email_service_thread.start()

        if log.isEnabledFor(logging.INFO):
            log.info('EmailService 模块启动')

    def check_and_restart(self):
        if self.email_service_thread.thread_status == 'error':
            self.email_service_thread = EmailServiceThread(self.smtp_server_host,
                                                           self.smtp_server_port,
                                                           self.smtp_server_password,
                                                           self.smtp_from_addr,
                                                           self.smtp_to_addr,
                                                           self.smtp_email_header,
                                                           self.smtp_send_interval,
                                                           self.data_persistent)
            self.email_service_thread.start()
            if log.isEnabledFor(logging.INFO):
                log.info('EmailService线程重新启动')

    # 发送指定的内容
    def send_message(self, email_content):
        # 准备发送的内容
        now = datetime.datetime.now()
        header = self.smtp_email_header + '[' + str(now.month) + '-' + str(now.day) + ' ' + \
            str(now.hour) + ':' + str(now.minute) + ':' + str(now.second) + ']'
        msg = MIMEText(email_content, 'plain', 'utf-8')
        msg['from'] = self.smtp_from_addr
        msg['to'] = self.smtp_to_addr
        msg['Subject'] = Header(header, 'utf-8').encode()

        # 发送
        try:
            smtp_server = smtplib.SMTP(self.smtp_server_host, self.smtp_server_port)
            smtp_server.login(self.smtp_from_addr, self.smtp_server_password)
            smtp_server.sendmail(self.smtp_from_addr, [self.smtp_to_addr], msg.as_string())
            smtp_server.quit()
        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error("邮件发送失败")
                log.exception(e)


class EmailServiceThread(threading.Thread):
    def __init__(self, smtp_server_host, smtp_server_port, smtp_server_password,
                 smtp_from_addr, smtp_to_addr, smtp_email_header, smtp_send_interval, data_persistent):
        threading.Thread.__init__(self)
        self.data_persistent = data_persistent
        # 设置参数
        self.smtp_server_host = smtp_server_host
        self.smtp_server_port = smtp_server_port
        self.smtp_server_password = smtp_server_password
        self.smtp_from_addr = smtp_from_addr
        self.smtp_to_addr = smtp_to_addr
        self.smtp_email_header = smtp_email_header
        self.smtp_send_interval = smtp_send_interval
        # 线程状态
        self.thread_status = 'working'
        # 持久化队列名称
        self.persistent_cache = 'persistentCache'

        self.lastSendTime = datetime.datetime.now()
        self.lastUserInfoNum = self.data_persistent.get_current_user_info_num()

    def run(self):
        if log.isEnabledFor(logging.DEBUG):
            log.debug("邮件服务线程启动")
        try:
            while True:
                time.sleep(self.smtp_send_interval)

                # 准备发送的内容
                msg = MIMEText(self.get_email_content(), 'plain', 'utf-8')
                msg['from'] = self.smtp_from_addr
                msg['to'] = self.smtp_to_addr
                msg['Subject'] = Header(self.get_email_header(), 'utf-8').encode()

                # 发送
                smtp_server = smtplib.SMTP(self.smtp_server_host, self.smtp_server_port)
                smtp_server.login(self.smtp_from_addr, self.smtp_server_password)
                smtp_server.sendmail(self.smtp_from_addr, [self.smtp_to_addr], msg.as_string())
                smtp_server.quit()

                # 更新最后一次发送时间
                self.lastSendTime = datetime.datetime.now()

        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error("邮件发送失败")
                log.exception(e)
            self.thread_status = 'error'

    # 构造邮件标题
    def get_email_header(self):
        now = datetime.datetime.now()
        return self.smtp_email_header + '[' + str(now.month) + '-' + str(now.day) + ' ' \
            + str(now.hour) + ':' + str(now.minute) + ':' + str(now.second) + ']'

    # 构建邮件内容
    def get_email_content(self):
        # 获得当前用户的数量
        current_num = self.data_persistent.get_current_user_info_num()
        total_add = current_num - self.lastUserInfoNum
        self.lastUserInfoNum = current_num

        # 构建邮件内容
        info_line = '自' + '[' + str(self.lastSendTime.month) + '-' + str(self.lastSendTime.day) + ' ' \
                    + str(self.lastSendTime.hour) + ':' + str(self.lastSendTime.minute) \
                    + ':' + str(self.lastSendTime.second) + ']' + "以来,\n" + "爬取到新的用户数量为：" + str(total_add) \
                    + '\n当前爬取到的用户信息总条数为：' + str(current_num) + '\n\n\n\n'

        # 获取日志信息
        logging_file = open('Logs/ZhiHuSpider.log', encoding='utf8')
        logging_info_line = '日志文件信息：\n' + logging_file.read()
        logging_file.close()

        return info_line + logging_info_line
