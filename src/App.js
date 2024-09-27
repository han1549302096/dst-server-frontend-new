import React, { useState } from 'react';
import { Button, Input, Select, message } from 'antd';

const { Option } = Select;

const API_BASE_URL = 'http://localhost:5000';

const ServerInstaller = () => {
  const handleInstall = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/install`, { method: 'POST' });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('服务器安装失败');
    }
  };

  return (
    <div>
      <h2>安装服务器</h2>
      <Button onClick={handleInstall}>安装服务器</Button>
    </div>
  );
};

const ServerConfigurator = () => {
  const [clusterName, setClusterName] = useState('');
  const [maxPlayers, setMaxPlayers] = useState(6);
  const [gamemode, setGamemode] = useState('survival');
  const [pvp, setPvp] = useState(false);

  const handleConfigure = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/configure`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cluster_name: clusterName, max_players: maxPlayers, gamemode, pvp }),
      });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('服务器配置失败');
    }
  };

  return (
    <div>
      <h2>配置服务器</h2>
      <Input placeholder="集群名称" value={clusterName} onChange={(e) => setClusterName(e.target.value)} />
      <Input type="number" placeholder="最大玩家数" value={maxPlayers} onChange={(e) => setMaxPlayers(Number(e.target.value))} />
      <Select value={gamemode} onChange={setGamemode}>
        <Option value="survival">生存</Option>
        <Option value="endless">无尽</Option>
        <Option value="wilderness">荒野</Option>
      </Select>
      <Select value={pvp} onChange={setPvp}>
        <Option value={false}>PvP关闭</Option>
        <Option value={true}>PvP开启</Option>
      </Select>
      <Button onClick={handleConfigure}>配置服务器</Button>
    </div>
  );
};

const ServerController = () => {
  const [clusterName, setClusterName] = useState('');

  const handleStart = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/start/${clusterName}`, { method: 'POST' });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('服务器启动失败');
    }
  };

  const handleStop = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/stop`, { method: 'POST' });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('服务器停止失败');
    }
  };

  const handleUpdate = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/update`, { method: 'POST' });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('服务器更新失败');
    }
  };

  return (
    <div>
      <h2>控制服务器</h2>
      <Input placeholder="集群名称" value={clusterName} onChange={(e) => setClusterName(e.target.value)} />
      <Button onClick={handleStart}>启动服务器</Button>
      <Button onClick={handleStop}>停止服务器</Button>
      <Button onClick={handleUpdate}>更新服务器</Button>
    </div>
  );
};

const BackupManager = () => {
  const [clusterName, setClusterName] = useState('');
  const [backupFile, setBackupFile] = useState('');

  const handleBackup = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/backup/${clusterName}`, { method: 'POST' });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('备份创建失败');
    }
  };

  const handleRestore = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/restore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backup_file: backupFile, cluster_name: clusterName }),
      });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('备份恢复失败');
    }
  };

  return (
    <div>
      <h2>备份管理</h2>
      <Input placeholder="集群名称" value={clusterName} onChange={(e) => setClusterName(e.target.value)} />
      <Button onClick={handleBackup}>创建备份</Button>
      <Input placeholder="备份文件名" value={backupFile} onChange={(e) => setBackupFile(e.target.value)} />
      <Button onClick={handleRestore}>恢复备份</Button>
    </div>
  );
};

const PlayerManager = () => {
  const [steamId, setSteamId] = useState('');

  const handleBan = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/ban`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steam_id: steamId }),
      });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('玩家封禁失败');
    }
  };

  const handleUnban = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/unban`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ steam_id: steamId }),
      });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('玩家解封失败');
    }
  };

  return (
    <div>
      <h2>玩家管理</h2>
      <Input placeholder="Steam ID" value={steamId} onChange={(e) => setSteamId(e.target.value)} />
      <Button onClick={handleBan}>封禁玩家</Button>
      <Button onClick={handleUnban}>解封玩家</Button>
    </div>
  );
};

const AdminManager = () => {
  const [kuId, setKuId] = useState('');

  const handleAddAdmin = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ku_id: kuId }),
      });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('添加管理员失败');
    }
  };

  const handleRemoveAdmin = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ku_id: kuId }),
      });
      const data = await response.json();
      message.success(data.message);
    } catch (error) {
      message.error('移除管理员失败');
    }
  };

  return (
    <div>
      <h2>管理员管理</h2>
      <Input placeholder="KU ID" value={kuId} onChange={(e) => setKuId(e.target.value)} />
      <Button onClick={handleAddAdmin}>添加管理员</Button>
      <Button onClick={handleRemoveAdmin}>移除管理员</Button>
    </div>
  );
};

const App = () => {
  return (
    <div className="App">
      <h1>饥荒联机版服务器管理器</h1>
      <ServerInstaller />
      <ServerConfigurator />
      <ServerController />
      <BackupManager />
      <PlayerManager />
      <AdminManager />
    </div>
  );
};

export default App;