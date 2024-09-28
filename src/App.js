// App.js
import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Button, Paper, TextField, Grid } from '@mui/material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000'; // 替换为您的API地址
const API_KEY = '123'; // 替换为您的API密钥

axios.defaults.headers.common['X-API-Key'] = API_KEY;

function App() {
  const [status, setStatus] = useState({ overworld: '未知', caves: '未知' });
  const [config, setConfig] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
    fetchConfig();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status`);
      setStatus(response.data);
    } catch (error) {
      console.error('获取状态时出错:', error);
    }
  };

  const fetchConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/config`);
      setConfig(response.data);
    } catch (error) {
      console.error('获取配置时出错:', error);
    }
  };

  const handleAction = async (action, shard = '') => {
    setLoading(true);
    try {
      let response;
      if (action === 'install' || action === 'update') {
        response = await axios.post(`${API_BASE_URL}/${action}`);
      } else {
        response = await axios.post(`${API_BASE_URL}/${action}/${shard}`);
      }
      console.log(response.data.message);
      fetchStatus();
    } catch (error) {
      console.error(`${action}过程中出错:`, error);
    }
    setLoading(false);
  };

  const handleConfigChange = (section, key, value) => {
    setConfig(prevConfig => ({
      ...prevConfig,
      [section]: {
        ...prevConfig[section],
        [key]: value
      }
    }));
  };

  const saveConfig = async () => {
    try {
      await axios.post(`${API_BASE_URL}/config`, config);
      console.log('配置保存成功');
    } catch (error) {
      console.error('保存配置时出错:', error);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h3" component="h1" gutterBottom>
        饥荒联机版服务器管理器
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={3}>
            <Box p={3}>
              <Typography variant="h5" gutterBottom>服务器状态</Typography>
              <Typography>主世界: {status.overworld}</Typography>
              <Typography>洞穴: {status.caves}</Typography>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={3}>
            <Box p={3}>
              <Typography variant="h5" gutterBottom>服务器操作</Typography>
              <Box display="flex" flexDirection="column" gap={2}>
                <Button variant="contained" color="primary" onClick={() => handleAction('install')} disabled={loading}>
                  安装服务器
                </Button>
                <Button variant="contained" color="secondary" onClick={() => handleAction('update')} disabled={loading}>
                  更新服务器
                </Button>
                <Button variant="contained" onClick={() => handleAction('start', 'overworld')} disabled={loading}>
                  启动主世界
                </Button>
                <Button variant="contained" onClick={() => handleAction('start', 'caves')} disabled={loading}>
                  启动洞穴
                </Button>
                <Button variant="contained" onClick={() => handleAction('stop', 'overworld')} disabled={loading}>
                  停止主世界
                </Button>
                <Button variant="contained" onClick={() => handleAction('stop', 'caves')} disabled={loading}>
                  停止洞穴
                </Button>
              </Box>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12}>
          <Paper elevation={3}>
            <Box p={3}>
              <Typography variant="h5" gutterBottom>服务器配置</Typography>
              {Object.entries(config).map(([section, options]) => (
                <Box key={section} mb={2}>
                  <Typography variant="h6">{section}</Typography>
                  {Object.entries(options).map(([key, value]) => (
                    <TextField
                      key={`${section}-${key}`}
                      label={key}
                      value={value}
                      onChange={(e) => handleConfigChange(section, key, e.target.value)}
                      fullWidth
                      margin="normal"
                    />
                  ))}
                </Box>
              ))}
              <Button variant="contained" color="primary" onClick={saveConfig}>
                保存配置
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;