import re
from flask import Flask, abort, request, jsonify, send_from_directory, send_file, make_response
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import mysql.connector
from datetime import timedelta, datetime
import bcrypt
from config import Config
import os
from werkzeug.utils import secure_filename
import random
import json
import time
from PIL import Image
import numpy as np
import threading
import shutil
from upload_map import process_map_tiles
from extract_pdf_layers import extract_layers
from map_prediction_simulation import predict_map_layers_simulation
import uuid
app = Flask(__name__)
CORS(app)
# JWT配置
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
# ... (靠近 JWT_SECRET_KEY, MAPS_FOLDER 等配置)

# --- 模型管理配置 ---
UPLOAD_FOLDER = '/local_server/ai_mapcheck/uploads' # 或者你希望的上传根目录
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SAMPLE_UPLOAD_TEMP_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_samples')
app.config['FINE_TUNED_MODELS_DIR'] = os.path.join(app.config['UPLOAD_FOLDER'], 'fine_tuned_models')

# 确保目录存在
os.makedirs(app.config['SAMPLE_UPLOAD_TEMP_DIR'], exist_ok=True)
os.makedirs(app.config['FINE_TUNED_MODELS_DIR'], exist_ok=True)

# ... (其他配置和 Flask app 初始化)
# 添加静态文件配置
AVATAR_FOLDER = '/local_server/ai_mapcheck/users/avatars'
TASK_FOLDER = '/local_server/ai_mapcheck/tasks'
ERROR_EXAMPLE_FOLDER = '/local_server/ai_mapcheck/error_examples'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf', 'dwg'}
USER_RULE_IMAGE_FOLDER = '/local_server/ai_mapcheck/user_error_examples' # Define path for user rule images
app.config['USER_RULE_IMAGE_FOLDER'] = USER_RULE_IMAGE_FOLDER
os.makedirs(app.config['USER_RULE_IMAGE_FOLDER'], exist_ok=True) # Ensure directory exists

jwt = JWTManager(app)

# JWT错误处理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'message': 'token已过期',
        'error': 'token_expired'
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'message': 'token无效',
        'error': 'invalid_token'
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'message': '缺少token',
        'error': 'authorization_required'
    }), 401

# 数据库连接
def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )

# 根据上传的地图，判断使用哪套已做好的数据

# 获取用户头像
@app.route('/api/avatars/<path:filename>')
def serve_avatar(filename):
    try:
        print(f"Attempting to serve avatar: {filename}")
        print(f"Full path: {os.path.join(AVATAR_FOLDER, filename)}")
        if os.path.exists(os.path.join(AVATAR_FOLDER, filename)):
            print("File exists!")
            return send_from_directory(AVATAR_FOLDER, filename)
        else:
            print("File does not exist!")
            return jsonify({'message': '头像文件不存在'}), 404
    except Exception as e:
        print(f"Error serving avatar: {str(e)}")
        return jsonify({'message': '头像文件不存在'}), 404

# 获取任务原始地图
@app.route('/api/tasks/files/task_<int:task_id>/original/<path:filename>')
def get_original_file(task_id, filename):
    try:
        # 验证文件是否存在
        file_path = os.path.join(TASK_FOLDER, f'task_{task_id}', 'original')
        full_path = os.path.join(file_path, filename)
        
        if not os.path.exists(full_path):
            return jsonify({'message': '文件不存在'}), 404
            
        return send_from_directory(file_path, filename)
    except Exception as e:
        print(f"Error serving task file: {str(e)}")
        return jsonify({'message': '文件不存在'}), 404
    
