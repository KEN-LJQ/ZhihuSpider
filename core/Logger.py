import logging.config

# 日志类型（若配置为consoleLogger则输出到控制台，若配置为fileLogger则记录到日志文件中）
LOGGER_TYPE = 'fileLogger'
# LOGGER_TYPE = 'consoleLogger'

# 配置全局Logger
configFile = open('Core/Config/SpiderLoggingConfig.conf', encoding='utf8')
logging.config.fileConfig(configFile)
log = logging.getLogger(LOGGER_TYPE)
