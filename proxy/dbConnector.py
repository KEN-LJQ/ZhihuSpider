import pymysql

PROXY_ID = 'id'
PROXY_IP = 'ip'
PROXY_PORT = 'port'
PROXY_ADDRESS = 'address'
PROXY_PROTOCAL = 'protocal'
PROXY_ALIVE_TIME = 'aliveTime'
PROXY_VALIDATE_TIME = 'validateTime'

# 数据库配置
DB_HOST = 'localhost'
DB_USERNAME = 'root'
DB_PASSWORD = 'LJQ20110627'
DB_DATABASE = 'proxy_ip_test'
DB_CHARSET = 'utf8'

# SQL
SELECT_BY_PROXY_IP = 'select id,proxy_ip,proxy_port,proxy_protocal,proxy_address,proxy_alive_time,proxy_validate_time' \
                     ' from ip_list where proxy_ip = %s'
SELECT_ALL = 'select id,proxy_ip,proxy_port,proxy_protocal,proxy_address,proxy_alive_time,proxy_validate_time ' \
             'from ip_list'
SELECT_BY_PROXY_IP_PORT = 'select id,proxy_ip,proxy_port,proxy_protocal,proxy_address,proxy_alive_time,' \
                          'proxy_validate_time from ip_list where proxy_ip = %s and proxy_port = %s'
SELECT_ONE = 'select id,proxy_ip,proxy_port,proxy_protocal,proxy_address,proxy_alive_time,proxy_validate_time ' \
             'from ip_list limit 1'
INSERT_PROXY_IP = 'insert into ip_list(proxy_ip,proxy_port,proxy_protocal,proxy_address,proxy_alive_time,' \
                  'proxy_validate_time) values(%s,%s,%s,%s,%s,%s)'
DELETE_PROXY_IP = 'delete from ip_list where id = %s'
NUMBER_COUNT = 'select count(*) from ip_list '

connection = None


# 数据库连接初始化
def connection_init():
    global connection
    connection = pymysql.connect(host=DB_HOST,
                                 user=DB_USERNAME,
                                 passwd=DB_PASSWORD,
                                 db=DB_DATABASE,
                                 charset=DB_CHARSET)


# 销毁数据库连接
def connection_destroy():
    if connection is not None:
        connection.close()


# 选择指定的 IP
def select_by_ip(ip):
    if connection is None:
        return None

    cur = connection.cursor()
    cur.execute(SELECT_BY_PROXY_IP, ip)
    query_result = cur.fetchone()

    data = {PROXY_ID: query_result[0],
            PROXY_IP: query_result[1],
            PROXY_PORT: query_result[2],
            PROXY_PROTOCAL: query_result[3],
            PROXY_ADDRESS: query_result[4],
            PROXY_ALIVE_TIME: query_result[5],
            PROXY_VALIDATE_TIME: query_result[6]}
    cur.close()
    return data


# 返回一条代理信息
def select_one():
    if connection is None:
        return None
    cur = connection.cursor()
    cur.execute(SELECT_ONE)
    elem = cur.fetchone()
    data = {PROXY_ID: elem[0],
            PROXY_IP: elem[1],
            PROXY_PORT: elem[2],
            PROXY_PROTOCAL: elem[3],
            PROXY_ADDRESS: elem[4],
            PROXY_ALIVE_TIME: elem[5],
            PROXY_VALIDATE_TIME: elem[6]}
    cur.close()
    return data


# 选择所有的代理 IP
def select_all():
    if connection is None:
        return None

    data = []
    cur = connection.cursor()
    cur.execute(SELECT_ALL)
    for elem in cur.fetchall():
        data.append({PROXY_ID: elem[0],
                     PROXY_IP: elem[1],
                     PROXY_PORT: elem[2],
                     PROXY_PROTOCAL: elem[3],
                     PROXY_ADDRESS: elem[4],
                     PROXY_ALIVE_TIME: elem[5],
                     PROXY_VALIDATE_TIME: elem[6]})
    cur.close()
    return data


# 查找指定的代理是否已经存在与数据库
def select_ip_port(proxy_info):
    if proxy_info is None:
        return None

    cur = connection.cursor()
    ip = str(proxy_info[PROXY_IP])
    port = str(proxy_info[PROXY_PORT])
    cur.execute(SELECT_BY_PROXY_IP_PORT, [ip, port])
    query_result = cur.fetchone()
    cur.close()
    return query_result


# 插入代理 IP 信息
def insert_proxy_info(proxy_info):
    if connection is None:
        return None

    cur = connection.cursor()
    ip = str(proxy_info[PROXY_IP])
    port = str(proxy_info[PROXY_PORT])
    protocal = str(proxy_info[PROXY_PROTOCAL])
    address = str(proxy_info[PROXY_ADDRESS])
    alive_time = str(proxy_info[PROXY_ALIVE_TIME])
    validate_time = str(proxy_info[PROXY_VALIDATE_TIME])
    cur.execute(INSERT_PROXY_IP,
                [ip, port, protocal, address, alive_time, validate_time])
    connection.commit()
    cur.close()


# 返回当前数据库中代理的数目
def get_proxy_num():
    if connection is None:
        return None

    cur = connection.cursor()
    cur.execute(NUMBER_COUNT)
    data = cur.fetchone()
    cur.close()
    return data[0]


# 删除代理 IP 信息
def delete_proxy_info(proxy_id):
    if connection is None:
        return None

    cur = connection.cursor()
    cur.execute(DELETE_PROXY_IP, proxy_id)
    connection.commit()
    cur.close()
