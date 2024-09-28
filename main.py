import os
import subprocess
import configparser
import logging
import time
from flask import Flask, request, jsonify, send_file
from functools import wraps

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 服务器配置
SERVER_ROOT = '/home/dst'
STEAMCMD_PATH = f'{SERVER_ROOT}/steamcmd.sh'
SERVER_PATH = f'{SERVER_ROOT}/server_dst'
CONFIG_PATH = f'{SERVER_ROOT}/.klei/DoNotStarveTogether/MyDediServer'

# 简单的身份验证
API_KEY = ""  # 请更改为安全的API密钥

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        if request.headers.get('X-API-Key') and request.headers.get('X-API-Key') == API_KEY:
            return view_function(*args, **kwargs)
        else:
            return jsonify({"status": "错误", "message": "无效的API密钥"}), 401
    return decorated_function

def run_command(command, use_sudo=False):
    try:
        if use_sudo:
            command = f"sudo {command}"
        logger.info(f"执行命令: {command}")
        process = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"命令输出: {process.stdout}")
        return process.stdout, None
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e.stderr}")
        return None, e.stderr

def ensure_directory(path, owner='dst'):
    if not os.path.exists(path):
        run_command(f"sudo mkdir -p {path}", use_sudo=True)
    run_command(f"sudo chown {owner}:{owner} {path}", use_sudo=True)
    run_command(f"sudo chmod 755 {path}", use_sudo=True)

def install_dependencies():
    logger.info("正在安装依赖项...")
    commands = [
        "apt-get update",
        "apt-get install -y lib32gcc1 lib32stdc++6 libcurl4-gnutls-dev:i386 screen"
    ]
    for cmd in commands:
        output, error = run_command(cmd, use_sudo=True)
        if error:
            logger.error(f"安装依赖项时出错: {error}")
            return False
    return True

def setup_user():
    logger.info("正在设置DST用户...")
    output, error = run_command("id -u dst || useradd -m -d /home/dst dst", use_sudo=True)
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
        output, error = run_command(f"sudo -u dst {cmd}", use_sudo=True)
        if error:
            logger.error(f"安装SteamCMD时出错: {error}")
            return False
    ensure_directory(SERVER_PATH)
    return True

def install_dst_server():
    logger.info("正在安装DST服务器...")
    command = f"sudo -u dst {STEAMCMD_PATH} +login anonymous +force_install_dir {SERVER_PATH} +app_update 343050 validate +quit"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    
    for line in process.stdout:
        if "Update state" in line or "Downloading" in line or "Validating" in line:
            logger.info(line.strip())
    
    output, error = process.communicate()
    if error:
        logger.error(f"安装DST服务器时出错: {error}")
        return False
    return True

def configure_server():
    logger.info("正在配置服务器...")
    ensure_directory(CONFIG_PATH)
    ensure_directory(f"{CONFIG_PATH}/Master")
    ensure_directory(f"{CONFIG_PATH}/Caves")

    # 创建配置文件
    config = configparser.ConfigParser()

    # cluster.ini
    config['GAMEPLAY'] = {
        'game_mode': 'survival',
        'max_players': '10',
        'pvp': 'false',
        'pause_when_empty': 'true'
    }
    config['NETWORK'] = {
        'cluster_name': '我的DST服务器',
        'cluster_description': '欢迎来到我的服务器！',
        'cluster_password': '',
        'cluster_intention': 'social'
    }
    config['MISC'] = {'console_enabled': 'true'}
    config['SHARD'] = {
        'shard_enabled': 'true',
        'bind_ip': '127.0.0.1',
        'master_ip': '127.0.0.1',
        'master_port': '11001',
        'cluster_key': 'defaultpass'
    }

    with open(f'{CONFIG_PATH}/cluster.ini', 'w') as configfile:
        config.write(configfile)
    run_command(f"sudo chown dst:dst {CONFIG_PATH}/cluster.ini", use_sudo=True)

    # server.ini for Overworld
    config = configparser.ConfigParser()
    config['NETWORK'] = {'server_port': '10999'}
    config['SHARD'] = {'is_master': 'true'}
    config['STEAM'] = {
        'master_server_port': '12346',
        'authentication_port': '12345'
    }

    with open(f'{CONFIG_PATH}/Master/server.ini', 'w') as configfile:
        config.write(configfile)
    run_command(f"sudo chown dst:dst {CONFIG_PATH}/Master/server.ini", use_sudo=True)

    # server.ini for Caves
    config = configparser.ConfigParser()
    config['NETWORK'] = {'server_port': '11000'}
    config['SHARD'] = {
        'is_master': 'false',
        'name': 'Caves'
    }
    config['STEAM'] = {
        'master_server_port': '12348',
        'authentication_port': '12347'
    }

    with open(f'{CONFIG_PATH}/Caves/server.ini', 'w') as configfile:
        config.write(configfile)
    run_command(f"sudo chown dst:dst {CONFIG_PATH}/Caves/server.ini", use_sudo=True)

    return True