# 获取任务地图瓦片（只获取zoom_4的全景图）


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 查询用户
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'message': '用户名不存在'}), 401
        
        try:
            # 验证密码
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                # 创建JWT token，使用username作为身份标识
                token = create_access_token(identity=user['username'])
                
                # 清理敏感信息
                user.pop('password', None)
                
                return jsonify({
                    'token': token,
                    'user': user
                })
            else:
                return jsonify({'message': '用户名或密码错误'}), 401
                
        except Exception as e:
            print(f"Password verification error: {str(e)}")
            return jsonify({'message': '密码验证错误'}), 500

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'message': '服务器错误'}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 检查用户名是否已存在
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({'message': '用户名已存在'}), 400
            
        # 对密码进行加密
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 插入新用户
        cursor.execute('''
            INSERT INTO users (username, password, real_name, role, created_at) 
            VALUES (%s, %s, %s, %s, NOW())
        ''', (username, hashed_password.decode('utf-8'), username, 'user'))
        
        conn.commit()
        
        return jsonify({'message': '注册成功'}), 201
        
    except Exception as e:
        print(f"Registration error: {str(e)}")
        return jsonify({'message': '注册失败'}), 500
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
# 获取该用户的任务列表
@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    current_username = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 修改SQL查询，使用username而不是creator_id
        cursor.execute('''
            SELECT t.*, ts.progress as current_progress
            FROM tasks t
            LEFT JOIN task_stages ts ON t.id = ts.task_id AND t.current_stage = ts.stage_number
            WHERE t.creator_username = %s
            ORDER BY t.created_at DESC
        ''', (current_username,))
        
        tasks = cursor.fetchall()
        
        # 格式化日期时间
        for task in tasks:
            task['created_at'] = task['created_at'].isoformat()
            task['updated_at'] = task['updated_at'].isoformat()
            task['hasReport'] = False  # 默认为False，后续可以根据实际文件检查来设置
            task['createTime'] = task.pop('created_at')
        
        return jsonify({'tasks': tasks})

    except Exception as e:
        print(f"Get tasks error: {str(e)}")
        return jsonify({'message': '获取任务列表失败'}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 创建信息任务
@app.route('/api/tasks', methods=['POST'])
@jwt_required()
def create_task():
    current_username = get_jwt_identity()
    data = request.get_json()
    task_name = data.get('name')

    if not task_name:
        return jsonify({'message': '任务名称不能为空'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 修改SQL插入语句，使用creator_username而不是creator_id
        cursor.execute('''
            INSERT INTO tasks (name, creator_username, status, current_stage, storage_path) 
            VALUES (%s, %s, 'pending', 1, %s)
        ''', (
            task_name, 
            current_username,
            f'/local_server/ai_mapcheck/tasks/task_{cursor.lastrowid}'
        ))
        
        task_id = cursor.lastrowid
        
        # 创建任务的7个阶段
        stages = [
            (1, '地图上传'),
            (2, '参数设置'),
            (3, '地图解析'),
            (4, '地图审查'),
            # (5, '结果预览'),
            (5, '报告导出'),
            (6, '问题反馈')
        ]
        
        for stage_number, stage_name in stages:
            cursor.execute('''
                INSERT INTO task_stages (task_id, stage_number, stage_name, status, progress)
                VALUES (%s, %s, %s, 'pending', 0)
            ''', (task_id, stage_number, stage_name))
        
        conn.commit()
        
        # 获取创建的任务信息
        cursor.execute('''
            SELECT t.*, ts.progress as current_progress
            FROM tasks t
            LEFT JOIN task_stages ts ON t.id = ts.task_id AND t.current_stage = ts.stage_number
            WHERE t.id = %s
        ''', (task_id,))
        
        task = cursor.fetchone()
        
        # 格式化日期时间
        task['created_at'] = task['created_at'].isoformat()
        task['updated_at'] = task['updated_at'].isoformat()
        task['hasReport'] = False
        task['createTime'] = task.pop('created_at')
        
        return jsonify({'task': task})

    except Exception as e:
        print(f"Create task error: {str(e)}")
        return jsonify({'message': '创建任务失败'}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 获取任务信息
@app.route('/api/tasks/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    current_username = get_jwt_identity()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取任务信息
        cursor.execute('''
            SELECT t.*, ts.progress as current_progress, ts.status as current_status
            FROM tasks t
            LEFT JOIN task_stages ts ON t.id = ts.task_id AND t.current_stage = ts.stage_number
            WHERE t.id = %s AND t.creator_username = %s
        ''', (task_id, current_username))
        
        task = cursor.fetchone()
        
        if not task:
            return jsonify({'message': '任务不存在或无权访问'}), 404
            
        # 获取任务阶段信息
        cursor.execute('''
            SELECT stage_number, stage_name, status, progress
            FROM task_stages
            WHERE task_id = %s
            ORDER BY stage_number
        ''', (task_id,))
        
        stages = cursor.fetchall()
        
        # 格式化日期时间
        task['created_at'] = task['created_at'].isoformat()
        task['updated_at'] = task['updated_at'].isoformat()
        task['createTime'] = task.pop('created_at')
        
        # 检查是否存在上传的文件
        original_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'original')
        if os.path.exists(original_dir):
            files = os.listdir(original_dir)
            if files:  # 如果目录中有文件
                task['original_file'] = files[0]  # 获取第一个文件
                task['file_url'] = f'/api/tasks/files/task_{task_id}/original/{files[0]}'
        
        return jsonify({
            'task': task,
            'stages': stages
        })
        
    except Exception as e:
        print(f"Get task error: {str(e)}")
        return jsonify({'message': '获取任务信息失败'}), 500
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


# 获取任务的阶段信息
@app.route('/api/tasks/<int:task_id>/stage/<int:stage_number>', methods=['GET'])
def get_task_stage(task_id, stage_number):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 获取任务阶段信息
        cursor.execute('''
            SELECT status, progress
            FROM task_stages
            WHERE task_id = %s AND stage_number = %s
        ''', (task_id, stage_number))
        
        stage = cursor.fetchone()
        
        return jsonify({'stage': stage})
    
    except Exception as e:
        print(f"Get task stage error: {str(e)}")
        return jsonify({'message': '获取任务阶段失败'}), 500


# 添加文件上传配置
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 上传任务原始地图
@app.route('/api/tasks/<int:task_id>/upload', methods=['POST'])
@jwt_required()
def upload_file(task_id):
    try:
        # 验证用户权限
        current_user = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT creator_username FROM tasks WHERE id = %s",
            (task_id,)
        )
        task = cursor.fetchone()
        
        if not task or task['creator_username'] != current_user:
            cursor.close()
            conn.close()
            return jsonify({'message': '无权访问该任务'}), 403

        if 'file' not in request.files:
            cursor.close()
            conn.close()
            return jsonify({'message': '未找到文件'}), 400
            
        file = request.files['file']
        if file.filename == '':
            cursor.close()
            conn.close()
            return jsonify({'message': '未选择文件'}), 400
            
        if not allowed_file(file.filename):
            cursor.close()
            conn.close()
            return jsonify({'message': '不支持的文件类型'}), 400

        # 创建任务目录
        task_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'original')
        os.makedirs(task_dir, exist_ok=True)

        # 清理原有文件（如果存在）
        for existing_file in os.listdir(task_dir):
            os.remove(os.path.join(task_dir, existing_file))

        # 保存文件
        filename = "原地图.pdf"
        file_path = os.path.join(task_dir, filename)
        file.save(file_path)

        # 更新数据库
        cursor.execute(
            """
            UPDATE tasks 
            SET status = 'in_progress', 
                current_stage = 2,
                updated_at = NOW()
            WHERE id = %s
            """,
            (task_id,)
        )

        # 更新阶段状态
        cursor.execute(
            """
            UPDATE task_stages 
            SET status = 'completed', 
                progress = 100,
                updated_at = NOW()
            WHERE task_id = %s AND stage_number = 1
            """,
            (task_id,)
        )

        conn.commit()
        # 地图分块处理
        # process_map_tiles(task_id,file_path)
        import fitz
        try:
            doc_orig = fitz.open(file_path)
        except Exception as e:
            print(f"Error opening original PDF '{file_path}': {e}")
            return
        page_number = 0
        if page_number >= len(doc_orig):
            print(f"Error: Page number {page_number} out of range for '{file_path}'.")
            doc_orig.close()
            return

        page_orig = doc_orig[page_number]
        page_rect = page_orig.rect # Get original page dimensions
        output_png_original_filename = "original_map.png"
        output_png_original_path = os.path.join(TASK_FOLDER, f'task_{task_id}', 'original', output_png_original_filename)
        try:
            dpi_orig = 600 # Choose desired resolution for original map PNG
            pix_orig = page_orig.get_pixmap(dpi=dpi_orig)
            pix_orig.save(output_png_original_path)
            print(f"Saved original map PNG ({pix_orig.width}x{pix_orig.height} px) to: {output_png_original_path}")
        except Exception as e_orig_png:
            print(f"Error saving original map PNG: {e_orig_png}")
        # 返回更新后的文件信息
        return jsonify({
            'message': '文件上传成功',
            'filename': filename,
            'file_url': f'/api/tasks/files/task_{task_id}/original/{filename}'
        }), 200

    except Exception as e:
        print('文件上传错误:', str(e))
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        return jsonify({'message': '文件上传失败'}), 500


@app.route('/api/tasks/<int:task_id>/original/original_map.png')
def get_original_map_png(task_id, filename='original_map.png'):
    try:
        # 验证文件是否存在
        file_path = os.path.join(TASK_FOLDER, f'task_{task_id}', 'original')
        full_path = os.path.join(file_path, filename)
        
        if not os.path.exists(full_path):
            return jsonify({'message': '文件不存在'}), 404
            
        return send_from_directory(file_path, filename)
    except Exception as e:
        print(f"Error serving task file: {str(e)}")
        return jsonify({'message': '文件不存在'}), 404
# 保存用户参数设置
# @app.route('/api/tasks/<int:task_id>/settings', methods=['POST'])
# @jwt_required()
# def save_settings(task_id):
#     try:
#         current_user = get_jwt_identity()
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
        
#         # 验证任务所有权
#         cursor.execute(
#             "SELECT creator_username FROM tasks WHERE id = %s",
#             (task_id,)
#         )
#         task = cursor.fetchone()
        
#         if not task or task['creator_username'] != current_user:
#             return jsonify({'message': '无权访问该任务'}), 403

#         # 获取设置参数
#         settings = request.get_json()
        
#         # 创建设置目录
#         settings_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'settings')
#         os.makedirs(settings_dir, exist_ok=True)
        
#         # 保存设置到文件
#         settings_file = os.path.join(settings_dir, 'settings.json')
#         with open(settings_file, 'w', encoding='utf-8') as f:
#             json.dump(settings, f, ensure_ascii=False, indent=2)
            
#         # 随机生成设置类型（1或2）
#         settings_type = random.randint(1, 2)
        
#         # 更新数据库
#         cursor.execute(
#             """
#             UPDATE tasks 
#             SET status = 'in_progress', 
#                 current_stage = 3,
#                 updated_at = NOW()
#             WHERE id = %s
#             """,
#             (task_id,)
#         )
        
#         # 更新阶段状态
#         cursor.execute(
#             """
#             UPDATE task_stages 
#             SET status = 'completed', 
#                 progress = 100,
#                 updated_at = NOW()
#             WHERE task_id = %s AND stage_number = 2
#             """,
#             (task_id,)
#         )
        
        
#         conn.commit()
        
#         return jsonify({
#             'success': True,
#             'message': '参数设置成功',
#             'settings_type': settings_type
#         })
        
#     except Exception as e:
#         print('保存设置失败:', str(e))
#         return jsonify({'message': '保存设置失败'}), 500
        
#     finally:
#         if 'cursor' in locals():
#             cursor.close()
#         if 'conn' in locals():
#             conn.close()

# 获取用户参数设置
# @app.route('/api/tasks/<int:task_id>/settings', methods=['GET'])
# @jwt_required()
# def get_settings(task_id):
#     try:
#         current_user = get_jwt_identity()
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
        
#         # 验证任务所有权
#         cursor.execute(
#             """
#             SELECT creator_username
#             FROM tasks 
#             WHERE id = %s
#             """,
#             (task_id,)
#         )
#         task = cursor.fetchone()
        
#         if not task or task['creator_username'] != current_user:
#             return jsonify({'message': '无权访问该任务'}), 403
            
#         # 获取设置文件内容
#         settings_file = os.path.join(TASK_FOLDER, f'task_{task_id}', 'settings', 'settings.json')
#         settings = {}
#         if os.path.exists(settings_file):
#             with open(settings_file, 'r', encoding='utf-8') as f:
#                 settings = json.load(f)
                
#         return jsonify({
#             'settings': settings,
#             'settings_type': 1
#         })
        
#     except Exception as e:
#         print('获取设置失败:', str(e))
#         return jsonify({'message': '获取设置失败'}), 500
        
#     finally:
#         if 'cursor' in locals():
#             cursor.close()
#         if 'conn' in locals():
#             conn.close()

# 添加解析任务状态存储
# analysis_tasks = {}
# 开始解析任务
@app.route('/api/tasks/<int:task_id>/analyze/start', methods=['POST'])
def start_analyze(task_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 更新任务信息
        cursor.execute(
                """
                UPDATE task_stages 
                SET status = 'in_progress', progress = 0 
                WHERE task_id = %s AND stage_number = 3
                """,
                (task_id,)
            )
        conn.commit()
        # 创建analysis文件夹（如果不存在）
        analysis_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'analysis')
        os.makedirs(analysis_dir, exist_ok=True)
        
        
        # 模拟解析过程（实际项目中这里应该启动真实的解析任务）
        def generate_results(task_id):
            # time.sleep(2)  # 模拟初始处理时间
            extract_layers(task_id)

            
            # 更新任务状态为完成
            cursor.execute(
                """
                UPDATE task_stages 
                SET status = 'completed', progress = 100 
                WHERE task_id = %s AND stage_number = 3
                """,
                (task_id,)
            )
            
            # 确保第三阶段的更新被提交
            conn.commit()
            
            # 等待一小段时间，确保前端能看到完成状态
            time.sleep(1)
            
            
            # 更新任务信息
            cursor.execute(
                """
                UPDATE tasks 
                SET current_stage = 4, updated_at = NOW()
                WHERE id = %s
                """,
                (task_id,)
            )
            
            conn.commit()
            
        
        # 在后台线程中运行生成过程
        thread = threading.Thread(target=generate_results, args=(task_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'message': '解析任务已启动'})
        
    except Exception as e:
        print('Error:', str(e))
        return jsonify({'success': False, 'message': str(e)}), 500

# 获取解析结果文件
@app.route('/api/tasks/<int:task_id>/analysis/image/<path:filename>')
def get_analysis_file(task_id, filename):
    try:
        file_path = os.path.join(TASK_FOLDER, f'task_{task_id}', 'analysis', filename)
        return send_file(file_path)
    except FileNotFoundError:
        return '', 404


#------------------------------------#
#       审查部分的api                 #
#       创建人：朱楠                  #
#       创建时间：4-7                 #
#       修改时间：4-15                #
#       修改人：朱楠                  #
#       修改内容：地图审查函数修改     #
#------------------------------------#
# 开始审查任务
@app.route('/api/tasks/<int:task_id>/review/start', methods=['POST'])
# @jwt_required()
def start_review(task_id):
    try:
        # 更新任务状态为进行中
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "UPDATE task_stages SET status = 'in_progress', progress = 0 WHERE task_id = %s AND stage_number = 4",
            (task_id,)
        )
        conn.commit()
        
        # 创建review文件夹（如果不存在）
        review_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'review')
        os.makedirs(review_dir, exist_ok=True)


        # 启动审查进程（这里使用模拟数据）
        def generate_random_review_results():
            cursor.execute("SELECT selected_model_id, review_mode FROM tasks WHERE id = %s", (task_id,))
            model_id, review_mode = cursor.fetchone()
            predict_map_layers_simulation(task_id, model_id,review_mode)
            
            
            # 更新任务状态为完成
            cursor.execute(
                "UPDATE task_stages SET status = 'completed', progress = 100 WHERE task_id = %s AND stage_number = 4",
                (task_id,)
            )
            # 确保第四阶段的更新被提交
            conn.commit()
            # 更新任务信息
            cursor.execute(
                "UPDATE tasks SET current_stage = 5, updated_at = NOW() WHERE id = %s",
                (task_id,)
            )
            conn.commit()
            
        # 在后台线程中运行生成过程
        thread = threading.Thread(target=generate_random_review_results)
        thread.daemon = True
        thread.start()

        return jsonify({'success': True, 'message': '审查任务已启动'})

    except Exception as e:
        print('启动审查失败:', str(e))
        return jsonify({'error': '启动审查失败'}), 500

