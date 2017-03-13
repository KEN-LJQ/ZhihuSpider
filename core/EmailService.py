import threading
import time
import logging
from email.header import Header
from email.mime.text import MIMEText
import smtplib
import datetime
from core.Logger import log

SMTP_SERVER_HOST = ''
SMTP_SERVER_PORT = 25
SMTP_SERVER_PASSWORD = ''
SMTP_FROM_ADDR = ''
SMTP_TO_ADDR = ''
SMTP_EMAIL_HEADER = ''
SMTP_SEND_INTERVAL = 3600


class EmailService:
    def __init__(self, db_connection):
        self.db_connection = db_connection
        # 创建邮件定时发送线程
        self.email_service_thread = EmailServiceThread(self.db_connection)

    # 启动邮件定时发送线程
    def start_email_notification_service(self):
        # 启动线程
        self.email_service_thread.start()

    # 获取线程状态
    def get_email_notification_service_status(self):
        return self.email_service_thread.status

    # 重启邮件服务线程
    def restart_email_notification_service(self):
        self.email_service_thread = EmailServiceThread(self.db_connection)
        self.email_service_thread.start()

    # 发送指定的内容
    @staticmethod
    def send_message(email_content):
        # 准备发送的内容
        now = datetime.datetime.now()
        header = SMTP_EMAIL_HEADER + '[' + str(now.month) + '-' + str(now.day) + ' ' + \
                 str(now.hour) + ':' + str(now.minute) + ':' + str(now.second) + ']'
        msg = MIMEText(email_content, 'plain', 'utf-8')
        msg['from'] = SMTP_FROM_ADDR
        msg['to'] = SMTP_TO_ADDR
        msg['Subject'] = Header(header, 'utf-8').encode()

        # 发送
        try:
            smtp_server = smtplib.SMTP(SMTP_SERVER_HOST, SMTP_SERVER_PORT)
            smtp_server.login(SMTP_FROM_ADDR, SMTP_SERVER_PASSWORD)
            smtp_server.sendmail(SMTP_FROM_ADDR, [SMTP_TO_ADDR], msg.as_string())
            smtp_server.quit()
        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error("邮件发送失败")
                log.exception(e)
            print(e)


class EmailServiceThread(threading.Thread):
    def __init__(self, db_connection):
        threading.Thread.__init__(self)
        self.db_connection = db_connection
        self.status = 'running'
        self.lastSendTime = datetime.datetime.now()
        self.lastUserInfoNum = db_connection.get_user_info_num()

    def run(self):
        if log.isEnabledFor(logging.DEBUG):
            log.debug("邮件服务线程启动")
        try:
            while True:
                time.sleep(SMTP_SEND_INTERVAL)

                # 准备发送的内容
                msg = MIMEText(self.get_email_content(), 'plain', 'utf-8')
                msg['from'] = SMTP_FROM_ADDR
                msg['to'] = SMTP_TO_ADDR
                msg['Subject'] = Header(self.get_email_header(), 'utf-8').encode()

                # 发送
                smtp_server = smtplib.SMTP(SMTP_SERVER_HOST, SMTP_SERVER_PORT)
                smtp_server.login(SMTP_FROM_ADDR, SMTP_SERVER_PASSWORD)
                smtp_server.sendmail(SMTP_FROM_ADDR, [SMTP_TO_ADDR], msg.as_string())
                smtp_server.quit()

                # 更新最后一次发送时间
                self.lastSendTime = datetime.datetime.now()

        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error("邮件发送失败")
                log.exception(e)
            self.status = 'error'

    @staticmethod
    def get_email_header():
        now = datetime.datetime.now()
        return SMTP_EMAIL_HEADER + '[' + str(now.month) + '-' + str(now.day) + ' ' \
            + str(now.hour) + ':' + str(now.minute) + ':' + str(now.second) + ']'

    def get_email_content(self):
        # 获得当前用户的数量
        current_num = self.db_connection.get_user_info_num()
        total_add = current_num - self.lastUserInfoNum
        self.lastUserInfoNum = current_num

        # 构建邮件内容
        info_line = '自' + '[' + str(self.lastSendTime.month) + '-' + str(self.lastSendTime.day) + ' ' \
                    + str(self.lastSendTime.hour) + ':' + str(self.lastSendTime.minute) \
                    + ':' + str(self.lastSendTime.second) + ']' + "以来,\n" + "爬取到新的用户数量为：" + str(total_add) \
                    + '\n当前爬取到的用户信息总条数为：' + str(current_num) + '\n\n\n\n'

        # 获取日志信息
        logging_file = open('logs/ZhiHuSpider.log', encoding='utf8')
        logging_info_line = '日志文件信息：\n' + logging_file.read()
        logging_file.close()

        return info_line + logging_info_line
