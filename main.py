import os
import subprocess
import configparser
import logging
import time
import shlex
import pwd
from flask import Flask, request, jsonify, send_file
from functools import wraps
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 服务器配置
SERVER_ROOT = '/home/dst'
STEAMCMD_PATH = f'{SERVER_ROOT}/steamcmd.sh'
SERVER_PATH = f'{SERVER_ROOT}/server_dst'
CONFIG_PATH = f'{SERVER_ROOT}/.klei/DoNotStarveTogether/MyDediServer'

# 简单的身份验证
API_KEY = "123"  # 请更改为安全的API密钥

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            return response
        elif request.headers.get('X-API-Key') and request.headers.get('X-API-Key') == API_KEY:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"状态": "错误", "消息": "无效的API密钥"}), 401
    return decorated_function

def run_command(command):
    try:
        logger.info(f"执行命令: {command}")
        process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"命令输出: {process.stdout}")
        return process.stdout, None
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e.stderr}")
        return None, e.stderr

def ensure_directory(path, owner='dst'):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    os.chown(path, pwd.getpwnam(owner).pw_uid, pwd.getpwnam(owner).pw_gid)
    os.chmod(path, 0o755)

def install_dependencies():
    logger.info("正在安装依赖项...")
    commands = [
        "apt-get update",
        "apt-get install -y lib32gcc1 lib32stdc++6 libcurl4-gnutls-dev:i386 screen"
    ]
    for cmd in commands:
        output, error = run_command(cmd)
        if error:
            logger.error(f"安装依赖项时出错: {error}")
            return False
    return True

def setup_user():
    logger.info("正在设置DST用户...")
    output, error = run_command("id -u dst || useradd -m -d /home/dst dst")
    if error:
        logger.error(f"设置用户时出错: {error}")
        return False
    ensure_directory(SERVER_ROOT)
    return True

def install_steamcmd():
    logger.info("正在安装SteamCMD...")
    ensure_directory(SERVER_ROOT)
    commands = [
        f"wget -O {SERVER_ROOT}/steamcmd_linux.tar.gz https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz",
        f"tar -xvzf {SERVER_ROOT}/steamcmd_linux.tar.gz -C {SERVER_ROOT}",
        f"rm {SERVER_ROOT}/steamcmd_linux.tar.gz"
    ]
    for cmd in commands:
        output, error = run_command(cmd)
        if error:
            logger.error(f"安装SteamCMD时出错: {error}")
            return False
    ensure_directory(SERVER_PATH)
    return True

