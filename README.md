

# Python 知乎用户信息爬虫



## 特点

* 使用多线程爬取，并可以自行配置使用的线程数目
* 使用Redis作为任务队列
* 使用高匿代理IP进行数据的爬取，每一个线程独立一个代理IP，并且失效后会重新分配，避免频繁访问导致本机 IP 被封
* 可以启用邮件定时通知功能



## 运行要求

* Python 版本：3.0 以上
* 数据库：MySQL、Redis




## 使用到的库

项目中使用到的 Python 第三方库如下：

###### 第三方库：

- requests——一个非常好用的请求库，http://docs.python-requests.org/en/master/
- pymysql——python 与 MySQL 连接，https://github.com/PyMySQL/PyMySQL
- BeautifulSoup——简单但是强大的网页文档解析库，https://www.crummy.com/software/BeautifulSoup/bs4/doc/
- Redis-py——Redis Python客户端，[How To Configure a Redis Cluster on CentOS 7](https://www.digitalocean.com/community/tutorials/how-to-configure-a-redis-cluster-on-centos-7)



## 写在前面

### 用户Token



![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-7.PNG)



![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-8.PNG)

​	用户Token是注册知乎账号时设置的一个非中文昵称，通过其可唯一确定某一个用户。同时由于URL中也是通过该Token区分不同用户的页面，所以我们可以很容易的利用token来爬取



### URL分析

爬虫中用到3类URL，分别是：

* 用户与获取用户详细信息：

  ```
  https://www.zhihu.com/people/excited-vczh/pins
  ```
  认为用户详细信息仅仅在加载用户信息页时已经在后端进行渲染一同加载显示，数据放在`id`为`data`的`<div>`标签中的`data-state`属性，目前没有找到可以直接提取数据的接口，所以只能够选择一个数据量较少的页面整个爬取

* 用户正在关注列表信息：

  ```
  http://www.zhihu.com/api/v4/members/xzer/followees?limit=20&offset=0
  ```

  该URL需要用户登陆后才用权限获取数据，返回的数据格式为JSON，URL的参数：`limit`列表分页大小，`offset`列表分页偏移值

* 用户关注者列表信息：

  ```
  http://www.zhihu.com/api/v4/members/xzer/followers?limit=20&offset=0
  ```


  该URL需要用户登陆后才用权限获取数据，返回的数据格式为JSON，URL的参数：`limit`列表分页大小，`offset`列表分页偏移值



## 爬取的用户信息内容

本爬虫的目标是爬取知乎中用户公开的个人信息，例如：

![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E7%88%AC%E5%8F%96%E5%86%85%E5%AE%B9%E4%BB%8B%E7%BB%8D1.png)

由于其中包含的信息较多，这个知乎爬虫只是选择了其中一些比较有意义的信息进行爬取。具体的信息包括：

|       字段       |        含义         |
| :------------: | :---------------: |
|   avator_url   |      用户头像URL      |
|     token      |      用户标识字段       |
|    headline    |     用户的一句话介绍      |
|    location    |        居住地        |
|    business    |       所在行业        |
|  employments   |       工作经历        |
|   educations   |       教育经历        |
|  description   |       用户描述        |
| sinaweibo_url  | 新浪微博网址(知乎貌似已不再提供) |
|     gender     |        性别         |
| followingCount |   该用户正在关注的用户数目    |
| followerCount  |    关注该用户的用户数目     |
|  answerCount   |    该用户回答的问题的数目    |
| questionCount  |    该用户提问的问题数目     |
|  voteupCount   |     该用户获得赞的数目     |
|    userName    |       用户昵称        |



## 结构设计



![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-22/spider-7.PNG)

## 如何运行

1. 安装指定版本的 Python、数据库、以及必须的第三方库

2. 执行`db.sql`文件，创建使用到的数据库以及表

3. 配置程序中的数据库配置

   1. 打开`SpiderCoreConfig.conf` 文件，修改MySQL的配置

      ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-22/spider-1.PNG)

   2. 在同一个文件下，修改Redis的配置、

      ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-22/spider-2.PNG)

4. 添加若干个初始的用户 token，程序运行后将会以这个用户开始搜索

   1. 修改`SpiderCoreConfig.conf`文件中里面的的`startToken` 变量的值为初始的用户token（可以设置多个）

      ```
      # 初始token（如果有多个初始token， 使用‘,’分隔）
      initToken = excited-vczh
      ```

5. 配置数据下载以及数据处理的线程数目

   1. 数据下载线程数目，修改`SpiderCoreConfig.conf`文件中的`downloadThreadNum`，默认为10个线程

   ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-22/spider-4.PNG)

   2. 数据处理线程数目，修改`SpiderCoreConfig.conf`文件中的`processThreadNum`，默认为3个线程

   ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-22/spider-5.PNG)

6. 配置是否使用代理

   1. 使用代理可避免爬虫频繁访问导致IP被屏蔽。修改`SpiderCoreConfig.conf`文件中的`isProxyServiceEnable`，值为`1`代表启动， `0`代表关闭

      ```
      # 是否启用代理服务(1代表是，0代表否)
      isProxyServiceEnable = 1
      ```

