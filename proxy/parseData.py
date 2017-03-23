from bs4 import BeautifulSoup


class DataParseModule:
    def __init__(self):
        pass

    # 解析 DOM 内容
    @staticmethod
    def parse_data(data):
        from Proxy import proxyCore
        # 存放解析出来代理信息
        proxy_ip_list = []

        # 判断数据是否为空
        if data is None:
            return proxy_ip_list

        # 解析获得包含代理 IP 的表格
        html = BeautifulSoup(data, "html.parser")
        html_ip_list = html.find('table', {'id': 'ip_list'})
        if html_ip_list is None:
            return proxy_ip_list
        data_list = html_ip_list.findAll('tr')

        # 逐个解析表格中的项
        for elem in data_list:
            if elem.find('th', text="国家") is not None:
                continue

            # 解析代理 IP 信息
            country_node = elem.find('td')
            ip_node = country_node.find_next_sibling()
            port_node = ip_node.find_next_sibling()
            protocol_node = port_node.find_next_sibling().find_next_sibling().find_next_sibling()
            ip = ip_node.string
            port = port_node.string
            protocol = protocol_node.string

            # 封装代理信息
            proxy_ip_info = {proxyCore.PROXY_IP: ip,
                             proxyCore.PROXY_PORT: port,
                             proxyCore.PROXY_PROTOCOL: protocol
                             }

            proxy_ip_list.append(proxy_ip_info)
        return proxy_ip_list
