import mysql.connector
import bcrypt
from config import Config

def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )

def reset_password(username, new_password):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 生成密码哈希
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        # 更新用户密码
        cursor.execute(
            'UPDATE users SET password = %s WHERE username = %s',
            (password_hash, username)
        )
        
        conn.commit()
        print(f"Successfully reset password for user: {username}")

    except Exception as e:
        print(f"Error resetting password: {str(e)}")
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    # 重置管理员密码为 123456
    reset_password('admin', '123456')
    # 重置其他用户密码
    reset_password('zhangsan', '123456')
    reset_password('lisi', '123456')
    reset_password('wangwu', '123456') 