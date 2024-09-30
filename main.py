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
# 配置字段映射
config_mapping = {
    'GAMEPLAY': '游戏设置',
    'game_mode': '游戏模式',
    'max_players': '最大玩家数',
    'pvp': '玩家对战',
    'pause_when_empty': '无人暂停',
    'vote_enabled': '允许投票',
    'vote_kick_enabled': '允许投票踢人',
    'NETWORK': '网络设置',
    'lan_only_cluster': '仅局域网',
    'cluster_intention': '服务器类型',
    'cluster_password': '服务器密码',
    'cluster_description': '服务器描述',
    'cluster_name': '服务器名称',
    'offline_cluster': '离线模式',
    'cluster_language': '服务器语言',
    'whitelist_slots': '预留位置',
    'tick_rate': '更新率',
    'MISC': '其他设置',
    'console_enabled': '控制台启用',
    'max_snapshots': '最大快照数',
    'SHARD': '分片设置',
    'shard_enabled': '分片启用',
    'bind_ip': '绑定IP',
    'master_ip': '主分片IP',
    'master_port': '主分片端口',
    'cluster_key': '集群密钥',
    'STEAM': 'Steam设置',
    'steam_group_only': '仅Steam组成员',
    'steam_group_id': 'Steam组ID',
    'steam_group_admins': 'Steam组管理员权限'
}

# 反向映射
reverse_mapping = {v: k for k, v in config_mapping.items()}
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

def run_command(command, use_sudo=False, user='dst'):
    try:
        if use_sudo:
            command = f"sudo {command}"
        elif user != 'root':
            command = f"sudo -u {user} {command}"
        
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
    run_command(f"chown {owner}:{owner} {path}", use_sudo=True)
    run_command(f"chmod 755 {path}", use_sudo=True)

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
        output, error = run_command(cmd, user='dst')
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
        run_command(f"mkdir -p {SERVER_PATH}", use_sudo=True)
        run_command(f"chown dst:dst {SERVER_PATH}", use_sudo=True)
        
        # 设置 SteamCMD 相关文件和目录的权限
        steamcmd_files = [
            STEAMCMD_PATH,
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'steamcmd'),
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'steamerrorreporter'),
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'libstdc++.so.6'),
            os.path.join(os.path.dirname(STEAMCMD_PATH), 'linux32', 'crashhandler.so')
        ]
        
        for file_path in steamcmd_files:
            if os.path.exists(file_path):
                run_command(f"chown dst:dst {file_path}", use_sudo=True)
                run_command(f"chmod 755 {file_path}", use_sudo=True)
        
        # 确保 SteamCMD 目录有正确的权限
        steamcmd_dir = os.path.dirname(STEAMCMD_PATH)
        linux32_dir = os.path.join(steamcmd_dir, 'linux32')
        
        for dir_path in [steamcmd_dir, linux32_dir]:
            if os.path.exists(dir_path):
                run_command(f"chown dst:dst {dir_path}", use_sudo=True)
                run_command(f"chmod 755 {dir_path}", use_sudo=True)
        
        # 使用dst用户运行SteamCMD
        output, error = run_command(command, user='dst')
        
        if error:
            logger.error(f"安装DST服务器时出错: {error}")
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
        'master_port': '10888',
        'cluster_key': 'defaultPass'
    }

    with open(f'{CONFIG_PATH}/cluster.ini', 'w') as configfile:
        config.write(configfile)
    run_command(f"chown dst:dst {CONFIG_PATH}/cluster.ini", use_sudo=True)

    # server.ini for Overworld
    config = configparser.ConfigParser()
    config['NETWORK'] = {'server_port': '10998'}
    config['SHARD'] = {'is_master': 'true'}
    config['STEAM'] = {
        'master_server_port': '27016',
        'authentication_port': '8766'
    }

    with open(f'{CONFIG_PATH}/Master/server.ini', 'w') as configfile:
        config.write(configfile)
    run_command(f"chown dst:dst {CONFIG_PATH}/Master/server.ini", use_sudo=True)

    # server.ini for Caves
    config = configparser.ConfigParser()
    config['NETWORK'] = {'server_port': '10999'}
    config['SHARD'] = {
        'is_master': 'false',
        'name': 'Caves'
    }
    config['STEAM'] = {
        'master_server_port': '27017',
        'authentication_port': '8767'
    }

    with open(f'{CONFIG_PATH}/Caves/server.ini', 'w') as configfile:
        config.write(configfile)
    run_command(f"chown dst:dst {CONFIG_PATH}/Caves/server.ini", use_sudo=True)

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
screen -S dst_server1 -X quit > /dev/null 2>&1
cd /home/dst/server_dst/bin
screen -dmS dst_server1 ./start.sh
''',
        'restart2.sh': '''#!/bin/bash
