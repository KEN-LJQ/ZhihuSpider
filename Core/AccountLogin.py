import requests
import logging
from bs4 import BeautifulSoup
from Core.Logger import log

requestHeader = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Encoding": "gzip, deflate, sdch, br",
                 "Accept-Language": "zh-CN,zh;q=0.8",
                 "Cache-Control": "max-age=0",
                 "Host": "www.zhihu.com",
                 "Upgrade-Insecure-Requests": "1",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
                               " Chrome/56.0.2924.87 Safari/537.36"}

loginURL = 'https://www.zhihu.com/login/email'

mainPageURL = 'https://www.zhihu.com'


# 用户账号登陆模块
class AccountManager:
    __slots__ = ('login_token', 'password', 'auth_token')

    def __init__(self, login_token, password):
        self.login_token = login_token
        self.password = password

        # 登陆凭证（Cookies）
        self.auth_token = None

    # 返回登陆凭证
    def get_auth_token(self):
        return self.auth_token

    # 登陆
    def login(self):
        # 创建会话
        session = requests.session()
        session.headers = requestHeader

        # 获取 _xsrf
        try:
            response = session.get(mainPageURL)
            input_tag = BeautifulSoup(response.text, 'html.parser').find('input', attrs={'name': '_xsrf'})
            if input_tag is None:
                return False
            _xsrf = input_tag['value']

            # login
            form_data = {'_xsrf': _xsrf,
                         'email': self.login_token,
                         'password': self.password}
            requestHeader.update({'X-Requested-With': 'XMLHttpRequest', 'X-Xsrftoken': _xsrf})
            session.headers = requestHeader
            response = session.post(url=loginURL, data=form_data)
            if response.status_code == 200:
                # 保存登陆认证cookie
                self.auth_token = session.cookies.get_dict()

                if log.isEnabledFor(logging.INFO):
                    log.info('知乎账户登陆成功')
                return True
            else:
                if log.isEnabledFor(logging.INFO):
                    log.info('知乎账户登陆失败')
                return False
        except Exception as e:
            if log.isEnabledFor(logging.ERROR):
                log.error(e)
        finally:
            session.close()

# if __name__ == '__main__':
#     account_manager = AccountManager('xxx', 'xxx')
#     account_manager.login()
#     print(account_manager.get_auth_token())