7. 知乎账户配置

   1. 配置登陆方式。设定配置文件的`isLoginByCookie`字段， 若值为`1`则使用Cookie方式登陆，若为`1`则使用普通方式（邮箱或手机号码）登陆

      ```
      # 是否使用Cookie登陆
      isLoginByCookie = 1
      ```

   2. 配置登陆认证信息。以下两种登陆方式

      1. Cookie登陆方式。首先使用PC浏览器手动登陆知乎账号，然后从浏览器中将登陆成功后的Cookie配置到爬虫配置文件中。配置的cookie包括：`q_c1`, `r_cap_id`,`cap_id`, `z_c0`。

      ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-29/spider-1.PNG)

      2. 普通方式。（当前不可用）配置知乎账户的账号和密码，最好不要使用自己的主账号（目前知乎的邮箱登陆和手机号码登陆方式均需要输入普通验证码或选择倒转文字验证码， 还没有解决）

      ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-22/spider-3.PNG)

8. 日志配置

   1. 可选择将程序运行信息输出到控制台，或者写入到日志文件中，选择哪一种方式在`Logger.py` 文件中配置。而日志级别等具体的设置在`SpiderLoggingConfig.conf`中配置

      ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-22/spider-6.PNG)

9. 若使用的Window平台,打开CMD，打开项目所在的文件夹的根目录

   ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A84.png)

10. 输入`startup.py`运行程序

 ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A85.png)

 需要注意的是，CMD的字符集需要设置为utf8，否则可能会出现问题

11. 程序开始运行

    * 运行结果

      ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E7%88%AC%E5%8F%96%E5%86%85%E5%AE%B9%E4%BB%8B%E7%BB%8D2.png)




## 可配置的内容

爬虫的相关参数在配置文件`SpiderCore.conf`中设置.具体如下：

```
[spider_core]

# 数据下载配置
# 是否启用代理服务(1代表是，0代表否)
isProxyServiceEnable = 1
# session pool 的大小
sessionPoolSize = 25
# 下载线程数量
downloadThreadNum = 10
# 网络连接错误重试次数
networkRetryTimes = 3
# 网络连接超时（单位：秒）
connectTimeout = 30
# 下载间隔
downloadInterval = 5

# 数据处理配置
# 数据处理线程数量
processThreadNum = 3
# 是否解析following列表（通过用户的正在关注列表获取下一批需要分析的token）
isParserFollowingList = 1
# 是否解析follower列表（通过用户的关注者列表获取下一批需要分析的token）
isParserFollowerList = 0

# URL调度配置
# 用户信息下载和用户关注列表下载URL比例（用户信息URL / URL总数， 例如：值为8，代表每次调度中80%是用户信息URL）
urlRate = 8

# 数据持久化配置
# 数据库写缓存大小（记录条数）
persistentCacheSize = 100

# 邮件服务配置
# 是否启用邮件通知(1代表是，0代表否)
isEmailServiceEnable = 1
# SMTP邮件服务器域名
smtpServerHost = smtp.mxhichina.com
# SMTP邮件服务器端口
smtpServerPort = 25
# SMTP邮件服务器登陆密码
smtpServerPassword = XXX
# 邮件发送人地址
smtpFromAddr = centosserver@ken-ljq.xyz
# 邮件接收人地址
smtpToAddr = ljq1120799726@outlook.com
# 邮件标题
smtpEmailHeader = ZhiZhuSpiderNotification
# 邮件发送间隔(单位：秒)
smtpSendInterval = 14400

# Redis 数据库配置
redisHost = localhost
redisPort = 6379
redisDB = 1
redisPassword = XXX

# MySQL 数据库配置
mysqlHost = localhost
mysqlUsername = root
mysqlPassword = XXX
mysqlDatabase = spider_test
mysqlCharset = utf8

# 知乎账号配置
loginToken = handsome@ken-ljq.xyz
password = XXX

# 初始token（如果有多个初始token， 使用‘,’分隔）
initToken = excited-vczh
```

代理模块参数在配置文件`proxyConfiguration.conf`中设置.具体如下：

```

[proxy_core]
# 代理验证连接超时时长（单位：秒）
proxyValidate_connectTimeout = 30
# 代理验证重新连接次数
proxyValidate_networkReconnectTimes = 3
# 代理数据抓取连接超时时长（单位：秒）
dataFetch_connectTimeout = 30
# 代理数据抓取重新连接时间间隔（单位：秒）
dataFetch_networkReconnectInterval = 30
# 代理数据抓取重新连接次数
dataFetch_networkReconnectionTimes = 3
# 代理网页数据抓取起始页码
proxyCore_fetchStartPage = 1
# 代理网页数据抓取结束页码
proxyCore_fetchEndPage = 5
# 代理池大小(不大于100)
proxyCore_proxyPoolSize = 10
# 代理池更新扫描间隔
proxyCore_proxyPoolScanInterval = 300
# 代理验证线程数量
proxyCore_proxyValidateThreadNum = 5

```



## 简单的分析数据

![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-9.PNG)

![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-10.PNG)



## 其他待续

