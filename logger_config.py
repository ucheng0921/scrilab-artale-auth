# logger_config.py - 統一日誌配置
import logging
import os
import sys
from datetime import datetime

class LoggerConfig:
    """統一日誌配置管理器"""
    
    _initialized = False
    
    @classmethod
    def setup_logging(cls, log_level=None, log_file=None, console_output=True):
        """設置日誌配置"""
        if cls._initialized:
            return
        
        # 確定日誌級別
        if log_level is None:
            log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
        
        # 創建根日誌器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # 清除現有處理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 創建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台輸出
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 文件輸出（如果指定）
        if log_file:
            try:
                # 確保日誌目錄存在
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"警告: 無法創建日誌文件 {log_file}: {e}")
        
        cls._initialized = True
        
        # 記錄初始化信息
        logger = logging.getLogger(__name__)
        logger.info(f"🔧 日誌系統已初始化 - 級別: {log_level}")
        if log_file:
            logger.info(f"📝 日誌文件: {log_file}")
    
    @classmethod
    def get_logger(cls, name):
        """獲取指定名稱的日誌器"""
        if not cls._initialized:
            cls.setup_logging()
        
        return logging.getLogger(name)

# 便捷函數
def get_logger(name=None):
    """獲取日誌器的便捷函數"""
    if name is None:
        # 自動獲取調用者的模塊名稱
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return LoggerConfig.get_logger(name)

# 自動初始化（可選）
def auto_setup():
    """自動設置日誌（根據環境）"""
    env = os.environ.get('FLASK_ENV', 'production').lower()
    
    if env == 'development':
        LoggerConfig.setup_logging(
            log_level='DEBUG',
            console_output=True,
            log_file='logs/debug.log'
        )
    elif env == 'testing':
        LoggerConfig.setup_logging(
            log_level='WARNING',
            console_output=True
        )
    else:  # production
        LoggerConfig.setup_logging(
            log_level='INFO',
            console_output=True,
            log_file='logs/artale_auth.log'
        )

# 如果直接運行此模塊，執行自動設置
if __name__ == '__main__':
    auto_setup()