# 获取审查结果文件
@app.route('/api/tasks/<int:task_id>/review/errors', methods=['GET'])
def get_review_errors(task_id):
    """
    Scans the error tiles directory for a task and returns
    a list of coordinates for found error tiles.
    """
    try:
        error_tile_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'review', 'predicted_error_tiles_zoom4')
        
        if not os.path.exists(error_tile_dir) or not os.path.isdir(error_tile_dir):
            # If the directory doesn't exist, assume no errors yet or process failed
            app.logger.warning(f"Error tile directory not found for task {task_id}: {error_tile_dir}")
            return jsonify([]) # Return empty list if dir not found

        error_list = []
        # Regex to match the error tile filename format and capture row and col
        # It expects one or more digits for row and col
        error_tile_pattern = re.compile(r'^error_tile_row(\d+)_col(\d+)\.jpg$', re.IGNORECASE)

        for filename in os.listdir(error_tile_dir):
            match = error_tile_pattern.match(filename)
            if match:
                try:
                    row = int(match.group(1))
                    col = int(match.group(2))
                    # error_list.append({"row": row, "col": col})
                    if(row == 0 and col == 4):
                        error_list.append({"row": row, "col": col,"cls_name":"道路转角处断开","error_category":"拓扑关系","severity":"中"})
                    elif(row == 0 and col == 6):
                        error_list.append({"row": row, "col": col,"cls_name":"注记重叠","error_category":"表达与符号化","severity":"中"})
                    elif(row == 11 and col == 7):
                        error_list.append({"row": row, "col": col,"cls_name":"道路交叉口断开","error_category":"拓扑关系","severity":"高"})
                    elif(row == 1 and col == 1):
                        error_list.append({"row": row, "col": col,"cls_name":"注记缺失","error_category":"完整性","severity":"中"})
                    elif(row == 2 and col == 8):
                        error_list.append({"row": row, "col": col,"cls_name":"道路转角处断开","error_category":"拓扑关系","severity":"中"})
                    elif(row == 3 and col == 4):
                        error_list.append({"row": row, "col": col,"cls_name":"建筑名称缺失","error_category":"完整性","severity":"中"})
                    elif(row == 3 and col == 9):
                        error_list.append({"row": row, "col": col,"cls_name":"建筑名称缺失","error_category":"完整性","severity":"中"})
                    elif(row == 4 and col == 3):
                        error_list.append({"row": row, "col": col,"cls_name":"注记缺失","error_category":"完整性","severity":"中"})
                    elif(row == 6 and col == 13):
                        error_list.append({"row": row, "col": col,"cls_name":"道路转角处断开","error_category":"拓扑关系","severity":"中"})
                    elif(row == 7 and col == 10):
                        error_list.append({"row": row, "col": col,"cls_name":"建筑压盖道路","error_category":"逻辑一致性 / 表达与符号化","severity":"中"})
                    elif(row == 8 and col == 14):
                        error_list.append({"row": row, "col": col,"cls_name":"道路断裂","error_category":"几何精度/完整性","severity":"中"})
                    elif(row == 9 and col == 13):
                        error_list.append({"row": row, "col": col,"cls_name":"道路断裂","error_category":"几何精度/完整性","severity":"中"})
                    elif(row == 9 and col == 5):
                        error_list.append({"row": row, "col": col,"cls_name":"建筑名称缺失","error_category":"完整性","severity":"中"})
                except ValueError:
                    app.logger.warning(f"Could not parse row/col from filename: {filename} in task {task_id}")
                    continue # Skip files with non-integer row/col

        app.logger.info(f"Found {len(error_list)} error tiles for task {task_id}")
        return jsonify(error_list)

    except Exception as e:
        app.logger.error(f"Error getting review errors for task {task_id}: {e}", exc_info=True)
        return jsonify({"message": "Internal server error retrieving error list"}), 500

@app.route('/api/tasks/<int:task_id>/review/error_tiles/error_tile_row<int:row>_col<int:col>.jpg', methods=['GET'])
def get_review_error_tile(task_id, row, col):
    """
    Serves a specific error tile image file.
    Uses send_from_directory for security.
    """
    try:
        error_tile_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'review', 'predicted_error_tiles_zoom4')
        filename = f"error_tile_row{row}_col{col}.jpg"
        
        # Log the request for debugging
        app.logger.debug(f"Requesting error tile: task={task_id}, row={row}, col={col}, filename={filename}")
        app.logger.debug(f"Serving from directory: {error_tile_dir}")

        # Use send_from_directory for safe file serving
        # It handles checking if the file exists and prevents path traversal
        return send_from_directory(error_tile_dir, filename, mimetype='image/jpeg')

    except FileNotFoundError:
         # send_from_directory raises Werkzeug NotFound which Flask handles as 404
         app.logger.warning(f"Error tile not found: Task {task_id}, Row {row}, Col {col}")
         abort(404, description="Error tile image not found.")
    except Exception as e:
        app.logger.error(f"Error serving error tile for task {task_id}, row {row}, col {col}: {e}", exc_info=True)
        abort(500, description="Internal server error serving error tile.")

# 获取原地图瓦片
@app.route('/api/tasks/<int:task_id>/review/tiles/original_map_tiles/<path:filename>')
def get_review_tiles(task_id, filename):
    try:
        file_path = os.path.join(TASK_FOLDER, f'task_{task_id}', 'review', 'tiles_original_zoom4', filename)
        return send_file(file_path)
    except FileNotFoundError:
        return '', 404
    
# 获取原地图上的错误图片
@app.route('/api/tasks/<int:task_id>/review/original_error_image/<path:filename>')
def get_original_error_image(task_id, filename):
    try:
        file_path = os.path.join(TASK_FOLDER, f'task_{task_id}', 'review',filename)
        return send_file(file_path)
    except FileNotFoundError:
        return '', 404


#------------------------------------#
#       报告部分的api                 #
#       创建人：朱楠                  #
#       创建时间：4-15                #
#       修改时间：4-15                #
#       修改人：朱楠                  #
#       修改内容：报告生成函数修改     #
#------------------------------------#
# 生成报告
@app.route('/api/tasks/<int:task_id>/report/generate', methods=['POST'])
def generate_report(task_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # 检查任务是否存在
        cursor.execute('''SELECT * FROM tasks WHERE id = %s''', (task_id,))
        task = cursor.fetchone()
        
        if not task:
            return jsonify({'error': '任务不存在'}), 404
            
        # TODO: 使用 reportlab 或其他 PDF 生成库生成报告
        # 更新任务状态
        cursor.execute('''
            UPDATE task_stages 
            SET status = 'completed', progress = 100 
            WHERE task_id = %s AND stage_number = 5
        ''', (task_id,))
        
        db.commit()
        return jsonify({'message': '报告生成成功'})
        
    except Exception as e:
        print('生成报告失败:', str(e))
        return jsonify({'error': '生成报告失败'}), 500

# 获取报告
@app.route('/api/tasks/<int:task_id>/report', methods=['GET'])
def get_report(task_id):
    try:
        # 检查报告是否存在
        report_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'review')
        if not os.path.exists(report_dir):
            return jsonify({'report_url': None})
            
        # 获取最新的报告文件
        pdf_report_files = [f for f in os.listdir(report_dir) if f.endswith('.pdf')]
        if not pdf_report_files:
            return jsonify({'report_url': None})
            
        markdown_report_files = [f for f in os.listdir(report_dir) if f.endswith('.md')]
        if not markdown_report_files:
            return jsonify({'report_url': None})
        
        latest_pdf_report = sorted(pdf_report_files)[-1]
        latest_markdown_report = sorted(markdown_report_files)[-1]
        pdf_report_url = f'/api/tasks/files/task_{task_id}/report/{latest_pdf_report}'
        md_report_url = f'/api/tasks/files/task_{task_id}/report/{latest_markdown_report}'
        
        return jsonify({'pdf_report_url': pdf_report_url, 'md_report_url': md_report_url})
        
    except Exception as e:
        print('获取报告状态失败:', str(e))
        return jsonify({'error': '获取报告状态失败'}), 500


# 添加新的路由来提供报告文件    
@app.route('/api/tasks/files/task_<int:task_id>/report/<path:filename>')
def serve_report_file(task_id, filename):
    try:
        # 验证文件是否存在
        file_path = os.path.join(TASK_FOLDER, f'task_{task_id}', 'review')
        full_path = os.path.join(file_path, filename)
        
        if not os.path.exists(full_path):
            return jsonify({'message': '文件不存在'}), 404
            
        return send_from_directory(file_path, filename)
    except Exception as e:
        print(f"Error serving report file: {str(e)}")
        return jsonify({'message': '文件不存在'}), 404
    


# # 处理问题反馈文件上传
# @app.route('/api/tasks/<int:task_id>/feedback/upload', methods=['POST'])
# def upload_feedback(task_id):
#     try:
#         # 检查任务是否存在
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
#         task = cursor.fetchone()
#         conn.commit()
#         if not task:
#             return jsonify({'message': '任务不存在'}), 404
            
#         # 检查是否有文件上传
#         if 'file' not in request.files:
#             return jsonify({'message': '没有上传文件'}), 400
            
#         file = request.files['file']
#         if file.filename == '':
#             return jsonify({'message': '没有选择文件'}), 400
            
#         # 检查文件类型
#         allowed_extensions = {'txt', 'doc', 'docx'}
#         if not file.filename.lower().endswith(tuple('.' + ext for ext in allowed_extensions)):
#             return jsonify({'message': '不支持的文件类型'}), 400
            
#         # 创建反馈文件目录
#         feedback_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'feedback')
#         os.makedirs(feedback_dir, exist_ok=True)
        
#         # 生成带时间戳的文件名
#         timestamp = int(time.time())
#         file_ext = os.path.splitext(file.filename)[1]
#         feedback_filename = f'feedback_{task_id}_{timestamp}{file_ext}'
        
#         # 保存文件
#         file_path = os.path.join(feedback_dir, feedback_filename)
#         file.save(file_path)
        
#         return jsonify({'message': '反馈文件上传成功'})
        
#     except Exception as e:
#         print('上传反馈文件失败:', str(e))
#         return jsonify({'message': '上传反馈文件失败'}), 500

# # 完成问题反馈阶段
# @app.route('/api/tasks/<int:task_id>/feedback/complete', methods=['POST'])
# def complete_feedback(task_id):
#     try:
#         data = request.get_json()
#         has_feedback = data.get('has_feedback', False)
        
#         # 更新任务阶段状态
#         conn = get_db_connection()
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute('''
#             UPDATE task_stages 
#             SET status = 'completed', progress = 100 
#             WHERE task_id = %s AND stage_number = 6
#         ''', (task_id,))
        
#         # 更新任务状态
#         cursor.execute('''
#             UPDATE tasks 
#             SET status = 'completed',current_stage = 6, has_feedback = %s 
#             WHERE id = %s
#         ''', (has_feedback, task_id))
        
#         conn.commit()
        
#         return jsonify({'message': '反馈阶段完成'})
        
#     except Exception as e:
#         print('完成反馈阶段失败:', str(e))
#         return jsonify({'message': '完成反馈阶段失败'}), 500


