import requests

# 请求网页的 UEL
requestUrl = "http://www.xicidaili.com/nn/"

# 请求首部信息
requestHeader = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                 "Accept-Encoding": "gzip, deflate, sdch",
                 "Accept-Language": "zh-CN,zh;q=0.8",
                 "Host": "www.xicidaili.com",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"}

# 当前连接的一些信息
session = requests.session()
cookies = None


# 构造 URL
def url_builder(page):
    return requestUrl + str(page)


# 连接到指定的 URL 并获得返回的内容
def access_to_web(url):
    global cookies
    # setting request info
    session.headers = requestHeader
    if cookies is not None:
        session.cookies = cookies

    # fetch data
    try:
        response = session.get(url)
    except Exception:
        # handler exception
        print("fail to connect to [" + url + "]")
        return None
    else:
        # update cookies
        cookies = response.cookies
        return response.text


# 获取代理 IP 信息
def scrape_data(page):
    return access_to_web(url_builder(page))

# if __name__ == '__main__':
#     result = scrape_data(1)
#     print(result)
#     print(len(result))
