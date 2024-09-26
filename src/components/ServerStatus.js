import React from 'react';
import { installServer, startServer, stopServer, updateServer } from '../api';

function ServerStatus() {
  const handleInstall = async () => {
    try {
      const response = await installServer();
      alert(response.data.message);
    } catch (error) {
      alert('安装失败: ' + error.response.data.message);
    }
  };

  const handleStart = async (shard) => {
    try {
      const response = await startServer(shard);
      alert(response.data.message);
    } catch (error) {
      alert(`启动${shard}服务器失败: ` + error.response.data.message);
    }
  };

  const handleStop = async (shard) => {
    try {
      const response = await stopServer(shard);
      alert(response.data.message);
    } catch (error) {
      alert(`停止${shard}服务器失败: ` + error.response.data.message);
    }
  };

  const handleUpdate = async () => {
    try {
      const response = await updateServer();
      alert(response.data.message);
    } catch (error) {
      alert('更新失败: ' + error.response.data.message);
    }
  };

  return (
    <div className="server-status">
      <h2>服务器状态</h2>
      <button onClick={handleInstall}>安装服务器</button>
      <button onClick={() => handleStart('overworld')}>启动主世界服务器</button>
      <button onClick={() => handleStart('caves')}>启动洞穴服务器</button>
      <button onClick={() => handleStop('overworld')}>停止主世界服务器</button>
      <button onClick={() => handleStop('caves')}>停止洞穴服务器</button>
      <button onClick={handleUpdate}>更新服务器</button>
    </div>
  );
}

export default ServerStatus;

# src/components/ConfigEditor.js
import React, { useState, useEffect } from 'react';
import { getConfig, saveConfig } from '../api';

function ConfigEditor() {
  const [config, setConfig] = useState('');

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await getConfig();
      setConfig(JSON.stringify(response.data, null, 2));
    } catch (error) {
      alert('获取配置失败: ' + error.response.data.message);
    }
  };

  const handleSave = async () => {
    try {
      const configObj = JSON.parse(config);
      const response = await saveConfig(configObj);
      alert(response.data.message);
    } catch (error) {
      alert('保存配置失败: ' + error.response.data.message);
    }
  };

  return (
    <div className="config-editor">
      <h2>配置编辑器</h2>
      <textarea
        value={config}
        onChange={(e) => setConfig(e.target.value)}
        rows="10"
        cols="50"
      />
      <br />
      <button onClick={handleSave}>保存配置</button>
    </div>
  );
}

export default ConfigEditor;