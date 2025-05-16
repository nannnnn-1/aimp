class Config:
    # 数据库配置
    DB_HOST = 'localhost'
    DB_USER = 'root'  # 替换为你的MySQL用户名
    DB_PASSWORD = '123456'  # 替换为你的MySQL密码
    DB_NAME = 'ai_map_check'
    
    # JWT配置
    JWT_SECRET_KEY = '7188a91172add7a59e73b918e28c025ed498565b4abd7853346b7a01f0aef52c'  # 在生产环境中应该使用更安全的密钥 