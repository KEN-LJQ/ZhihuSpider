# Python 知乎用户信息爬虫



## 特点

* 无需登陆知乎账号
* 使用多线程爬取，并可以自行配置使用的线程数目
* 使用高匿代理IP进行数据的爬取，每一个线程独立一个代理IP，并且失效后会重新分配，避免频繁访问导致本机 IP 被封



## 运行要求

* Python 版本：3.0 以上
* 数据库：MySQL




## 使用到的库

项目中使用到的一些 Python 自带以及其他的第三方库如下：

###### Python自带：

- time
- threading
- re
- queue
- html
- json

###### 第三方库：

- requests——一个非常好用的请求库，http://docs.python-requests.org/en/master/
- pymysql——python 与 MySQL 连接，https://github.com/PyMySQL/PyMySQL
- BeautifulSoup——简单但是强大的网页文档解析库，https://www.crummy.com/software/BeautifulSoup/bs4/doc/



## 写在前面

### 用户Token



![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-7.PNG)



![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-8.PNG)

​	用户Token是注册知乎账号是设置的一个非中文昵称，通过其可唯一确定某一个用户。同时由于URL中也是通过该Token区分不同用户的页面，所以我们可以很容易的利用token来爬取



### URL分析

爬虫中用到3类URL，分别是：

* 用户主页：

  ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-4.PNG)

* 用户正在关注页：

  ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-5.PNG)

* 用户关注者页：

  ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-6.PNG)




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



## 如何运行

1. 安装指定版本的 Python、数据库、以及必须的第三方库

2. 执行`db.sql`文件，创建使用到的数据库以及表

3. 配置程序中的数据库配置

   1. 打开`spiderConfiguration.conf` 文件，修改用户名以及密码

      ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-1.PNG)

   2. 保存文件

4. 添加若干个初始的用户 token，程序运行后将会以这个用户开始搜索

   * 方法一：修改`spiderConfiguration.conf`文件中里面的的`startToken` 变量的值为初始的用户token（仅可以一个）

     ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-2.PNG)

   * 方法二：比较推荐，把这若干个初始用户 token 添加到数据库中`user_list_cache`表中，并保存

     ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A87.png)

5. 配置用户信息抓取以及用户列表抓取使用的线程数

   * 修改`spiderConfiguration.conf`文件中的`userInfoScrapeThreadNum`以及`userListScrapeThreadNum`字段并保存，默认为8个线程

     ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-3-10/zhihuSpider-3.PNG)

6. 若使用的Window平台,打开CMD，打开项目所在的文件夹的根目录

   ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A84.png)

7. 输入`startup.py`运行程序

   ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A85.png)

   需要注意的是，CMD的字符集需要设置为utf8，否则可能会出现问题

8. 程序开始运行

   * 运行截图：

     ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A86.png)

   * 运行截图：

     ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E5%A6%82%E4%BD%95%E4%BD%BF%E7%94%A88.png)

   * 运行结果

     ![](https://raw.githubusercontent.com/KEN-LJQ/MarkdownPics/master/Resource/2017-2-15/%E7%9F%A5%E4%B9%8E%E7%88%AC%E8%99%AB-%E7%88%AC%E5%8F%96%E5%86%85%E5%AE%B9%E4%BB%8B%E7%BB%8D2.png)




## 可配置的内容

爬虫的相关参数以及使用的代理的参数均可在配置文件`spiderConfiguration.conf`中设置.具体如下：

```

[spider_core]
# 默认关注与被关注列表每页的大小（知乎目前是20条一页）
pageSize = 20
# 爬虫动作时间间隔（单位：秒）
scrapeTimeInterval = 2
# 正在关注页面时最大爬取页面范围(若为负数则代表不作限制)
followingPageMax = 200
# 关注着页面最大爬取页面范围(若为负数则代表不作限制)
followerPageMax = 100
# 是否分析正在关注列表(1代表是，0代表否)
analyseFollowingList = 1
# 是否分析关注者列表(1代表是，0代表否)
analyse_FollowerList = 1
# 用户信息抓取线程数量
userInfoScrapeThreadNum = 8
# 用户列表抓取线程数量
userListScrapeThreadNum = 8
# 是否使用代理(1代表是，0代表否)
isProxyEnable = 1

# 每个代理最大请求次数
proxyUsageMax = 10000
# 发生网络异常重试次数
networkReconnectTimes = 3
# 发生响应异常重试次数
responseErrorRetryTimes = 5
# 网络连接超时（单位：秒）
connectTimeout = 30

# 已分析用户信息的用户 token 缓存列表大小
maxAnalysedCacheQueueSize = 1000
# 已分析用户信息的缓存列表保留大小
remainAnalysedCacheQueueSize = 10
# 未分析用户信息的用户 token 缓存列表大小
maxCacheQueueSize = 1000
# 未分析用户信息的用户 token 缓存列表保留大小
remainCacheQueueSize = 10

# 数据库配置
dbHost = localhost
dbUsername = root
dbPassword = LJQ20110627
dbDatabase = zhihu_spider_test
dbCharset = utf8

# 爬虫起始token
startToken =
```

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

