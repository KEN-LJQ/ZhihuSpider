import logging.config

# 日志配置（若配置为consoleLogger则输出到控制台，若配置为fileLogger则记录到日志文件中）
LOGGING_TYPE = 'fileLogger'

# 配置Logger
configFile = open('core/spiderLogging.conf', encoding='utf8')
logging.config.fileConfig(configFile)
log = logging.getLogger(LOGGING_TYPE)