def start_server(shard):
    logger.info(f"正在启动{shard}服务器...")
    script_name = 'start.sh' if shard == 'overworld' else 'start2.sh'
    command = f"sudo -u dst screen -dmS dst_server_{shard} {SERVER_PATH}/bin/{script_name}"
    output, error = run_command(command, use_sudo=True)
    if error:
        logger.error(f"启动{shard}服务器时出错: {error}")
        return False
    return True

def stop_server(shard):
    logger.info(f"正在停止{shard}服务器...")
    command = f"sudo -u dst screen -S dst_server_{shard} -X quit"
    output, error = run_command(command, use_sudo=True)
    if error:
        logger.error(f"停止{shard}服务器时出错: {error}")
        return False
    return True

def update_server():
    logger.info("正在更新服务器...")
    stop_server('overworld')
    stop_server('caves')
    command = f"sudo -u dst {STEAMCMD_PATH} +login anonymous +force_install_dir {SERVER_PATH} +app_update 343050 validate +quit"
    output, error = run_command(command, use_sudo=True)
    if error:
        logger.error(f"更新服务器时出错: {error}")
        return False
    start_server('overworld')
    start_server('caves')
    return True

def check_server_status(shard):
    command = f"sudo -u dst screen -list | grep dst_server_{shard}"
    output, error = run_command(command, use_sudo=True)
    return output is not None and "dst_server_" in output

@app.route('/install', methods=['POST'])
@require_api_key
def install():
    steps = [
        ("安装依赖项", install_dependencies),
        ("设置DST用户", setup_user),
        ("安装SteamCMD", install_steamcmd),
        ("安装DST服务器", install_dst_server),
        ("配置服务器", configure_server)
    ]
    
    for step_name, step_function in steps:
        logger.info(f"开始{step_name}...")
        if not step_function():
            return jsonify({"status": "错误", "message": f"{step_name}失败"}), 500
        logger.info(f"{step_name}完成")
    
    return jsonify({"status": "成功", "message": "服务器安装成功"}), 200

@app.route('/start/<shard>', methods=['POST'])
@require_api_key
def start(shard):
    if shard not in ['overworld', 'caves']:
        return jsonify({"status": "错误", "message": "指定的分片无效"}), 400
    if start_server(shard):
        return jsonify({"status": "成功", "message": f"{shard}服务器启动成功"}), 200
    else:
        return jsonify({"status": "错误", "message": f"启动{shard}服务器失败"}), 500

@app.route('/stop/<shard>', methods=['POST'])
@require_api_key
def stop(shard):
    if shard not in ['overworld', 'caves']:
        return jsonify({"status": "错误", "message": "指定的分片无效"}), 400
    if stop_server(shard):
        return jsonify({"status": "成功", "message": f"{shard}服务器停止成功"}), 200
    else:
        return jsonify({"status": "错误", "message": f"停止{shard}服务器失败"}), 500

@app.route('/update', methods=['POST'])
@require_api_key
def update():
    if update_server():
        return jsonify({"status": "成功", "message": "服务器更新成功"}), 200
    else:
        return jsonify({"status": "错误", "message": "服务器更新失败"}), 500

@app.route('/config', methods=['GET', 'POST'])
@require_api_key
def config():
    if request.method == 'GET':
        # 读取配置文件
        cluster_config = configparser.ConfigParser()
        cluster_config.read(f'{CONFIG_PATH}/cluster.ini')
        return jsonify(dict(cluster_config)), 200
    elif request.method == 'POST':
        # 更新配置文件
        new_config = request.json
        cluster_config = configparser.ConfigParser()
        cluster_config.read(f'{CONFIG_PATH}/cluster.ini')
        for section, options in new_config.items():
            if section not in cluster_config:
                cluster_config[section] = {}
            for key, value in options.items():
                cluster_config[section][key] = str(value)
        with open(f'{CONFIG_PATH}/cluster.ini', 'w') as configfile:
            cluster_config.write(configfile)
        run_command(f"sudo chown dst:dst {CONFIG_PATH}/cluster.ini", use_sudo=True)
        return jsonify({"status": "成功", "message": "配置更新成功"}), 200

@app.route('/status', methods=['GET'])
@require_api_key
def status():
    overworld_status = "运行中" if check_server_status("overworld") else "已停止"
    caves_status = "运行中" if check_server_status("caves") else "已停止"
    return jsonify({
        "overworld": overworld_status,
        "caves": caves_status
    }), 200

@app.route('/logs/<shard>', methods=['GET'])
@require_api_key
def get_logs(shard):
    if shard not in ['overworld', 'caves']:
        return jsonify({"status": "错误", "message": "指定的分片无效"}), 400
    
    log_file = f"{CONFIG_PATH}/{'Master' if shard == 'overworld' else 'Caves'}/server_log.txt"
    if not os.path.exists(log_file):
        return jsonify({"status": "错误", "message": "日志文件不存在"}), 404
    
    return send_file(log_file, as_attachment=True)

if __name__ == '__main__':
    server_host = '0.0.0.0'
    server_port = 5000
    app.run(host=server_host, port=server_port, debug=True)