screen -S dst_server2 -X quit > /dev/null 2>&1
cd /home/dst/server_dst/bin
screen -dmS dst_server2 ./start2.sh
''',
        'update.sh': '''#!/bin/bash
screen -S dst_server1 -X quit > /dev/null 2>&1
screen -S dst_server2 -X quit > /dev/null 2>&1
cd /home/dst
./steamcmd.sh +login anonymous +force_install_dir /home/dst/server_dst +app_update 343050 validate +quit
sleep 10
bash /home/dst/server_dst/bin/restart.sh
bash /home/dst/server_dst/bin/restart2.sh
''',
        'start_all.sh': '''#!/bin/bash
bash /home/dst/server_dst/bin/restart.sh
bash /home/dst/server_dst/bin/restart2.sh
''',
        'stop_all.sh': '''#!/bin/bash
screen -S dst_server1 -X quit > /dev/null 2>&1
screen -S dst_server2 -X quit > /dev/null 2>&1
'''
    }
        
    for script_name, script_content in scripts.items():
        script_path = f"{SERVER_PATH}/bin/{script_name}"
        with open(script_path, 'w') as f:
            f.write(script_content)
        run_command(f"chmod 755 {script_path}", use_sudo=True)
        run_command(f"chown dst:dst {script_path}", use_sudo=True)
    
    logger.info("Shell脚本设置完成")
    return True




def parse_lua_table(content):
    def parse_value(value):
        value = value.strip()
        if value == "true":
            return True
        elif value == "false":
            return False
        elif value.isdigit():
            return int(value)
        elif value.replace(".", "").isdigit():
            return float(value)
        else:
            return value.strip('"')

    result = {}
    current_table = result
    table_stack = []
    current_key = None

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('[') and line.endswith('] = {'):
            key = line[1:-4].strip('[]" ')
            current_table[key] = {}
            table_stack.append((current_table, current_key))
            current_table = current_table[key]
            current_key = None
        elif line == '},':
            if table_stack:
                current_table, current_key = table_stack.pop()
        elif '=' in line:
            key, value = line.split('=', 1)
            key = key.strip('[] "')
            value = value.strip('," ')
            if value == '{':
                current_table[key] = {}
                table_stack.append((current_table, current_key))
                current_table = current_table[key]
                current_key = key
            else:
                current_table[key] = parse_value(value)

    return result

def read_modoverrides():
    modoverrides_path = f"{CONFIG_PATH}/Master/modoverrides.lua"
    if not os.path.exists(modoverrides_path):
        return {}
    
    with open(modoverrides_path, 'r') as f:
        content = f.read()
    
    # 移除 'return' 并解析Lua表
    content = content.replace('return', '').strip()
    return parse_lua_table(content)

def write_modoverrides(mods):
    def lua_repr(value):
        if isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return f'"{value}"'
        else:
            return str(value)

    def format_table(table, indent=0):
        lines = []
        for key, value in table.items():
            if isinstance(value, dict):
                lines.append(f'{"  " * indent}["{key}"] = {{')
                lines.extend(format_table(value, indent + 1))
                lines.append(f'{"  " * indent}}},')
            else:
                lines.append(f'{"  " * indent}{key} = {lua_repr(value)},')
        return lines

    modoverrides_path = f"{CONFIG_PATH}/Master/modoverrides.lua"
    
    with open(modoverrides_path, 'w') as f:
        f.write("return {\n")
        f.write('\n'.join(format_table(mods, 1)))
        f.write("}\n")

def update_mod_configuration():
    mods = read_modoverrides()
    mod_setup_path = f"{SERVER_PATH}/mods/dedicated_server_mods_setup.lua"
    
    try:
        with open(mod_setup_path, 'w') as f:
            f.write("-- 这个文件由服务器自动生成，请勿手动修改\n\n")
            for mod_id in mods.keys():
                # 提取 workshop ID
                workshop_id = mod_id.split('-')[-1]
                f.write(f'ServerModSetup("{workshop_id}")\n')
        
        logger.info("MOD配置已更新")
    except Exception as e:
        logger.error(f"更新MOD配置时出错: {str(e)}")
        raise

# 修改start_server函数
def start_server(shard):
    logger.info(f"正在启动{shard}服务器...")
    
    update_mod_configuration()
    
    script_name = 'restart.sh' if shard == 'overworld' else 'restart2.sh'
    command = f"sh {SERVER_PATH}/bin/{script_name}"
    output, error = run_command(command, user='dst')
    if error:
        logger.error(f"启动{shard}服务器时出错: {error}")
        return False
    return True

def stop_server(shard):
    logger.info(f"正在停止{shard}服务器...")
    server_name = 'dst_server1' if shard == 'overworld' else 'dst_server2'
    command = f"screen -S {server_name} -X quit"
    output, error = run_command(command, user='dst')
    if error:
        logger.error(f"停止{shard}服务器时出错: {error}")
        return False
    return True

def start_all_server():
    logger.info("正在启动所有服务器...")
    
    # 更新MOD配置
    update_mod_configuration()
    
    command = f"sh {SERVER_PATH}/bin/start_all.sh"
    output, error = run_command(command, user='dst')
    if error:
        logger.error(f"启动所有服务器时出错: {error}")
        return False
    return True

def stop_all_server():
    logger.info(f"正在停止所有服务器...")
    command = f"sh {SERVER_PATH}/bin/stop_all.sh"
    output, error = run_command(command, user='dst')
    if error:
        logger.error(f"停止所有服务器时出错: {error}")
        return False
    return True

def update_server():
    logger.info("正在更新服务器...")
    stop_server('overworld')
    stop_server('caves')
    command = f"{STEAMCMD_PATH} +login anonymous +force_install_dir {SERVER_PATH} +app_update 343050 validate +quit"
    output, error = run_command(command, user='dst')
    if error:
        logger.error(f"更新服务器时出错: {error}")
        return False
    start_server('overworld')
    start_server('caves')
    return True

def check_server_status(shard):
    command = "screen -list"
    output, error = run_command(command, user='dst')
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
        ## ("配置服务器", configure_server),
        ("设置Shell脚本", setup_shell_scripts)
    ]
    
    for step_name, step_function in steps:
        logger.info(f"开始{step_name}...")
        if not step_function():
            return jsonify({"状态": "错误", "消息": f"{step_name}失败"}), 500
        logger.info(f"{step_name}完成")
    
    return jsonify({"状态": "成功", "消息": "服务器安装成功"}), 200


@app.route('/mods', methods=['GET', 'POST', 'OPTIONS'])
@require_api_key
def manage_mods():
    if request.method == 'GET':
        mods = read_modoverrides()
        return jsonify({"mods": mods}), 200
    
    elif request.method == 'POST':
        new_mods = request.json.get('mods', {})
        write_modoverrides(new_mods)
        return jsonify({"状态": "成功", "消息": "MOD配置已更新"}), 200
    

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
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Methods'] = 'GET,POST'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    elif request.method == 'GET':
        try:
            cluster_config = configparser.ConfigParser()
            cluster_config.read(f'{CONFIG_PATH}/cluster.ini')
            
            # 将配置转换为中文标签
            translated_config = {}
            for section in cluster_config.sections():
                translated_section = config_mapping.get(section, section)
                translated_config[translated_section] = {}
                for key, value in cluster_config[section].items():
                    translated_key = config_mapping.get(key, key)
                    translated_config[translated_section][translated_key] = value
            
            return jsonify(translated_config), 200
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
                original_section = reverse_mapping.get(section, section)
                if original_section not in cluster_config:
                    cluster_config[original_section] = {}
                for key, value in options.items():
                    original_key = reverse_mapping.get(key, key)
                    cluster_config[original_section][original_key] = str(value)

            with open(f'{CONFIG_PATH}/cluster.ini', 'w') as configfile:
                cluster_config.write(configfile)

            os.chown(f'{CONFIG_PATH}/cluster.ini', pwd.getpwnam('dst').pw_uid, pwd.getpwnam('dst').pw_gid)

            return jsonify({"状态": "成功", "消息": "配置更新成功"}), 200
        except Exception as e:
            return jsonify({"状态": "错误", "消息": f"更新配置时出错: {str(e)}"}), 500

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