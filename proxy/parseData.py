from bs4 import BeautifulSoup

PROXY_IP = 'ip'
PROXY_PORT = 'port'
PROXY_ADDRESS = 'address'
PROXY_PROTOCAL = 'protocal'
PROXY_ALIVE_TIME = 'aliveTime'
PROXY_VALIDATE_TIME = 'validateTime'


# 解析 DOM 内容
def parse_data(data):
    # data 要求非空
    if data is None:
        return

    html = BeautifulSoup(data, "html.parser")
    proxy_ip_list = []

    # 解析获得包含代理 IP 的表格
    data_list = html.find('table', {'id': 'ip_list'}).findAll('tr')

    # 逐个解析表格中的项
    for elem in data_list:
        if elem.find('th', text="国家") is not None:
            continue

        # 解析代理 IP 信息
        country_node = elem.find('td')
        ip_node = country_node.find_next_sibling()
        port_node = ip_node.find_next_sibling()
        address_node = port_node.find_next_sibling()
        protocal_node = address_node.find_next_sibling().find_next_sibling()
        # alive_time_node = protocal_node.find_next_sibling().find_next_sibling().find_next_sibling()
        # validate_time_node = alive_time_node.find_next_sibling()
        ip = ip_node.string
        port = port_node.string
        # if address_node.find('a') is not None:
        #     address = address_node.find('a').string
        # else:
        #     address = 'none'
        protocol = protocal_node.string
        # alive_time = alive_time_node.string
        # validate_time = validate_time_node.string

        proxy_ip_info = {PROXY_IP: ip,
                         PROXY_PORT: port,
                         # PROXY_ADDRESS: address,
                         PROXY_PROTOCAL: protocol
                         # PROXY_ALIVE_TIME: alive_time,
                         # PROXY_VALIDATE_TIME: validate_time
                         }

        proxy_ip_list.append(proxy_ip_info)

    return proxy_ip_list


# 测试
testData1 = '<tr><th class="country">国家</th><th>IP地址</th><th>端口</th><th>服务器地址</th><th class="country">是否匿名' \
            '</th><th>类型</th><th class="country">速度</th><th class="country">连接时间</th><th width="8%">存活时间</th>' \
            '<th width="20%">验证时间</th></tr>'

testData2 = '<tr class="odd"><td class="country"><img src="http://fs.xicidaili.com/images/flag/cn.png" alt="Cn" /></td>' \
            '<td>182.92.207.196</td><td>3128</td><td><a href="/2016-11-30/zhejiang">浙江杭州</a></td><td class="country">' \
            '透明</td><td>HTTP</td><td class="country"><div title="5.056秒" class="bar"><div class="bar_inner slow" styl' \
            'e="width:56%"></div></div></td><td class="country"><div title="1.011秒" class="bar"> <div class="bar_inner ' \
            'medium" style="width:81%"> </div></div></td><td>61天</td><td>17-01-31 05:45</td></tr>'
