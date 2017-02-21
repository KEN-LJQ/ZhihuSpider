import requests
import time

# 请求网页的 UEL
requestUrl = "http://www.xicidaili.com/nn/"

# 请求首部信息
requestHeader = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Encoding": "gzip, deflate, sdch",
                 "Accept-Language": "zh-CN,zh;q=0.8",
                 "Host": "www.xicidaili.com",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}

# 连接重试次数
NETWORK_RETRY_TIME = 3
# 连接重试间隔(单位：秒)
NETWORK_RETRY_INTERVAL = 30

# 当前连接
session = requests.session()


# 获取代理信息
def fetch_proxy_data(page):
    # 设置连接信息
    session.headers = requestHeader

    # 构造请求 URL
    url = requestUrl + str(page)

    # 获取数据
    retry_time = 0
    while retry_time < NETWORK_RETRY_TIME:
        try:
            response = session.get(url)
            return response.text
        except Exception:
            # 网络异常
            print("[代理模块]网络异常，代理信息获取失败")
            retry_time += 1
    time.sleep(NETWORK_RETRY_INTERVAL)

    # 超过重试次数返回 None
    return None