# --- 后台微调任务 (使用原生 MySQL) ---
def run_fine_tuning_task_mysql(model_id, user_id, sample_file_path, base_model_id, output_model_dir, db_config):
    """
    后台执行微调任务的函数 (MySQL 版本)。
    接收数据库配置字典作为参数。
    """
    print(f"[FineTune Task {model_id}] Started for user {user_id}")
    conn = None
    cursor = None

    try:
        # 在新线程中创建独立的数据库连接
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database']
        )
        cursor = conn.cursor(dictionary=True) # 使用字典游标

        # 0. 检查模型是否存在 (虽然理论上刚创建，但以防万一)
        cursor.execute("SELECT id FROM models WHERE id = %s", (model_id,))
        model_exists = cursor.fetchone()
        if not model_exists:
            print(f"[FineTune Task {model_id}] Error: Model not found in database.")
            return # 结束任务

        # 1. 更新状态为 'fine-tuning'
        print(f"[FineTune Task {model_id}] Setting status to fine-tuning...")
        cursor.execute("UPDATE models SET status = %s WHERE id = %s", ('fine-tuning', model_id))
        conn.commit()
        print(f"[FineTune Task {model_id}] Status set to fine-tuning.")

        # 2. **TODO: 实现真实的微调逻辑**
        #    - 解压 sample_file_path 中的数据
        #    - 加载 base_model_id 对应的基础模型
        #    - 使用样本数据进行微调
        #    - 保存微调后的模型到 output_model_dir
        #    - 计算评估指标 (metrics)
        print(f"[FineTune Task {model_id}] Simulating fine-tuning process...")
        time.sleep(5) # 模拟耗时操作

        # --- 模拟结果 ---
        simulated_success = True # random.choice([True, False]) # 可以随机模拟成功或失败
        simulated_metrics = {"accuracy": round(random.uniform(0.7, 0.95), 2), "loss": round(random.uniform(0.05, 0.3), 2)} if simulated_success else None
        final_model_filename = f"model_{model_id}_weights.h5" # 假设模型文件名
        final_model_path = os.path.join(output_model_dir, final_model_filename)
        # 模拟保存模型文件
        try:
            with open(final_model_path, 'w') as f:
                f.write(f"Simulated fine-tuned model data for model {model_id}")
            print(f"[FineTune Task {model_id}] Simulated model saved to {final_model_path}")
        except IOError as e:
            print(f"[FineTune Task {model_id}] Error saving simulated model file: {e}")
            simulated_success = False # 如果文件无法保存，则视为失败
        # --- 结束模拟 ---
        print(f"[FineTune Task {model_id}] Simulation complete. Success: {simulated_success}")

        # 3. 根据结果更新数据库状态
        completion_time = datetime.utcnow()
        if simulated_success:
            status = 'ready'
            metrics_json = json.dumps(simulated_metrics) if simulated_metrics else None
            print(f"[FineTune Task {model_id}] Updating status to ready, path: {final_model_filename}")
            cursor.execute("""
                UPDATE models
                SET status = %s, model_path = %s, completion_timestamp = %s, metrics = %s
                WHERE id = %s
            """, (status, final_model_filename, completion_time, metrics_json, model_id))
        else:
            status = 'failed'
            print(f"[FineTune Task {model_id}] Updating status to failed.")
            cursor.execute("""
                UPDATE models SET status = %s, completion_timestamp = %s WHERE id = %s
            """, (status, completion_time, model_id))

        conn.commit()
        print(f"[FineTune Task {model_id}] Database updated with final status: {status}")

    except mysql.connector.Error as err:
        print(f"[FineTune Task {model_id}] Database Error during fine-tuning: {err}")
        if conn and conn.is_connected(): conn.rollback()
        # 尝试将模型状态标记为失败（如果可能）
        try:
            if conn and conn.is_connected() and cursor:
                 print(f"[FineTune Task {model_id}] Attempting to mark model as failed after DB error...")
                 cursor.execute("UPDATE models SET status = %s, completion_timestamp = %s WHERE id = %s",
                                ('failed', datetime.utcnow(), model_id))
                 conn.commit()
                 print(f"[FineTune Task {model_id}] Marked model as failed after DB error.")
        except Exception as inner_e:
            print(f"[FineTune Task {model_id}] Could not mark model as failed after DB error: {inner_e}")

    except Exception as e:
        # 捕获微调逻辑本身可能抛出的非数据库错误
        print(f"[FineTune Task {model_id}] Non-DB Error during fine-tuning: {e}")
        # 尝试将模型状态标记为失败
        try:
             if conn and conn.is_connected() and cursor:
                 print(f"[FineTune Task {model_id}] Attempting to mark model as failed after non-DB error...")
                 cursor.execute("UPDATE models SET status = %s, completion_timestamp = %s WHERE id = %s",
                                ('failed', datetime.utcnow(), model_id))
                 conn.commit()
                 print(f"[FineTune Task {model_id}] Marked model as failed after non-DB error.")
        except Exception as inner_e:
            print(f"[FineTune Task {model_id}] Could not mark model as failed after non-DB error: {inner_e}")

    finally:
        print(f"[FineTune Task {model_id}] Cleaning up...")
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print(f"[FineTune Task {model_id}] Database connection closed.")

        # 可选：清理临时上传的样本文件 (如果微调成功或不再需要)
        # if simulated_success and os.path.exists(sample_file_path):
        #     try:
        #         os.remove(sample_file_path)
        #         print(f"[FineTune Task {model_id}] Removed temporary sample file: {sample_file_path}")
        #     except OSError as e:
        #         print(f"[FineTune Task {model_id}] Error removing temporary sample file {sample_file_path}: {e}")
        print(f"[FineTune Task {model_id}] Finished.")


# --- 模型管理 API 端点 ---

