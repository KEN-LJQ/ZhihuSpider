import requests
import re

# 代理信息字段
PROXY_IP = 'ip'
PROXY_PORT = 'port'
PROXY_ADDRESS = 'address'
PROXY_PROTOCAL = 'protocal'
PROXY_ALIVE_TIME = 'aliveTime'
PROXY_VALIDATE_TIME = 'validateTime'

# 代理 IP 验证网站
url = 'http://icanhazip.com/'

# 连接超时设置（单位：秒）
timeout = 30
# 连接重试次数
network_retry_time = 3

# 请求头信息
header = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Encoding': 'gzip, deflate, sdch',
          'Accept-Language': 'zh-CN,zh;q=0.8',
          'Cache-Control': 'max-age=0',
          'Host': 'icanhazip.com',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/56.0.2924.87 Safari/537.36'}


# 验证给定的代理 IP 是否有效
def validate_proxy_ip(proxy_ip_info):
    if proxy_ip_info is None:
        return False

    # 构造代理信息
    proxy_ip = proxy_ip_info[PROXY_IP]
    proxy_port = proxy_ip_info[PROXY_PORT]
    proxy_protocal = proxy_ip_info[PROXY_PROTOCAL].lower()
    proxy = {proxy_protocal: proxy_ip + ':' + proxy_port}

    # 使用代理进行连接
    session = requests.session()
    session.headers = header
    session.proxies = proxy
    retry_time = 0
    while retry_time < network_retry_time:
        try:
            response = session.get(url, timeout=timeout)

            # 解析返回的当前使用的IP并判断是否有效
            match_list = re.findall(r'[0-9]+(?:\.[0-9]+){3}', response.text)
            if len(match_list) > 0:
                current_ip = match_list.pop()
                if current_ip is not None and current_ip == proxy_ip:
                    return True
            else:
                retry_time += 1
        except Exception:
            retry_time += 1

    return False
