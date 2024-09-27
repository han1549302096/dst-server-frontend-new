import os
import subprocess
import shutil
import configparser
import time
import requests
import tarfile
from datetime import datetime

class DSTServerManager:
    def __init__(self, base_dir="/home/dst"):
        self.base_dir = base_dir
        self.steam_cmd_path = os.path.join(base_dir, "steamcmd.sh")
        self.server_dir = os.path.join(base_dir, "server_dst")
        self.config_dir = os.path.join(base_dir, ".klei", "DoNotStarveTogether")
    
    def install_dependencies(self):
        try:
            subprocess.run(["apt-get", "update"], check=True)
            subprocess.run(["apt-get", "install", "-y", "lib32gcc1", "lib32stdc++6", "libcurl4-gnutls-dev:i386"], check=True)
            print("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
    
    def create_user(self, username="dst"):
        try:
            subprocess.run(["adduser", username, "--disabled-password", "--gecos", ""], check=True)
            print(f"User '{username}' created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error creating user: {e}")
    
    def install_steamcmd(self):
        try:
            steamcmd_url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"
            response = requests.get(steamcmd_url)
            with open("steamcmd_linux.tar.gz", "wb") as f:
                f.write(response.content)
            
            with tarfile.open("steamcmd_linux.tar.gz", "r:gz") as tar:
                tar.extractall(path=self.base_dir)
            
            os.remove("steamcmd_linux.tar.gz")
            print("SteamCMD installed successfully.")
        except Exception as e:
            print(f"Error installing SteamCMD: {e}")
    
    def install_dst_server(self):
        try:
            subprocess.run([
                self.steam_cmd_path,
                "+login", "anonymous",
                "+force_install_dir", self.server_dir,
                "+app_update", "343050", "validate",
                "+quit"
            ], check=True)
            print("Don't Starve Together server installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error installing DST server: {e}")
    
    def configure_server(self, cluster_name, max_players=6, gamemode="survival", pvp=False):
        cluster_dir = os.path.join(self.config_dir, cluster_name)
        os.makedirs(cluster_dir, exist_ok=True)
        
        # Create cluster.ini
        cluster_config = configparser.ConfigParser()
        cluster_config["GAMEPLAY"] = {
            "game_mode": gamemode,
            "max_players": str(max_players),
            "pvp": str(pvp).lower()
        }
        cluster_config["NETWORK"] = {
            "cluster_name": cluster_name,
            "cluster_description": "Powered by Python",
            "cluster_password": "",
            "cluster_intention": "cooperative"
        }
        cluster_config["MISC"] = {
            "console_enabled": "true"
        }
        cluster_config["SHARD"] = {
            "shard_enabled": "true",
            "bind_ip": "127.0.0.1",
            "master_ip": "127.0.0.1",
            "master_port": "10888",
            "cluster_key": "defaultpass"
        }
        
        with open(os.path.join(cluster_dir, "cluster.ini"), "w") as f:
            cluster_config.write(f)
        
        # Create server.ini for Master and Caves
        for shard in ["Master", "Caves"]:
            shard_dir = os.path.join(cluster_dir, shard)
            os.makedirs(shard_dir, exist_ok=True)
            
            server_config = configparser.ConfigParser()
            server_config["NETWORK"] = {
                "server_port": "10999" if shard == "Master" else "11000"
            }
            server_config["SHARD"] = {
                "is_master": "true" if shard == "Master" else "false",
                "name": shard
            }
            server_config["STEAM"] = {
                "master_server_port": "27018" if shard == "Master" else "27019",
                "authentication_port": "8768" if shard == "Master" else "8769"
            }
            
            with open(os.path.join(shard_dir, "server.ini"), "w") as f:
                server_config.write(f)
        
        print(f"Server configuration for cluster '{cluster_name}' created successfully.")
    
    def start_server(self, cluster_name):
        try:
            for shard in ["Master", "Caves"]:
                screen_name = f"dst_server_{shard.lower()}"
                server_dir = os.path.join(self.server_dir, "bin")
                server_command = f"./dontstarve_dedicated_server_nullrenderer -console -cluster {cluster_name} -shard {shard}"
                
                subprocess.run(["screen", "-dmS", screen_name, "bash", "-c", f"cd {server_dir} && {server_command}"], check=True)
            
            print(f"Server cluster '{cluster_name}' started successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error starting server: {e}")
    
    def stop_server(self):
        try:
            for shard in ["master", "caves"]:
                screen_name = f"dst_server_{shard}"
                subprocess.run(["screen", "-S", screen_name, "-X", "quit"], check=True)
            
            print("Server stopped successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error stopping server: {e}")
    
    def update_server(self):
        try:
            self.stop_server()
            subprocess.run([
                self.steam_cmd_path,
                "+login", "anonymous",
                "+force_install_dir", self.server_dir,
                "+app_update", "343050", "validate",
                "+quit"
            ], check=True)
            print("Server updated successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error updating server: {e}")
    
    def create_backup(self, cluster_name):
        try:
            source_dir = os.path.join(self.config_dir, cluster_name)
            backup_dir = os.path.join(self.base_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{cluster_name}_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_name)
            
            shutil.make_archive(backup_path, "zip", source_dir)
            print(f"Backup created successfully: {backup_path}.zip")
        except Exception as e:
            print(f"Error creating backup: {e}")
    
    def restore_backup(self, backup_file, cluster_name):
        try:
            backup_path = os.path.join(self.base_dir, "backups", backup_file)
            target_dir = os.path.join(self.config_dir, cluster_name)
            
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            
            shutil.unpack_archive(backup_path, target_dir, "zip")
            print(f"Backup restored successfully to cluster '{cluster_name}'")
        except Exception as e:
            print(f"Error restoring backup: {e}")
    
    def _modify_list_file(self, file_name, item, add=True):
        file_path = os.path.join(self.config_dir, file_name)
        items = set()
        
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                items = set(line.strip() for line in f if line.strip())
        
        if add:
            items.add(item)
        else:
            items.discard(item)
        
        with open(file_path, "w") as f:
            for item in sorted(items):
                f.write(f"{item}\n")
    
    def ban_player(self, steam_id):
        self._modify_list_file("blocklist.txt", steam_id, add=True)
        print(f"Player with Steam ID {steam_id} has been banned.")
    
    def unban_player(self, steam_id):
        self._modify_list_file("blocklist.txt", steam_id, add=False)
        print(f"Player with Steam ID {steam_id} has been unbanned.")
    
    def add_admin(self, ku_id):
        self._modify_list_file("adminlist.txt", ku_id, add=True)
        print(f"Admin with KU ID {ku_id} has been added.")
    
    def remove_admin(self, ku_id):
        self._modify_list_file("adminlist.txt", ku_id, add=False)
        print(f"Admin with KU ID {ku_id} has been removed.")

def main():
    manager = DSTServerManager()
    # Use the manager to perform various operations
    # For example:
    # manager.install_dependencies()
    # manager.create_user()
    # manager.install_steamcmd()
    # manager.install_dst_server()
    # manager.configure_server("MyCluster")
    # manager.start_server("MyCluster")

if __name__ == "__main__":
    main()