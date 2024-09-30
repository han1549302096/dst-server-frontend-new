import React, { useState, useEffect } from 'react';
import { 
  Container, Typography, Box, Button, Paper, TextField, Grid, CircularProgress,
  ThemeProvider, createTheme, CssBaseline, AppBar, Toolbar, IconButton, List, ListItem, ListItemText
} from '@mui/material';
import { 
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  CloudUpload as UpdateIcon,
  Build as InstallIcon
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = 'http://192.168.150.138:5000';
const API_KEY = '123';

axios.defaults.headers.common['X-API-Key'] = API_KEY;

const theme = createTheme({
  palette: {
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#ff9800',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  const [status, setStatus] = useState({ overworld: '未知', caves: '未知' });
  const [config, setConfig] = useState({});
  const [mods, setMods] = useState({});
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [loadingConfig, setLoadingConfig] = useState(false);
  const [actionLoading, setActionLoading] = useState({});
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchStatus();
    fetchConfig();
    fetchMods();
  }, []);

  const fetchStatus = async () => {
    setLoadingStatus(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/status`);
      setStatus(response.data);
    } catch (error) {
      console.error('获取状态时出错:', error);
      setMessage('获取状态时出错: ' + error.message);
    }
    setLoadingStatus(false);
  };

  const fetchConfig = async () => {
    setLoadingConfig(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/config`);
      setConfig(response.data);
    } catch (error) {
      console.error('获取配置时出错:', error);
      setMessage('获取配置时出错: ' + error.message);
    }
    setLoadingConfig(false);
  };

  const fetchMods = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/mods`);
      setMods(response.data.mods);
    } catch (error) {
      console.error('获取MOD列表时出错:', error);
      setMessage('获取MOD列表时出错: ' + error.message);
    }
  };

  const handleAction = async (action, shard = '') => {
    setActionLoading(prevState => ({ ...prevState, [`${action}-${shard}`]: true }));
    setMessage('');
    try {
      let response;
      if (action === 'install' || action === 'update') {
        response = await axios.post(`${API_BASE_URL}/${action}`);
      } else if (action === 'start_all') {
        await axios.post(`${API_BASE_URL}/start/overworld`);
        response = await axios.post(`${API_BASE_URL}/start/caves`);
      } else if (action === 'stop_all') {
        await axios.post(`${API_BASE_URL}/stop/overworld`);
        response = await axios.post(`${API_BASE_URL}/stop/caves`);
      } else {
        response = await axios.post(`${API_BASE_URL}/${action}/${shard}`);
      }
      setMessage(response.data.message);
      fetchStatus();
    } catch (error) {
      console.error(`${action}过程中出错:`, error);
      setMessage(`${action}过程中出错: ${error.response ? error.response.data.message : error.message}`);
    }
    setActionLoading(prevState => ({ ...prevState, [`${action}-${shard}`]: false }));
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
    setLoading(true);
    setMessage('');
    try {
      await axios.post(`${API_BASE_URL}/config`, config);
      setMessage('配置保存成功');
    } catch (error) {
      console.error('保存配置时出错:', error);
      setMessage(`保存配置时出错: ${error.response ? error.response.data.message : error.message}`);
    }
    setLoading(false);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AppBar position="static" color="primary">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            饥荒联机版服务器管理器
          </Typography>
          <IconButton color="inherit" onClick={fetchStatus} disabled={loadingStatus}>
            <RefreshIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        {message && (
          <Box mb={2}>
            <Paper elevation={3}>
              <Box p={2} bgcolor={message.includes('错误') ? 'error.light' : 'success.light'}>
                <Typography variant="body1">{message}</Typography>
              </Box>
            </Paper>
          </Box>
        )}

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper elevation={3}>
              <Box p={3}>
                <Typography variant="h5" gutterBottom>服务器状态</Typography>
                {loadingStatus ? (
                  <CircularProgress />
                ) : (
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Paper elevation={1} sx={{ p: 2, bgcolor: status.地上世界 === '运行中' ? 'success.light' : 'error.light' }}>
                        <Typography variant="h6">主世界</Typography>
                        <Typography variant="body1">{status.地上世界}</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6}>
                      <Paper elevation={1} sx={{ p: 2, bgcolor: status.洞穴 === '运行中' ? 'success.light' : 'error.light' }}>
                        <Typography variant="h6">洞穴</Typography>
                        <Typography variant="body1">{status.洞穴}</Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                )}
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper elevation={3}>
              <Box p={3}>
                <Typography variant="h5" gutterBottom>服务器操作</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="primary"
                      startIcon={<InstallIcon />}
                      onClick={() => handleAction('install')}
                      disabled={actionLoading['install-']}
                    >
                      {actionLoading['install-'] ? <CircularProgress size={24} /> : '安装服务器'}
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="secondary"
                      startIcon={<UpdateIcon />}
                      onClick={() => handleAction('update')}
                      disabled={actionLoading['update-']}
                    >
                      {actionLoading['update-'] ? <CircularProgress size={24} /> : '更新服务器'}
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="success"
                      startIcon={<StartIcon />}
                      onClick={() => handleAction('start', 'overworld')}
                      disabled={actionLoading['start-overworld']}
                    >
                      {actionLoading['start-overworld'] ? <CircularProgress size={24} /> : '启动主世界'}
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="success"
                      startIcon={<StartIcon />}
                      onClick={() => handleAction('start', 'caves')}
                      disabled={actionLoading['start-caves']}
                    >
                      {actionLoading['start-caves'] ? <CircularProgress size={24} /> : '启动洞穴'}
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="error"
                      startIcon={<StopIcon />}
                      onClick={() => handleAction('stop', 'overworld')}
                      disabled={actionLoading['stop-overworld']}
                    >
                      {actionLoading['stop-overworld'] ? <CircularProgress size={24} /> : '停止主世界'}
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="error"
                      startIcon={<StopIcon />}
                      onClick={() => handleAction('stop', 'caves')}
                      disabled={actionLoading['stop-caves']}
                    >
                      {actionLoading['stop-caves'] ? <CircularProgress size={24} /> : '停止洞穴'}
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="success"
                      startIcon={<StartIcon />}
                      onClick={() => handleAction('start_all')}
                      disabled={actionLoading['start_all-']}
                    >
                      {actionLoading['start_all-'] ? <CircularProgress size={24} /> : '启动所有'}
                    </Button>
                  </Grid>
                  <Grid item xs={6}>
                    <Button
                      fullWidth
                      variant="contained"
                      color="error"
                      startIcon={<StopIcon />}
                      onClick={() => handleAction('stop_all')}
                      disabled={actionLoading['stop_all-']}
                    >
                      {actionLoading['stop_all-'] ? <CircularProgress size={24} /> : '停止所有'}
                    </Button>
                  </Grid>
                </Grid>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper elevation={3}>
              <Box p={3}>
                <Typography variant="h5" gutterBottom>MOD列表</Typography>
                <List>
                  {Object.entries(mods).map(([modId, modConfig]) => (
                    <ListItem key={modId}>
                      <ListItemText 
                        primary={modId} 
                        secondary={`启用: ${modConfig.enabled ? '是' : '否'}`} 
                      />
                    </ListItem>
                  ))}
                </List>
              </Box>
            </Paper>
          </Grid>

          <Grid item xs={12}>
            <Paper elevation={3}>
              <Box p={3}>
                <Typography variant="h5" gutterBottom>服务器配置</Typography>
                {loadingConfig ? (
                  <CircularProgress />
                ) : (
                  <>
                    {Object.entries(config).map(([section, options]) => (
                      <Box key={section} mb={2}>
                        <Typography variant="h6">{section}</Typography>
                        <Grid container spacing={2}>
                          {Object.entries(options).map(([key, value]) => (
                            <Grid item xs={12} sm={6} key={`${section}-${key}`}>
                              <TextField
                                label={key}
                                value={value}
                                onChange={(e) => handleConfigChange(section, key, e.target.value)}
                                fullWidth
                                margin="normal"
                                variant="outlined"
                              />
                            </Grid>
                          ))}
                        </Grid>
                      </Box>
                    ))}
                    <Button
                      variant="contained"
                      color="primary"
                      onClick={saveConfig}
                      disabled={loading}
                      startIcon={loading ? <CircularProgress size={24} /> : null}
                    >
                      保存配置
                    </Button>
                  </>
                )}
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

export default App;