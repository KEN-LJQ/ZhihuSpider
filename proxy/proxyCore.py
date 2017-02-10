from proxy import dbConnector
from proxy import validateData
from proxy import fetchData
from proxy import parseData
import time

# 希望查找的代理IP总数
proxy_expect = 2
# 当前存在的代理IP总数
proxy_total = 0

# 代理网页检索起始页
start_page = 1
# 代理网页检索最大截至页
end_page = 2
# 当前检索页面
current_page = start_page


# 启动代理IP爬虫
def start_proxy_scraper():
    global current_page
    global proxy_total

    if current_page > end_page:
        current_page = start_page

    # 检查当前数据库中的代理IP的有效性
    db_proxy_list = dbConnector.select_all()
    # print("正在检验已经保存的代理IP的有效性...\n")
    for proxy_info in db_proxy_list:
        is_available = validateData.validate_proxy_ip(proxy_info)
        if is_available is not True:
            dbConnector.delete_proxy_info(proxy_info['id'])
            proxy_total -= 1
            # print("无效代理[" + proxy_info['ip'] + ':' + proxy_info['port'] + ']')

    # 开始检索新的代理IP
    current_proxy_list = []
    while proxy_total < proxy_expect:
        # 当前待验证列表中无代理IP时，再次检索
        if len(current_proxy_list) <= 0:
            # print("开始检索代理IP，当前检索页面：" + str(current_page) + "\n")
            current_proxy_list = parseData.parse_data(fetchData.scrape_data(current_page))
            current_page += 1

        # print(len(current_proxy_list))
        # 对当前列表中的代理进行验证
        time.sleep(1)
        if len(current_proxy_list) > 0:
            current_proxy_info = current_proxy_list.pop()
            print("正在验证代理：" + current_proxy_info['ip'] + ":" + current_proxy_info['port'] )
            # 检查是否存在
            # print(current_proxy_info)
            is_exist = dbConnector.select_ip_port(current_proxy_info)
            # is_exist = None
            if is_exist is None:
                is_available = validateData.validate_proxy_ip(current_proxy_info)
                if is_available is True:
                    dbConnector.insert_proxy_info(current_proxy_info)
                    proxy_total += 1
                    # print('验证成功，代理IP有效，并保存到数据库\n')
                    # else:
                    #     print('验证失败，代理IP无效\n')
                    # else:
                    #     print("验证失败，代理IP已经存在\n")


# 初始化爬虫
def proxy_init():
    global proxy_total
    # 初始化数据库连接
    dbConnector.connection_init()
    proxy_total = dbConnector.get_proxy_num()
    start_proxy_scraper()


# 关闭爬虫
def proxy_close():
    # 关闭数据库连接
    dbConnector.connection_destroy()


# 返回一条代理信息
def get_proxy():
    global proxy_total
    while True:
        # 检查是否需要重新搜索
        if proxy_total <= 0:
            start_proxy_scraper()

        # 获取一条代理信息
        proxy_info = dbConnector.select_one()
        is_available = validateData.validate_proxy_ip(proxy_info)
        if is_available is False:
            dbConnector.delete_proxy_info(proxy_info['id'])
            proxy_total -= 1
        else:
            return proxy_info

# if __name__ == '__main__':
#     proxy_init()
#     print(get_proxy())
#     proxy_close()
