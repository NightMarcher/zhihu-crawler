# ZhihuCrawler
徒手实现定时爬取知乎，从中发掘有价值的信息，并可视化爬取的数据作网页展示。项目目前正在开发，欢迎前来交流学习！
## 问题及解决方案
- [x] **日志**      
程序运行时统一初始化。由于logging应用了单例模式，之后可以直接使用配置好的logging
- [x] **第三方库版本管理**      
pipenv，功能强大，方便易用
- [x] **代码版本控制**      
git，使用.gitignore来忽略日志文件夹、vim临时文件、缓存文件文件夹
- [x] **配置管理**      
yaml，可读性好，语法简单
- [x] **文件组织**      
将相同功能的文件放于同一文件夹下，*.py文件组织成包
- [x] **性能分析**      
使用自己定义的装饰器函数来测量函数运行的时间
- [x] **数据爬取**      
使用selenium + webdriver爬取动态网页，使用requests库请求部分已有接口
- [x] **数据解析**      
xpath，速度快，使用简单
- [x] **爬取标记**      
使用Redis存储已爬取的话题id及其下信息的摘要值，数据类型选取为hash
- [x] **数据序列化方式选取**     
json，通用序列化方案
- [x] **摘要算法选取**      
MD5，选择原因见[Hashing Algorithms In Python](http://widerin.net/blog/hashing-algorithms-in-python/)。此外经测试，base16速度仅次于MD5，base64次于base16，base32最慢；整体而言，直接加密'汉字'类型的字符串，比加密'\\u6c49\\u5b57'类型的字符串速度要快，因此json.dumps的时候ensure_ascii参数要设置为False
- [x] **数据持久化**     
MongoDB，时间类型数据统一存储为格林尼治时间
- [ ] **定时任务**
- [ ] **任务管理**   
supervisor
- [x] **并发实现**   
multiprocessing.dummy多线程，易于移植，方法简单
- [ ] **话题树建立**
- [ ] **网页展示**   
flask框架 + bootstrap-flask + pyecharts
