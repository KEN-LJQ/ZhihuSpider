import requests
from proxy import proxyCore
import sys

# 请求头信息
requestHeader = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Encoding": "gzip, deflate, sdch, br",
                 "Accept-Language": "zh-CN,zh;q=0.8",
                 "Cache-Control": "max-age=0",
                 "Host": "www.zhihu.com",
                 "Upgrade-Insecure-Requests": "1",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}

# 当个代理最大请求次数
PROXY_REQUEST_MAX = 20000
# 发生网络错误时重新连接次数
NETWORK_RETRY_TIME = 3
# 网络连接超时（单位：秒）
NETWORK_TIMEOUT = 30

session = None
usage_times = 0


# 配置基本网络设置
def network_init():
    global session
    print('正在配置网络...')
    proxyCore.proxy_init()
    session = requests.session()
    session.headers = requestHeader
    proxy = proxyCore.get_proxy()
    ip = proxy['ip']
    port = proxy['port']
    protocal = proxy['protocal'].lower()
    session.proxies = {protocal: ip + ":" + port}
    print('配置网络成功!!!')


# 关闭
def network_close():
    proxyCore.proxy_close()


# 更换代理
def change_proxy():
    print('正在更换代理...')
    proxy = proxyCore.get_proxy()
    if proxy is None:
        sys.exit(1)
    ip = proxy['ip']
    port = proxy['port']
    protocal = proxy['protocal'].lower()
    session.proxies = {protocal: ip + ":" + port}
    print("更换代理成功!!!")


# 连接到指定的 URL 并返回数据
def fetch_data_from_url(url):
    global usage_times
    retry_time = 0
    while retry_time <= NETWORK_RETRY_TIME:
        # 若代理使用次数过多则更换
        if usage_times >= PROXY_REQUEST_MAX:
            change_proxy()

        # 尝试连接
        try:
            response = session.get(url, timeout=NETWORK_TIMEOUT)
            usage_times += 1
            return response
        except requests.exceptions.RequestException:
            # 重试
            retry_time += 1
            print('网络异常，正在重新连接...')
        except Exception:
            # 重试
            retry_time += 1
            print('网络异常，正在重新连接...')
    return None

# if __name__ == '__main__':
#     network_init()
#     print(fetch_data_from_url('http://icanhazip.com/').text)
#     network_close()