@app.route('/api/base-models', methods=['GET'])
def get_base_models():
    """返回可用的基础模型列表。"""
    # TODO: 从数据库的 base_models 表查询实际数据
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, description FROM base_models ORDER BY name")
        base_models_data = cursor.fetchall()
        return jsonify(base_models_data)
    except mysql.connector.Error as err:
        print(f"Error fetching base models: {err}")
        return jsonify({'message': '获取基础模型列表失败'}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()



@app.route('/api/models/fine-tune/upload', methods=['POST'])
@jwt_required()
def upload_model_sample_data():
    """上传用于模型微调的样本数据 (.zip)。"""
    current_username = get_jwt_identity() # 获取用户名
    # 注意：这里我们没有使用 user_id，因为文件名与用户直接关联不大，使用 UUID 即可

    if 'sample_data' not in request.files:
        return jsonify({"message": "请求中缺少文件部分"}), 400
    file = request.files['sample_data']
    if file.filename == '':
        return jsonify({"message": "未选择上传文件"}), 400

    if file:
        # 检查文件扩展名
        if not file.filename.lower().endswith('.zip'):
             return jsonify({"message": "文件类型无效，只允许上传 .zip 文件"}), 400

        original_filename = secure_filename(file.filename)
        # 使用 UUID 生成唯一的文件引用标识符
        file_ref = str(uuid.uuid4())
        save_path = os.path.join(app.config['SAMPLE_UPLOAD_TEMP_DIR'], f"{file_ref}.zip")

        try:
            file.save(save_path)
            print(f"User '{current_username}' uploaded sample data, ref: {file_ref}, original: {original_filename}, saved to: {save_path}")
            # 返回成功信息和文件引用标识符
            return jsonify({"success": True, "file_ref": file_ref})
        except Exception as e:
            print(f"Failed to save uploaded sample file for user '{current_username}', ref: {file_ref}: {e}")
            return jsonify({"message": "保存上传文件失败"}), 500
    else:
        # 虽然前面检查过 file.filename，但以防万一
        return jsonify({"message": "无效的文件"}), 400

@app.route('/api/models/fine-tune/start', methods=['POST'])
@jwt_required()
def start_fine_tuning():
    """接收微调请求，创建模型记录，并启动后台微调任务。"""
    current_username = get_jwt_identity()
    data = request.get_json()

    if not data or not data.get('name') or not data.get('base_model_id') or not data.get('sample_data_ref'):
        return jsonify({"message": "缺少必要字段：name, base_model_id, sample_data_ref"}), 400

    name = data['name']
    description = data.get('description', '') # 可选字段
    base_model_id = data['base_model_id']
    sample_data_ref = data['sample_data_ref']

    # 验证样本文件是否存在
    sample_file_path = os.path.join(app.config['SAMPLE_UPLOAD_TEMP_DIR'], f"{sample_data_ref}.zip")
    if not os.path.exists(sample_file_path):
         return jsonify({"message": f"无效的 sample_data_ref：找不到文件 {sample_data_ref}.zip"}), 400

    conn = None
    cursor = None
    model_id = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 获取当前用户的 user_id
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_username,))
        user = cursor.fetchone()
        if not user:
            # 理论上 JWT 验证通过后用户应该存在，但还是检查一下
            return jsonify({"message": "用户信息无效"}), 401
        current_user_id = user['id']

        # 2. (可选) 验证 base_model_id 是否存在于 base_models 表
        # cursor.execute("SELECT id FROM base_models WHERE id = %s", (base_model_id,))
        # base_model_exists = cursor.fetchone()
        # if not base_model_exists:
        #     return jsonify({"message": f"无效的基础模型 ID: {base_model_id}"}), 400

        # 3. 在 models 表中插入新记录
        insert_query = """
            INSERT INTO models (user_id, name, description, base_model_id, sample_data_ref, status, creation_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        current_time = datetime.utcnow()
        initial_status = 'creating' # 初始状态
        cursor.execute(insert_query, (
            current_user_id, name, description, base_model_id, sample_data_ref,
            initial_status, current_time
        ))
        model_id = cursor.lastrowid # 获取新插入记录的 ID
        conn.commit() # 提交插入操作

        if not model_id:
            raise mysql.connector.Error("未能插入模型记录或获取 lastrowid")

        print(f"Created new model record {model_id} for user {current_user_id} ('{current_username}')")

        # 4. 准备并启动后台微调线程
        output_dir = os.path.join(app.config['FINE_TUNED_MODELS_DIR'], str(model_id))
        os.makedirs(output_dir, exist_ok=True) # 确保该模型的输出目录存在

        # 准备传递给线程的数据库配置
        db_config_for_thread = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME
        }

        thread = threading.Thread(target=run_fine_tuning_task_mysql, args=(
            model_id, current_user_id, sample_file_path, base_model_id, output_dir, db_config_for_thread
        ))
        thread.daemon = True # 设置为守护线程，主程序退出时线程也退出
        thread.start()
        print(f"Started fine-tuning thread for model {model_id}")

        # 返回 202 Accepted，表示请求已接受，将在后台处理
        return jsonify({"message": "微调任务已成功启动", "model_id": model_id}), 202

    except mysql.connector.Error as err:
        print(f"Database error starting fine-tuning for user '{current_username}': {err}")
        if conn and conn.is_connected(): conn.rollback() # 回滚插入操作（如果已执行）
        return jsonify({"message": f"启动微调任务时发生数据库错误: {err.msg}"}), 500
    except Exception as e:
        print(f"General error starting fine-tuning for user '{current_username}': {e}")
        if conn and conn.is_connected(): conn.rollback()
        # 如果模型记录已创建但线程启动失败，可能需要考虑删除该记录或标记为失败
        return jsonify({"message": "启动微调任务时发生内部错误"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/models', methods=['GET'])
@jwt_required()
def get_user_models():
    """获取当前用户的模型列表。"""
    current_username = get_jwt_identity()
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 获取用户 ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "用户信息无效"}), 401
        current_user_id = user['id']

        # 2. 查询该用户的模型
        select_query = """
            SELECT id, name, description, base_model_id, status, model_path,
                   sample_data_ref, creation_timestamp, completion_timestamp, metrics
            FROM models
            WHERE user_id = %s
            ORDER BY creation_timestamp DESC
        """
        cursor.execute(select_query, (current_user_id,))
        models_raw = cursor.fetchall()

        # 3. 格式化结果
        models_list = []
        for row in models_raw:
            model_dict = dict(row) # 已经是字典了
            # 格式化时间戳为 ISO 格式字符串
            if model_dict.get('creation_timestamp'):
                model_dict['creation_timestamp'] = model_dict['creation_timestamp'].isoformat() + 'Z' # Flask jsonify 会处理 datetime
            if model_dict.get('completion_timestamp'):
                model_dict['completion_timestamp'] = model_dict['completion_timestamp'].isoformat() + 'Z'
            # 解析 metrics JSON 字符串
            if model_dict.get('metrics'):
                try:
                    model_dict['metrics'] = json.loads(model_dict['metrics'])
                except (json.JSONDecodeError, TypeError):
                     print(f"Could not parse metrics JSON for model {model_dict['id']}: {model_dict['metrics']}")
                     model_dict['metrics'] = None # 或者保持为原始字符串
            models_list.append(model_dict)

        return jsonify(models_list)

    except mysql.connector.Error as err:
        print(f"Database error fetching models for user '{current_username}': {err}")
        return jsonify({"message": f"获取模型列表时发生数据库错误: {err.msg}"}), 500
    except Exception as e:
        print(f"General error fetching models for user '{current_username}': {e}")
        return jsonify({"message": "获取模型列表时发生内部错误"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/models/<int:model_id>', methods=['GET'])
@jwt_required()
def get_model_details(model_id):
    """获取指定模型的详细信息（用于状态轮询）。"""
    current_username = get_jwt_identity()
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 获取用户 ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_username,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "用户信息无效"}), 401
        current_user_id = user['id']

        # 2. 查询模型信息，并验证所有权
        select_query = """
            SELECT id, user_id, name, description, base_model_id, status, model_path,
                   sample_data_ref, creation_timestamp, completion_timestamp, metrics
            FROM models WHERE id = %s
        """
        cursor.execute(select_query, (model_id,))
        model_dict = cursor.fetchone()

        if not model_dict:
            return jsonify({"message": "模型未找到"}), 404

        # 3. 验证模型是否属于当前用户
        if model_dict['user_id'] != current_user_id:
             return jsonify({"message": "无权访问此模型"}), 403

        # 4. 格式化结果 (同上)
        if model_dict.get('creation_timestamp'):
            model_dict['creation_timestamp'] = model_dict['creation_timestamp'].isoformat() + 'Z'
        if model_dict.get('completion_timestamp'):
            model_dict['completion_timestamp'] = model_dict['completion_timestamp'].isoformat() + 'Z'
        if model_dict.get('metrics'):
            try:
                model_dict['metrics'] = json.loads(model_dict['metrics'])
            except (json.JSONDecodeError, TypeError):
                 model_dict['metrics'] = None

        return jsonify(model_dict)

    except mysql.connector.Error as err:
        print(f"Database error fetching model {model_id} for user '{current_username}': {err}")
        return jsonify({"message": f"获取模型详情时发生数据库错误: {err.msg}"}), 500
    except Exception as e:
        print(f"General error fetching model {model_id} for user '{current_username}': {e}")
        return jsonify({"message": "获取模型详情时发生内部错误"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/models/<int:model_id>', methods=['DELETE'])
@jwt_required()
def delete_user_model(model_id):
    """删除用户指定的模型。"""
    current_username = get_jwt_identity()
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        # 注意：删除操作，最好开启事务控制
        # conn.start_transaction() # 如果 MySQL 版本和配置支持
        cursor = conn.cursor(dictionary=True)

        # 1. 获取用户 ID
        cursor.execute("SELECT id FROM users WHERE username = %s", (current_username,))
        user = cursor.fetchone()
        if not user:
            # conn.rollback() # 如果开启了事务
            return jsonify({"message": "用户信息无效"}), 401
        current_user_id = user['id']

        # 2. 获取模型信息，验证所有权和状态
        cursor.execute("SELECT user_id, status, model_path FROM models WHERE id = %s", (model_id,))
        model_info = cursor.fetchone()

        if not model_info:
            # conn.rollback()
            return jsonify({"message": "模型未找到"}), 404

        if model_info['user_id'] != current_user_id:
            # conn.rollback()
            return jsonify({"message": "无权删除此模型"}), 403

        if model_info['status'] in ['creating', 'fine-tuning']:
            # conn.rollback()
            return jsonify({"message": "不能删除正在处理中的模型"}), 400

        # 3. 删除关联的模型文件/目录 (如果存在)
        #    注意：这部分需要非常小心，确保路径正确且安全
        model_output_dir = os.path.join(app.config['FINE_TUNED_MODELS_DIR'], str(model_id))
        if os.path.exists(model_output_dir) and os.path.isdir(model_output_dir):
            try:
                shutil.rmtree(model_output_dir) # 使用 shutil 删除整个目录及其内容
                print(f"Deleted model output directory: {model_output_dir}")
            except OSError as e:
                print(f"Error deleting model directory {model_output_dir} for model {model_id}: {e}")
                # 重要：决定是否因为文件删除失败而中止数据库删除
                # conn.rollback()
                # return jsonify({"message": "删除模型文件时出错，操作已中止"}), 500

        # 4. 从数据库删除模型记录
        cursor.execute("DELETE FROM models WHERE id = %s", (model_id,))
        conn.commit() # 提交删除操作
        print(f"Deleted model {model_id} for user {current_user_id} ('{current_username}')")

        return jsonify({"message": "模型已成功删除"}), 200

    except mysql.connector.Error as err:
        print(f"Database error deleting model {model_id} for user '{current_username}': {err}")
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({"message": f"删除模型时发生数据库错误: {err.msg}"}), 500
    except Exception as e:
        print(f"General error deleting model {model_id} for user '{current_username}': {e}")
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({"message": "删除模型时发生内部错误"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()



@app.route('/api/tasks/<int:task_id>/settings', methods=['GET'])
@jwt_required()
def get_task_settings(task_id):
    """获取指定任务的已保存设置"""
    current_username = get_jwt_identity()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 验证任务所有权
        cursor.execute("SELECT creator_username, selected_model_id, review_mode FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()

        if not task:
            return jsonify({'message': '任务未找到'}), 404
        if task['creator_username'] != current_username:
            return jsonify({'message': '无权访问该任务设置'}), 403

        # 2. 返回设置 (从 tasks 表直接读取，或从专门的设置文件/表读取)
        settings = {
            "selected_model_id": task.get('selected_model_id'), # May be NULL or a string/int
            "review_mode": task.get('review_mode', 'standard') # Default if not set
        }

        # Handle potential type issue for selected_model_id if stored as string but should be int
        # Example: If ID '25' is stored as string, convert it to int for consistency? Or handle in frontend.
        # For now, return as stored. Frontend JS can handle string/number comparison loosely.
        # if settings['selected_model_id'] and settings['selected_model_id'].isdigit():
        #     settings['selected_model_id'] = int(settings['selected_model_id'])

        return jsonify({'settings': settings})

    except mysql.connector.Error as err:
        print(f"Database error getting settings for task {task_id}: {err}")
        return jsonify({'message': '获取任务设置时发生数据库错误'}), 500
    except Exception as e:
        print(f"Error getting settings for task {task_id}: {e}")
        return jsonify({'message': '获取任务设置时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/tasks/<int:task_id>/settings', methods=['POST'])
@jwt_required()
def save_task_settings(task_id):
    """保存任务设置，并更新任务到下一阶段"""
    current_username = get_jwt_identity()
    data = request.get_json()

    if not data or 'selected_model_id' not in data or 'review_mode' not in data:
        return jsonify({'message': '缺少必要的设置参数 (selected_model_id, review_mode)'}), 400

    selected_model_id = data['selected_model_id'] # Can be string or int
    review_mode = data['review_mode']

    # Basic validation (more robust validation might be needed)
    if not selected_model_id:
         return jsonify({'message': '必须选择一个模型'}), 400
    if review_mode not in ['fast', 'standard', 'strict']:
        return jsonify({'message': '无效的审查模式'}), 400

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. 验证任务所有权
        cursor.execute("SELECT creator_username, current_stage FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()

        if not task:
            return jsonify({'message': '任务未找到'}), 404
        if task['creator_username'] != current_username:
            return jsonify({'message': '无权修改该任务设置'}), 403
        # Optional: Check if current_stage is actually 2 before allowing save
        # if task['current_stage'] != 2:
        #    return jsonify({'message': '当前任务阶段不允许修改设置'}), 400

        # 2. 更新 tasks 表 (或专用设置表/文件)
        #    Ensure your tasks table has 'selected_model_id' (e.g., VARCHAR(255) to hold string or number)
        #    and 'review_mode' (e.g., VARCHAR(50)) columns. Add them if they don't exist.
        update_task_sql = """
            UPDATE tasks
            SET selected_model_id = %s,
                review_mode = %s,
                current_stage = 3, -- Move to next stage
                updated_at = NOW()
            WHERE id = %s
        """
        # Convert model ID to string for storage consistency, or handle type in DB schema
        cursor.execute(update_task_sql, (str(selected_model_id), review_mode, task_id))

        # 3. 更新 task_stages 表，标记 stage 2 为完成
        update_stage_sql = """
            UPDATE task_stages
            SET status = 'completed',
                progress = 100,
                updated_at = NOW()
            WHERE task_id = %s AND stage_number = 2
        """
        cursor.execute(update_stage_sql, (task_id,))

        conn.commit() # Commit both updates

        print(f"Task {task_id} settings saved: model={selected_model_id}, mode={review_mode}. Moved to stage 3.")
        return jsonify({'success': True, 'message': '设置已成功保存'})

    except mysql.connector.Error as err:
        if conn: conn.rollback()
        print(f"Database error saving settings for task {task_id}: {err}")
        return jsonify({'message': '保存任务设置时发生数据库错误'}), 500
    except Exception as e:
        if conn: conn.rollback()
        print(f"Error saving settings for task {task_id}: {e}")
        return jsonify({'message': '保存任务设置时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# --- NEW Endpoint for Base Model Details ---

@app.route('/api/base-models/<string:base_model_id>', methods=['GET'])
def get_base_model_detail(base_model_id):
    """获取指定基础模型的详细信息，包括模拟的指标"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query the base_models table
        cursor.execute("SELECT id, name, description, metrics FROM base_models WHERE id = %s", (base_model_id,))
        base_model = cursor.fetchone()

        if not base_model:
            return jsonify({'message': '基础模型未找到'}), 404

        # ** Add Representative Metrics Here **
        # These should ideally be stored with the base model definition or calculated
        # For now, we provide fixed representative metrics based on ID
        # representative_metrics = {}
        # if base_model_id == 'generic-map-v1':
        #     representative_metrics = {"elementCoverage": 78, "responseSpeed": 85, "errorDetection": 75, "complexStructure": 70, "ruleCompatibility": 80, "resourceConsumption": 65}
        # elif base_model_id == 'building-dense-v1.2':
        #     representative_metrics = {"elementCoverage": 88, "responseSpeed": 78, "errorDetection": 85, "complexStructure": 80, "ruleCompatibility": 82, "resourceConsumption": 75}
        # elif base_model_id == 'vegetation-id-v2':
        #     representative_metrics = {"elementCoverage": 82, "responseSpeed": 80, "errorDetection": 88, "complexStructure": 78, "ruleCompatibility": 85, "resourceConsumption": 70}
        # else:
        #     # Default fallback metrics if ID doesn't match known ones
        #     representative_metrics = {"elementCoverage": 70, "responseSpeed": 70, "errorDetection": 70, "complexStructure": 60, "ruleCompatibility": 70, "resourceConsumption": 70}

        base_model['metrics'] = json.loads(base_model['metrics'])

        return jsonify(base_model)

    except mysql.connector.Error as err:
        print(f"Database error getting base model {base_model_id}: {err}")
        return jsonify({'message': '获取基础模型详情时发生数据库错误'}), 500
    except Exception as e:
        print(f"Error getting base model {base_model_id}: {e}")
        return jsonify({'message': '获取基础模型详情时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


#-----------------------------------------#
#          样例库相关的api                 #
#          创建人：朱楠                    #
#          创建时间：4-15                  #
#                                         #
#                                         #
#                                         #
#-----------------------------------------#
@app.route('/api/error-examples', methods=['GET'])
# @jwt_required() # 根据是否需要登录访问决定是否添加认证
def get_error_examples():
    """获取错误检测样例列表"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection() # 使用你现有的函数
        cursor = conn.cursor(dictionary=True)

        # 查询所有样例，可以添加分页或筛选参数
        # 例如： request.args.get('category'), request.args.get('page')
        query = "SELECT id, layer_name, error_category, error_type, description, solution, image_before_url, image_after_url, severity FROM error_examples ORDER BY error_category, id"
        cursor.execute(query)
        examples = cursor.fetchall()

        # 确保图片 URL 是前端可访问的完整 URL 或正确的相对路径
        # 如果存储的是相对路径，可能需要在这里拼接基础 URL
        base_static_url = 'http://localhost:5000/api/error-examples/image/' # 示例
        for example in examples:
            if example.get('image_before_url'):
                example['image_before_url'] = base_static_url + example['image_before_url']
            if example.get('image_after_url'):
                example['image_after_url'] = base_static_url + example['image_after_url']

        return jsonify(examples)

    except mysql.connector.Error as err:
        print(f"Database error fetching error examples: {err}")
        return jsonify({'message': '获取样例库数据时发生数据库错误'}), 500
    except Exception as e:
        print(f"Error fetching error examples: {e}")
        return jsonify({'message': '获取样例库数据时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

@app.route('/api/error-examples/image/<path:filename>')
def get_error_examples_image(filename):
    file_path = os.path.join(ERROR_EXAMPLE_FOLDER, filename)
    print(file_path)
    if os.path.exists(file_path):
        return send_from_directory(ERROR_EXAMPLE_FOLDER, filename)
    else:
        return jsonify({'message': '图片不存在'}), 404
# --- 如果图片存储在 static 目录，需要确保 Flask 能提供静态文件服务 ---
# Flask 默认从 static 文件夹提供服务，路径是 /static/<filename>
# 如果你的图片放在 back/static/error_examples/ 下
# 前端访问 URL 应类似 /static/error_examples/example1_before.png

#----------------------------------#
#        用户个人规则库             #
#        创建人：朱楠               #
#        创建时间：4-16             #
#                                  #
#                                  #
#                                  #
#----------------------------------#
def get_user_id_from_username(username):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        return user['id'] if user else None
    except mysql.connector.Error as err:
        print(f"Database Error getting user ID for {username}: {err}")
        return None
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


@app.route('/api/rules', methods=['GET'])
@jwt_required(optional=True)
def get_rules():
    scope = request.args.get('scope', 'public')
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if scope == 'public':
            # Select CORRECT image fields from 'error_examples'
            query = """
                SELECT id, layer_name, error_category, error_type, description, solution,
                       image_before_url, image_after_url,  -- Corrected fields
                       severity
                FROM error_examples
                ORDER BY error_category, id
            """
            cursor.execute(query)
            rules = cursor.fetchall()
            # Adjust public image URLs (points to existing route for public images)
            base_public_image_url = '/api/error-examples/image/'
            for rule in rules:
                 # Use correct field names
                 if rule.get('image_before_url'):
                     rule['image_before_url'] = base_public_image_url + rule['image_before_url']
                 if rule.get('image_after_url'):
                     rule['image_after_url'] = base_public_image_url + rule['image_after_url']

        elif scope == 'user':
            current_username = get_jwt_identity()
            if not current_username:
                 return jsonify({"message": "需要认证才能访问用户规则"}), 401

            current_user_id = get_user_id_from_username(current_username)
            if not current_user_id:
                 return jsonify({"message": "无法验证用户信息"}), 401

            # Select CORRECT image fields from 'user_error_examples'
            query = """
                SELECT id, owner_user_id, layer_name, error_category, error_type, description, solution,
                       image_before_url, image_after_url, -- Corrected fields
                       severity
                FROM user_error_examples
                WHERE owner_user_id = %s
                ORDER BY error_category, id
            """
            cursor.execute(query, (current_user_id,))
            rules = cursor.fetchall()
            # Adjust user image URLs (points to NEW route for user images)
            base_user_image_url = '/api/user-error-examples/image/' # Use the NEW route
            for rule in rules:
                 # Use correct field names. Path stored is '<user_id>/filename.ext'
                 if rule.get('image_before_url'):
                     rule['image_before_url'] = base_user_image_url + rule['image_before_url']
                 if rule.get('image_after_url'):
                     rule['image_after_url'] = base_user_image_url + rule['image_after_url']

        else:
            return jsonify({"message": "无效的 scope 参数"}), 400

        return jsonify(rules)

    except mysql.connector.Error as err:
        print(f"Database error fetching rules (scope: {scope}): {err}")
        return jsonify({'message': '获取规则数据时发生数据库错误'}), 500
    except Exception as e:
        print(f"Error fetching rules (scope: {scope}): {e}")
        return jsonify({'message': '获取规则数据时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# POST User Rule (Create)
@app.route('/api/user-rules', methods=['POST'])
@jwt_required()
def create_user_rule():
    current_username = get_jwt_identity()
    current_user_id = get_user_id_from_username(current_username)
    if not current_user_id:
        return jsonify({"message": "无法验证用户信息"}), 401

    data = request.form
    files = request.files

    required_fields = ['layer_name', 'error_category', 'error_type', 'severity', 'description', 'solution']
    if not all(field in data for field in required_fields):
        return jsonify({"message": "缺少必要的表单字段"}), 400

    error_type = data.get('error_type')
    conn = None
    cursor = None
    print(data)
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT id FROM user_error_examples WHERE owner_user_id = %s AND error_type = %s",
            (current_user_id, error_type)
        )
        existing_rule = cursor.fetchone()
        if existing_rule:
             return jsonify({"message": f"错误类型 '{error_type}' 已存在于您的规则库中"}), 409

        # --- File Handling ---
        image_paths = {} # Stores relative paths for DB: {'image_before_url': 'user_id/filename.ext'}
        # Use the CORRECTED base path
        user_upload_dir_abs_base = app.config['USER_RULE_IMAGE_FOLDER']
        user_upload_dir_abs_user = os.path.join(user_upload_dir_abs_base, str(current_user_id))
        os.makedirs(user_upload_dir_abs_user, exist_ok=True) # Ensure specific user's subdir exists

        # Use CORRECTED form keys expected from frontend
        for form_key in ['image_before', 'image_after']:
            db_key = f"{form_key}_url" # e.g., image_before_url
            if form_key in files:
                file = files[form_key]
                if file and file.filename:
                    if allowed_file(file.filename):
                        unique_suffix = uuid.uuid4().hex
                        filename = secure_filename(f"{unique_suffix}_{file.filename}")
                        # Relative path includes user_id subdir
                        relative_path = os.path.join(str(current_user_id), filename)
                        # Absolute path uses the user-specific subdir
                        absolute_save_path = os.path.join(user_upload_dir_abs_user, filename)

                        try:
                            file.save(absolute_save_path)
                            image_paths[db_key] = relative_path # Store relative path '<user_id>/filename.ext'
                            print(f"Saved user rule image: {absolute_save_path}")
                        except Exception as e:
                             print(f"Error saving file {form_key}: {e}")
                             return jsonify({"message": f"保存图片 {form_key} 失败"}), 500
                    else:
                         return jsonify({"message": f"无效的文件类型: {file.filename}"}), 400

        # --- Create and Save Rule ---
        # Use CORRECTED image field names in SQL
        insert_query = """
            INSERT INTO user_error_examples (
                owner_user_id, layer_name, error_category, error_type, description, solution,
                image_before_url, image_after_url,
                 severity
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) -- Adjusted placeholder count
        """
        insert_values = (
            current_user_id,
            data.get('layer_name'),
            data.get('error_category'),
            error_type,
            data.get('description'),
            data.get('solution'),
            image_paths.get('image_before_url'), # Use correct key
            image_paths.get('image_after_url'),  # Use correct key
            data.get('severity')
        )
        cursor.execute(insert_query, insert_values)
        new_rule_id = cursor.lastrowid
        conn.commit()

        cursor.execute("SELECT * FROM user_error_examples WHERE id = %s", (new_rule_id,))
        new_rule = cursor.fetchone()

        if new_rule:
            base_user_image_url = '/api/user-error-examples/image/' # Use NEW route
            # Use correct field names
            for key in ['image_before_url', 'image_after_url']:
                 if new_rule.get(key):
                      new_rule[key] = base_user_image_url + new_rule[key]

        return jsonify(new_rule), 201

    except mysql.connector.Error as err:
        print(f"Database error creating user rule: {err}")
        if conn: conn.rollback()
        # Cleanup potentially saved files
        for path_suffix in image_paths.values():
             if path_suffix:
                  abs_path = os.path.join(app.config['USER_RULE_IMAGE_FOLDER'], path_suffix)
                  if os.path.exists(abs_path):
                      try: os.remove(abs_path)
                      except OSError: pass
        return jsonify({"message": "创建规则时发生数据库错误"}), 500
    except Exception as e:
        print(f"Error creating user rule: {e}")
        if conn: conn.rollback()
        return jsonify({"message": "创建规则时发生内部错误"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# PUT/PATCH User Rule (Update)
@app.route('/api/rules/<int:rule_id>', methods=['PUT', 'PATCH'])
@jwt_required()
def update_user_rule(rule_id):
     current_username = get_jwt_identity()
     current_user_id = get_user_id_from_username(current_username)
     if not current_user_id:
         return jsonify({"message": "无法验证用户信息"}), 401

     data = request.form
     files = request.files
     conn = None
     cursor = None

     try:
         conn = get_db_connection()
         cursor = conn.cursor(dictionary=True)

         cursor.execute(
             "SELECT * FROM user_error_examples WHERE id = %s AND owner_user_id = %s",
             (rule_id, current_user_id)
         )
         rule = cursor.fetchone()
         if not rule:
              return jsonify({"message": "规则未找到或无权修改"}), 404

         update_fields = []
         update_values = []

         new_error_type = data.get('error_type')
         if new_error_type and new_error_type != rule['error_type']:
             cursor.execute(
                 "SELECT id FROM user_error_examples WHERE owner_user_id = %s AND error_type = %s AND id != %s",
                 (current_user_id, new_error_type, rule_id)
             )
             existing = cursor.fetchone()
             if existing:
                  return jsonify({"message": f"错误类型 '{new_error_type}' 已存在"}), 409
             update_fields.append("error_type = %s")
             update_values.append(new_error_type)

         for field in ['layer_name', 'error_category', 'severity', 'description', 'solution']:
             if field in data:
                 update_fields.append(f"{field} = %s")
                 update_values.append(data[field])

         # --- Handle Image Updates ---
         # Use CORRECTED form keys and DB keys
         image_keys = {'image_before': 'image_before_url', 'image_after': 'image_after_url'}
         user_upload_dir_abs_base = app.config['USER_RULE_IMAGE_FOLDER'] # Correct base path
         user_upload_dir_abs_user = os.path.join(user_upload_dir_abs_base, str(current_user_id))
         os.makedirs(user_upload_dir_abs_user, exist_ok=True)

         for form_key, db_key in image_keys.items():
             if form_key in files:
                 file = files[form_key]
                 if file and file.filename:
                     if allowed_file(file.filename):
                         # Delete old file
                         old_path_suffix = rule.get(db_key)
                         if old_path_suffix:
                              # Absolute path uses the CORRECTED base path
                              old_abs_path = os.path.join(user_upload_dir_abs_base, old_path_suffix)
                              if os.path.exists(old_abs_path):
                                  try:
                                      os.remove(old_abs_path)
                                      print(f"Deleted old image: {old_abs_path}")
                                  except OSError as e:
                                      print(f"Error deleting old image {old_abs_path}: {e}")

                         # Save new file
                         unique_suffix = uuid.uuid4().hex
                         filename = secure_filename(f"{unique_suffix}_{file.filename}")
                         # Relative path includes user_id subdir
                         relative_path = os.path.join(str(current_user_id), filename)
                         # Absolute path uses the user-specific subdir
                         absolute_save_path = os.path.join(user_upload_dir_abs_user, filename)

                         try:
                             file.save(absolute_save_path)
                             update_fields.append(f"{db_key} = %s")
                             update_values.append(relative_path)
                             print(f"Saved updated user rule image: {absolute_save_path}")
                         except Exception as e:
                              print(f"Error saving updated file {form_key}: {e}")
                              return jsonify({"message": f"保存更新后的图片 {form_key} 失败"}), 500
                     else:
                         return jsonify({"message": f"无效的文件类型: {file.filename}"}), 400

         if not update_fields:
             # Return existing data with correct image URLs
             base_user_image_url = '/api/user-error-examples/image/'
             for key in ['image_before_url', 'image_after_url']:
                 if rule.get(key):
                     rule[key] = base_user_image_url + rule[key]
             return jsonify(rule)

         update_query = f"UPDATE user_error_examples SET {', '.join(update_fields)} WHERE id = %s AND owner_user_id = %s"
         update_values.extend([rule_id, current_user_id])
         cursor.execute(update_query, tuple(update_values))
         conn.commit()

         cursor.execute("SELECT * FROM user_error_examples WHERE id = %s", (rule_id,))
         updated_rule = cursor.fetchone()

         if updated_rule:
            base_user_image_url = '/api/user-error-examples/image/' # Use NEW route
            # Use correct field names
            for key in ['image_before_url', 'image_after_url']:
                 if updated_rule.get(key):
                      updated_rule[key] = base_user_image_url + updated_rule[key]

         return jsonify(updated_rule)

     except mysql.connector.Error as err:
        print(f"Database error updating rule {rule_id}: {err}")
        if conn: conn.rollback()
        return jsonify({"message": "更新规则时发生数据库错误"}), 500
     except Exception as e:
        print(f"Error updating rule {rule_id}: {e}")
        if conn: conn.rollback()
        return jsonify({"message": "更新规则时发生内部错误"}), 500
     finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# DELETE User Rule
@app.route('/api/rules/<int:rule_id>', methods=['DELETE'])
@jwt_required()
def delete_user_rule(rule_id):
    current_username = get_jwt_identity()
    current_user_id = get_user_id_from_username(current_username)
    if not current_user_id:
        return jsonify({"message": "无法验证用户信息"}), 401

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Fetch rule details using CORRECT field names
        cursor.execute(
            "SELECT owner_user_id, image_before_url, image_after_url FROM user_error_examples WHERE id = %s",
            (rule_id,)
        )
        rule = cursor.fetchone()

        if not rule:
            return jsonify({"message": "规则未找到"}), 404
        if rule['owner_user_id'] != current_user_id:
             return jsonify({"message": "无权删除此规则"}), 403

        # --- Delete Associated Images ---
        # Use CORRECTED field names and base path
        image_keys = ['image_before_url', 'image_after_url']
        user_upload_dir_abs_base = app.config['USER_RULE_IMAGE_FOLDER'] # Correct base path

        for db_key in image_keys:
            path_suffix = rule.get(db_key) # Path suffix is '<user_id>/filename.ext'
            if path_suffix:
                abs_path = os.path.join(user_upload_dir_abs_base, path_suffix)
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                        print(f"Deleted rule image: {abs_path}")
                    except OSError as e:
                         print(f"Error deleting image file {abs_path}: {e}")

        # --- Delete Rule from DB ---
        cursor.execute("DELETE FROM user_error_examples WHERE id = %s AND owner_user_id = %s", (rule_id, current_user_id))
        affected_rows = cursor.rowcount
        conn.commit()

        if affected_rows > 0:
            return jsonify({"message": "规则删除成功"}), 200
        else:
            return jsonify({"message": "删除规则失败或规则不存在"}), 404

    except mysql.connector.Error as err:
        print(f"Database error deleting rule {rule_id}: {err}")
        if conn: conn.rollback()
        return jsonify({"message": "删除规则时发生数据库错误"}), 500
    except Exception as e:
        print(f"Error deleting rule {rule_id}: {e}")
        if conn: conn.rollback()
        return jsonify({"message": "删除规则时发生内部错误"}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()

# --- Static File Serving for User Rule Images ---
@app.route('/api/user-error-examples/image/<path:filepath>')
# Optional: Add @jwt_required() if images should only be accessed by the owner
def serve_user_rule_image_corrected(filepath):
    # IMPORTANT: Filepath is expected to be '<user_id>/<filename.ext>' as saved in DB
    if '..' in filepath or filepath.startswith('/') or filepath.startswith('\\'):
        print(f"Attempted directory traversal in user rule images: {filepath}")
        abort(400, description="无效路径")
    try:
        # Serve from the CORRECTED base folder
        print(f"Serving user rule image from: {app.config['USER_RULE_IMAGE_FOLDER']} with path: {filepath}")
        # send_from_directory needs the BASE directory and the RELATIVE path within it
        return send_from_directory(app.config['USER_RULE_IMAGE_FOLDER'], filepath)
    except FileNotFoundError:
         print(f"User rule image not found: {filepath}")
         abort(404, description="图片文件未找到。")
    except Exception as e:
        print(f"Error serving user rule image {filepath}: {e}")
        abort(500, description="无法提供图片文件。")

#------------------------------#
#        用户反馈               #
#        创建人：朱楠           #
#        创建时间：4-17         #
#                              #
#                              #
#------------------------------#
# --- NEW: Submit Feedback Endpoint ---
@app.route('/api/tasks/<int:task_id>/feedback/submit', methods=['POST'])
@jwt_required()
def submit_task_feedback(task_id):
    current_username = get_jwt_identity()
    current_user_id = get_user_id_from_username(current_username)
    if not current_user_id:
        return jsonify({"message": "无法验证用户信息"}), 401

    conn = None
    cursor = None

    # --- Debugging: Print Request Info ---
    print(f"--- Feedback Submit Request for Task {task_id} ---")
    print(f"Request Content-Type: {request.content_type}")
    print(f"Request Form Data: {request.form}")
    print(f"Request Files: {request.files}")
    # --- End Debugging Info ---

    try:
        # 1. Verify Task Ownership
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT creator_username FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            return jsonify({'message': '任务未找到'}), 404
        if task['creator_username'] != current_username:
            return jsonify({'message': '无权访问该任务'}), 403

        # 2. Get Form Data (text fields)
        data = request.form
        category = data.get('category')
        description = data.get('description')
        related_info = data.get('related_info', '')
        suggestion = data.get('suggestion', '')

        if not category or not description:
            return jsonify({'message': '反馈类别和详细描述不能为空'}), 400

        # 3. Prepare Feedback Directory
        feedback_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'feedback')
        os.makedirs(feedback_dir, exist_ok=True)
        print(f"Feedback directory: {feedback_dir}") # Debug directory path

        # 4. Handle Optional Image Upload
        image_relative_path = None # Initialize as None
        # --- Check if the key exists in request.files ---
        if 'feedback_image' in request.files:
            file = request.files['feedback_image']
            print(f"Found 'feedback_image' key in files.")
            print(f"File object: {file}")
            print(f"File filename: {file.filename}")

            # --- Check if a file was actually uploaded ---
            if file and file.filename:
                 print(f"File has a name: {file.filename}")
                 # --- Check if file type is allowed ---
                 if allowed_file(file.filename):
                    print(f"File type allowed.")
                    # Generate unique filename for the image
                    timestamp = int(time.time())
                    original_filename, file_ext = os.path.splitext(file.filename)
                    secure_original = secure_filename(original_filename)
                    image_filename = f"feedback_image_{timestamp}_{secure_original}{file_ext}"
                    image_save_path = os.path.join(feedback_dir, image_filename)
                    print(f"Attempting to save image to: {image_save_path}") # Debug save path

                    try:
                        file.save(image_save_path)
                        image_relative_path = image_filename # Store just the filename
                        print(f"SUCCESS: Saved feedback image: {image_save_path}")
                    except Exception as e:
                        # --- Log the specific save error ---
                        print(f"ERROR: Failed to save feedback image for task {task_id}: {e}")
                        # traceback.print_exc() # Uncomment for full stack trace
                        # Optionally return error, or just proceed without image
                        # return jsonify({'message': f'保存反馈图片失败: {e}'}), 500
                        image_relative_path = None # Ensure it remains None if save fails
                        print("WARNING: Proceeding without saved image due to error.")

                 else: # File type not allowed
                    print(f"ERROR: File type not allowed: {file.filename}")
                    # Return error as this is likely a user mistake
                    return jsonify({'message': f'不支持的图片文件类型: {file.filename}'}), 400
            else:
                print("WARNING: 'feedback_image' key exists, but file object or filename is empty/invalid.")
        else:
             print("INFO: No 'feedback_image' key found in request.files.")


        # 5. Prepare JSON Data (image_filename will be None if upload failed/skipped)
        feedback_content = {
            "submitted_by_user_id": current_user_id,
            "submitted_by_username": current_username,
            "submitted_at": datetime.now().isoformat(),
            "category": category,
            "related_info": related_info,
            "description": description,
            "suggestion": suggestion,
            "image_filename": image_relative_path # This will be None if image wasn't saved
        }
        print(f"Feedback JSON content being saved: {feedback_content}") # Debug JSON content

        # 6. Save JSON File (Logic remains the same)
        json_timestamp = int(time.time())
        json_filename = f"feedback_{json_timestamp}.json"
        json_save_path = os.path.join(feedback_dir, json_filename)
        try:
            with open(json_save_path, 'w', encoding='utf-8') as f:
                json.dump(feedback_content, f, ensure_ascii=False, indent=4)
            print(f"SUCCESS: Saved feedback JSON: {json_save_path}")
        except Exception as e:
            print(f"ERROR: Failed to save feedback JSON for task {task_id}: {e}")
            # traceback.print_exc() # Uncomment for full stack trace
            # Cleanup saved image ONLY if JSON saving fails AFTER image save succeeded
            if image_relative_path: # Check if image was supposedly saved
                image_cleanup_path = os.path.join(feedback_dir, image_relative_path)
                if os.path.exists(image_cleanup_path):
                    try:
                        os.remove(image_cleanup_path)
                        print(f"INFO: Cleaned up image file {image_cleanup_path} due to JSON save error.")
                    except OSError as rm_err:
                         print(f"WARNING: Could not clean up image file {image_cleanup_path}: {rm_err}")
            return jsonify({'message': '保存反馈信息失败'}), 500

        # 7. Update Database: Set has_feedback = 1 (Logic remains the same)
        cursor.execute("UPDATE tasks SET has_feedback = 1 WHERE id = %s", (task_id,))
        conn.commit()
        print(f"SUCCESS: Updated has_feedback flag for task {task_id}")

        return jsonify({'message': '反馈提交成功'}), 200

    # --- Error handling remains the same ---
    except mysql.connector.Error as err:
        print(f"Database error submitting feedback for task {task_id}: {err}")
        if conn: conn.rollback()
        return jsonify({'message': '提交反馈时发生数据库错误'}), 500
    except Exception as e:
        print(f"ERROR submitting feedback for task {task_id}: {e}")
        # traceback.print_exc() # Uncomment for full stack trace
        if conn: conn.rollback()
        return jsonify({'message': '提交反馈时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# --- NEW: Get Submitted Feedback Endpoint ---
@app.route('/api/tasks/<int:task_id>/feedback', methods=['GET'])
@jwt_required()
def get_task_feedback(task_id):
    current_username = get_jwt_identity()
    conn = None
    cursor = None

    try:
        # 1. Verify Task Ownership
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT creator_username FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            return jsonify({'message': '任务未找到'}), 404
        if task['creator_username'] != current_username:
            return jsonify({'message': '无权访问该任务的反馈'}), 403

        # 2. Find Feedback Directory
        feedback_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'feedback')
        if not os.path.exists(feedback_dir) or not os.path.isdir(feedback_dir):
            return jsonify([]) # Return empty list if no feedback directory exists

        # 3. Read and Parse JSON files
        feedback_list = []
        for filename in sorted(os.listdir(feedback_dir)): # Sort to get chronological order?
            if filename.lower().endswith('.json'):
                json_path = os.path.join(feedback_dir, filename)
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        feedback_data = json.load(f)
                        # Optionally add a link to the image if filename exists
                        if feedback_data.get('image_filename'):
                            # Construct the URL for the feedback image serving endpoint
                            # Ensure this endpoint exists and works correctly
                            feedback_data['image_url'] = f'/api/tasks/files/task_{task_id}/feedback/image/{feedback_data["image_filename"]}'
                        feedback_list.append(feedback_data)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON file: {json_path}")
                except Exception as e:
                    print(f"Error reading feedback file {json_path}: {e}")

        return jsonify(feedback_list)

    except mysql.connector.Error as err:
        print(f"Database error getting feedback for task {task_id}: {err}")
        return jsonify({'message': '获取反馈列表时发生数据库错误'}), 500
    except Exception as e:
        print(f"Error getting feedback for task {task_id}: {e}")
        return jsonify({'message': '获取反馈列表时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()


# --- NEW: Endpoint to Serve Feedback Images ---
@app.route('/api/tasks/files/task_<int:task_id>/feedback/image/<path:filename>')
# @jwt_required() # Protect images if needed
def serve_feedback_image(task_id, filename):
    # current_username = get_jwt_identity()
    conn = None
    cursor = None
    try:
        # Optional but recommended: Verify task ownership before serving image
        # conn = get_db_connection()
        # cursor = conn.cursor(dictionary=True)
        # cursor.execute("SELECT creator_username FROM tasks WHERE id = %s", (task_id,))
        # task = cursor.fetchone()
        # if not task:
        #     abort(404, description="任务未找到")
        # if task['creator_username'] != current_username:
        #     abort(403, description="无权访问此任务的反馈图片")

        # Construct the path to the specific task's feedback directory
        feedback_dir = os.path.join(TASK_FOLDER, f'task_{task_id}', 'feedback')

        # Securely serve the file from that directory
        # Prevent path traversal by checking filename format or using secure_filename
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
             abort(400, description="无效的文件名")

        # Check if file exists before sending
        if not os.path.exists(os.path.join(feedback_dir, filename)):
             abort(404, description="反馈图片未找到")

        return send_from_directory(feedback_dir, filename)

    except mysql.connector.Error as err:
        print(f"DB error checking ownership for feedback image task {task_id}: {err}")
        abort(500, description="服务器错误")
    except Exception as e:
        print(f"Error serving feedback image task {task_id}, file {filename}: {e}")
        abort(500, description="无法提供反馈图片")
    finally:
         if cursor: cursor.close()
         if conn and conn.is_connected(): conn.close()


# --- MODIFY: Complete Feedback Stage Endpoint ---
@app.route('/api/tasks/<int:task_id>/feedback/complete', methods=['POST'])
@jwt_required()
def complete_feedback(task_id):
    current_username = get_jwt_identity() # Added for ownership check
    conn = None
    cursor = None
    try:
        # data = request.get_json() # No longer need to get has_feedback from request
        # has_feedback = data.get('has_feedback', False) # This is now set by the /submit endpoint

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 1. Verify Task Ownership (Important!)
        cursor.execute("SELECT creator_username FROM tasks WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            return jsonify({'message': '任务未找到'}), 404
        if task['creator_username'] != current_username:
            return jsonify({'message': '无权修改该任务'}), 403

        # 2. Update Task Stage Status
        cursor.execute('''
            UPDATE task_stages
            SET status = 'completed', progress = 100, updated_at = NOW()
            WHERE task_id = %s AND stage_number = 6
        ''', (task_id,))

        # 3. Update Main Task Status (Only update status/stage, NOT has_feedback)
        cursor.execute('''
            UPDATE tasks
            SET status = 'completed', current_stage = 6, updated_at = NOW()
            WHERE id = %s
        ''', (task_id,))
        # Removed has_feedback update from here

        conn.commit()

        return jsonify({'message': '反馈阶段标记完成'}) # Adjusted message

    except mysql.connector.Error as err: # Catch specific DB errors
        print(f'完成反馈阶段数据库失败 (Task {task_id}): {err}')
        if conn: conn.rollback()
        return jsonify({'message': '完成反馈阶段时发生数据库错误'}), 500
    except Exception as e:
        print(f'完成反馈阶段失败 (Task {task_id}): {e}')
        if conn: conn.rollback()
        return jsonify({'message': '完成反馈阶段时发生内部错误'}), 500
    finally:
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()
if __name__ == '__main__':
    app.run(debug=True) 