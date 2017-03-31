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

authTestURL = 'https://www.zhihu.com/api/v4/members/xzer/followers?offset=0&limit=20'


# 用户账号登陆模块
class AccountManager:
    __slots__ = ('login_token', 'password', 'auth_token', 'is_login_by_cookie', 'z_c0')

    def __init__(self, login_token, password, is_login_by_cookie, z_c0):
        # 登陆方式
        self.is_login_by_cookie = is_login_by_cookie

        # 普通登陆信息
        self.login_token = login_token
        self.password = password

        # Cookie 登陆信息
        self.z_c0 = z_c0

        # 登陆凭证（Cookies）
        self.auth_token = None

    # 返回登陆凭证
    def get_auth_token(self):
        return self.auth_token

    def login(self):
        if self.is_login_by_cookie is True:
            if log.isEnabledFor(logging.INFO):
                log.info('使用Cookie登陆方式登陆')
            return self.cookie_login()
        else:
            if log.isEnabledFor(logging.INFO):
                log.info('使用邮箱或手机号码登陆方式登陆')
            return self.common_login()

    # Cookie 登陆方式
    def cookie_login(self):
        # 创建会话
        session = requests.session()
        session.headers = requestHeader

        # 获取基本的cookie
        session.get(mainPageURL)

        # 添加用户配置的认证Cookie
        cookie = {'z_c0': self.z_c0}
        requests.utils.add_dict_to_cookiejar(session.cookies, cookie)

        # 检验是否成功登陆
        response = session.get(authTestURL)
        if response.status_code == 200:
            # 保存已经被认证Cookie
            self.auth_token = session.cookies.get_dict()
            if log.isEnabledFor(logging.INFO):
                log.info('知乎账户登陆成功')
            return True
        else:
            if log.isEnabledFor(logging.INFO):
                log.info('知乎账户登陆失败')
            return False

    # 普通登陆方式
    def common_login(self):
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
                # 检查是否已经登陆成功
                response = session.get(authTestURL)
                if response.status_code == 200:
                    # 保存登陆认证cookie
                    self.auth_token = session.cookies.get_dict()
                    if log.isEnabledFor(logging.INFO):
                        log.info('知乎账户登陆成功')
                    return True

            # 登陆失败
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
