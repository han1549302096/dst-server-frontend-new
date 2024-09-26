import axios from 'axios';

const API_URL = 'http://your_server_ip:5000';

export const installServer = () => axios.post(`${API_URL}/install`);
export const startServer = (shard) => axios.post(`${API_URL}/start/${shard}`);
export const stopServer = (shard) => axios.post(`${API_URL}/stop/${shard}`);
export const updateServer = () => axios.post(`${API_URL}/update`);
export const getConfig = () => axios.get(`${API_URL}/config`);
export const saveConfig = (config) => axios.post(`${API_URL}/config`, config);