def install_dst_server():
    logger.info("正在安装DST服务器...")
    command = f"{STEAMCMD_PATH} +force_install_dir {SERVER_PATH} +login anonymous +app_update 343050 validate +quit"
    
    try:
        # 确保目标目录存在并设置正确的权限
        os.makedirs(SERVER_PATH, exist_ok=True)
        os.chown(SERVER_PATH, pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)
        
        # 设置 SteamCMD 相关文件和目录的权限
        steamcmd_files = [
            STEAMCMD_PATH,  # steamcmd.sh
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'steamcmd'),
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'steamerrorreporter'),
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'libstdc++.so.6'),
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'crashhandler.so')
        ]
        
        for file_path in steamcmd_files:
            if os.path.exists(file_path):
                os.chown(file_path, pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)
                os.chmod(file_path, 0o755)
        
        # 确保 SteamCMD 目录有正确的权限
        steamcmd_dir = os.path.dirname(STEAMCMD_PATH)
        linux32_dir = os.path.join(steamcmd_dir, 'linux32')
        
        for dir_path in [steamcmd_dir, linux32_dir]:
            if os.path.exists(dir_path):
                os.chown(dir_path, pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)
                os.chmod(dir_path, 0o755)
        
        # 使用su命令切换到dst用户运行SteamCMD
        full_command = f"su - dst -c '{command}'"
        
        process = subprocess.Popen(
            full_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                logger.info(output.strip())
        
        returncode = process.poll()
        
        _, stderr = process.communicate()
        if stderr:
            logger.error(f"安装DST服务器时有错误输出: {stderr}")
        
        if returncode != 0:
            logger.error(f"安装DST服务器失败，返回码: {returncode}")
            return False
        
        logger.info("DST服务器安装成功完成")
        return True
    
    except Exception as e:
        logger.exception(f"安装DST服务器时发生异常: {str(e)}")
        return False

def configure_server():
    logger.info("正在配置服务器...")
    ensure_directory(CONFIG_PATH)
    ensure_directory(f"{CONFIG_PATH}/Master")
    ensure_directory(f"{CONFIG_PATH}/Caves")

    config = configparser.ConfigParser()

    # cluster.ini
    config['游戏设置'] = {
        '游戏模式': 'survival',
        '最大玩家数': '10',
        '玩家对战': 'false',
        '无人暂停': 'true'
    }
    config['网络设置'] = {
        '服务器名称': '我的DST服务器',
        '服务器描述': '欢迎来到我的服务器！',
        '服务器密码': '',
        '服务器类型': 'social'
    }
    config['其他设置'] = {'控制台启用': 'true'}
    config['分片设置'] = {
        '分片启用': 'true',
        '绑定IP': '127.0.0.1',
        '主分片IP': '127.0.0.1',
        '主分片端口': '11001',
        '集群密钥': 'defaultpass'
    }

    with open(f'{CONFIG_PATH}/cluster.ini', 'w') as configfile:
        config.write(configfile)
    os.chown(f'{CONFIG_PATH}/cluster.ini', pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)

    # server.ini for Overworld
    config = configparser.ConfigParser()
    config['网络设置'] = {'服务器端口': '10999'}
    config['分片设置'] = {'是否为主分片': 'true'}
    config['STEAM'] = {
        '主服务器端口': '12346',
        '身份验证端口': '12345'
    }

    with open(f'{CONFIG_PATH}/Master/server.ini', 'w') as configfile:
        config.write(configfile)
    os.chown(f'{CONFIG_PATH}/Master/server.ini', pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)

    # server.ini for Caves
    config = configparser.ConfigParser()
    config['网络设置'] = {'服务器端口': '11000'}
    config['分片设置'] = {
        '是否为主分片': 'false',
        '分片名称': 'Caves'
    }
    config['STEAM'] = {
        '主服务器端口': '12348',
        '身份验证端口': '12347'
    }

    with open(f'{CONFIG_PATH}/Caves/server.ini', 'w') as configfile:
        config.write(configfile)
    os.chown(f'{CONFIG_PATH}/Caves/server.ini', pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)

    return True

def setup_shell_scripts():
    logger.info("正在设置Shell脚本...")
    scripts = {
        'start.sh': '''#!/bin/bash
cd /home/dst/server_dst/bin
./dontstarve_dedicated_server_nullrenderer -console -cluster MyDediServer -shard Master
''',
        'start2.sh': '''#!/bin/bash
cd /home/dst/server_dst/bin
./dontstarve_dedicated_server_nullrenderer -console -cluster MyDediServer -shard Caves
''',
        'restart.sh': '''#!/bin/bash
screen -dr dst_server1 -X -S quit
cd /home/dst/server_dst/bin
screen -dmS dst_server1 sh start.sh
''',
        'restart2.sh': '''#!/bin/bash
screen -dr dst_server2 -X -S quit
cd /home/dst/server_dst/bin
screen -dmS dst_server2 sh start2.sh
''',
        'update.sh': '''#!/bin/bash
screen -dr dst_server1 -X quit
screen -dr dst_server2 -X quit
cd /home/dst
./steamcmd.sh +login anonymous +force_install_dir /home/dst/server_dst +app_update 343050 validate +quit
sleep 10
sh /home/dst/server_dst/bin/restart.sh
sh /home/dst/server_dst/bin/restart2.sh
'''
    }
    
    for script_name, script_content in scripts.items():
        script_path = f"{SERVER_PATH}/bin/{script_name}"
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        os.chown(script_path, pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)
    
    logger.info("Shell脚本设置完成")
    return True

def start_server(shard):
    logger.info(f"正在启动{shard}服务器...")
    script_name = 'start.sh' if shard == 'overworld' else 'start2.sh'
    command = f"sh {SERVER_PATH}/bin/{script_name}"
    output, error = run_command(command)
    if error:
        logger.error(f"启动{shard}服务器时出错: {error}")
        return False
    return True

def stop_server(shard):
    logger.info(f"正在停止{shard}服务器...")
    server_name = 'dst_server1' if shard == 'overworld' else 'dst_server2'
    command = f"screen -S {server_name} -X quit"
    output, error = run_command(command)
    if error:
        logger.error(f"停止{shard}服务器时出错: {error}")
        return False
    return True

def update_server():
    logger.info("正在更新服务器...")
    stop_server('overworld')
    stop_server('caves')
    command = f"{STEAMCMD_PATH} +login anonymous +force_install_dir {SERVER_PATH} +app_update 343050 validate +quit"
    output, error = run_command(command)
    if error:
        logger.error(f"更新服务器时出错: {error}")
        return False
    start_server('overworld')
    start_server('caves')
    return True

def check_server_status(shard):
    command = "screen -list"
    output, error = run_command(command)
    if error:
        logger.error(f"检查服务器状态时出错: {error}")
        return False
    
    server_name = 'dst_server1' if shard == 'overworld' else 'dst_server2'
    return output is not None and server_name in output

@app.route('/install', methods=['POST', 'OPTIONS'])
@require_api_key
def install():
    steps = [
        ("安装依赖项", install_dependencies),
        ("设置DST用户", setup_user),
        ("安装SteamCMD", install_steamcmd),
        ("安装DST服务器", install_dst_server),
        ("配置服务器", configure_server),
        ("设置Shell脚本", setup_shell_scripts)
    ]
    
    for step_name, step_function in steps:
        logger.info(f"开始{step_name}...")
        if not step_function():
            return jsonify({"状态": "错误", "消息": f"{step_name}失败"}), 500
        logger.info(f"{step_name}完成")
    
    return jsonify({"状态": "成功", "消息": "服务器安装成功"}), 200

@app.route('/start/<shard>', methods=['POST', 'OPTIONS'])
@require_api_key
def start(shard):
    if shard not in ['overworld', 'caves']:
        return jsonify({"状态": "错误", "消息": "指定的分片无效"}), 400
    if start_server(shard):
        return jsonify({"状态": "成功", "消息": f"{shard}服务器启动成功"}), 200
    else:
        return jsonify({"状态": "错误", "消息": f"启动{shard}服务器失败"}), 500

@app.route('/stop/<shard>', methods=['POST', 'OPTIONS'])
@require_api_key
def stop(shard):
    if shard not in ['overworld', 'caves']:
        return jsonify({"状态": "错误", "消息": "指定的分片无效"}), 400
    if stop_server(shard):
        return jsonify({"状态": "成功", "消息": f"{shard}服务器停止成功"}), 200
    else:
        return jsonify({"状态": "错误", "消息": f"停止{shard}服务器失败"}), 500

@app.route('/update', methods=['POST', 'OPTIONS'])
@require_api_key
def update():
    if update_server():
        return jsonify({"状态": "成功", "消息": "服务器更新成功"}), 200
    else:
        return jsonify({"状态": "错误", "消息": "服务器更新失败"}), 500

@app.route('/config', methods=['GET', 'POST', 'OPTIONS'])
@require_api_key
def config():
    if request.method == 'OPTIONS':
        # 处理 CORS 预检请求
        response = app.make_default_options_response()
        # 设置必要的 CORS 头部
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    elif request.method == 'GET':
            try:
                cluster_config = configparser.ConfigParser()
                cluster_config.read(f'{CONFIG_PATH}/cluster.ini')
                
                # 将 ConfigParser 对象转换为可序列化的字典
                serializable_config = {
                    section: dict(cluster_config[section]) 
                    for section in cluster_config.sections()
                }
                
                return jsonify(serializable_config), 200
            except Exception as e:
                return jsonify({"状态": "错误", "消息": f"获取配置时出错: {str(e)}"}), 500

    elif request.method == 'POST':
        try:
            new_config = request.json
            if not new_config:
                return jsonify({"状态": "错误", "消息": "没有收到有效的 JSON 数据"}), 400

            cluster_config = configparser.ConfigParser()
            cluster_config.read(f'{CONFIG_PATH}/cluster.ini')

            for section, options in new_config.items():
                if section not in cluster_config:
                    cluster_config[section] = {}
                for key, value in options.items():
                    cluster_config[section][key] = str(value)

            with open(f'{CONFIG_PATH}/cluster.ini', 'w') as configfile:
                cluster_config.write(configfile)

            os.chown(f'{CONFIG_PATH}/cluster.ini', pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)

            return jsonify({"状态": "成功", "消息": "配置更新成功"}), 200
        except Exception as e:
            return jsonify({"状态": "错误", "消息": f"更新配置时出错: {str(e)}"}), 500

    # 如果请求方法既不是 GET、POST 也不是 OPTIONS
    return jsonify({"状态": "错误", "消息": "不支持的 HTTP 方法"}), 405

@app.route('/status', methods=['GET', 'OPTIONS'])
@require_api_key
def status():
    overworld_status = "运行中" if check_server_status("overworld") else "已停止"
    caves_status = "运行中" if check_server_status("caves") else "已停止"
    return jsonify({
        "地上世界": overworld_status,
        "洞穴": caves_status
    }), 200

@app.route('/logs/<shard>', methods=['GET', 'OPTIONS'])
@require_api_key
def get_logs(shard):
    if shard not in ['overworld', 'caves']:
        return jsonify({"状态": "错误", "消息": "指定的分片无效"}), 400
    
    log_file = f"{CONFIG_PATH}/{'Master' if shard == 'overworld' else 'Caves'}/server_log.txt"
    if not os.path.exists(log_file):
        return jsonify({"状态": "错误", "消息": "日志文件不存在"}), 404
    
    return send_file(log_file, as_attachment=True)

if __name__ == '__main__':
    server_host = '0.0.0.0'
    server_port = 5000
    app.run(host=server_host, port=server_port, debug=True)