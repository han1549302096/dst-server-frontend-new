from flask import Flask, request, jsonify
from dst_server_manager import DSTServerManager
import os

app = Flask(__name__)
manager = DSTServerManager()

@app.route('/install', methods=['POST'])
def install():
    try:
        manager.install_dependencies()
        manager.create_user()
        manager.install_steamcmd()
        manager.install_dst_server()
        return jsonify({"message": "Server installed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/configure', methods=['POST'])
def configure():
    data = request.json
    cluster_name = data.get('cluster_name', 'MyCluster')
    max_players = data.get('max_players', 6)
    gamemode = data.get('gamemode', 'survival')
    pvp = data.get('pvp', False)

    try:
        manager.configure_server(cluster_name, max_players, gamemode, pvp)
        return jsonify({"message": f"Server {cluster_name} configured successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/start/<cluster_name>', methods=['POST'])
def start(cluster_name):
    try:
        manager.start_server(cluster_name)
        return jsonify({"message": f"Server {cluster_name} started successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop():
    try:
        manager.stop_server()
        return jsonify({"message": "Server stopped successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update', methods=['POST'])
def update():
    try:
        manager.update_server()
        return jsonify({"message": "Server updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/backup/<cluster_name>', methods=['POST'])
def backup(cluster_name):
    try:
        manager.create_backup(cluster_name)
        return jsonify({"message": f"Backup for {cluster_name} created successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/restore', methods=['POST'])
def restore():
    data = request.json
    backup_file = data.get('backup_file')
    cluster_name = data.get('cluster_name')

    if not backup_file or not cluster_name:
        return jsonify({"error": "Missing backup_file or cluster_name"}), 400

    try:
        manager.restore_backup(backup_file, cluster_name)
        return jsonify({"message": f"Backup restored to {cluster_name} successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ban', methods=['POST'])
def ban():
    data = request.json
    steam_id = data.get('steam_id')

    if not steam_id:
        return jsonify({"error": "Missing steam_id"}), 400

    try:
        manager.ban_player(steam_id)
        return jsonify({"message": f"Player with Steam ID {steam_id} banned successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/unban', methods=['POST'])
def unban():
    data = request.json
    steam_id = data.get('steam_id')

    if not steam_id:
        return jsonify({"error": "Missing steam_id"}), 400

    try:
        manager.unban_player(steam_id)
        return jsonify({"message": f"Player with Steam ID {steam_id} unbanned successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin', methods=['POST'])
def add_admin():
    data = request.json
    ku_id = data.get('ku_id')

    if not ku_id:
        return jsonify({"error": "Missing ku_id"}), 400

    try:
        manager.add_admin(ku_id)
        return jsonify({"message": f"Admin with KU ID {ku_id} added successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin', methods=['DELETE'])
def remove_admin():
    data = request.json
    ku_id = data.get('ku_id')

    if not ku_id:
        return jsonify({"error": "Missing ku_id"}), 400

    try:
        manager.remove_admin(ku_id)
        return jsonify({"message": f"Admin with KU ID {ku_id} removed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))