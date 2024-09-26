import React from 'react';
import ServerStatus from './components/ServerStatus';
import ConfigEditor from './components/ConfigEditor';
import './App.css';

function App() {
  return (
    <div className="App">
      <h1>Don't Starve Together 服务器管理</h1>
      <ServerStatus />
      <ConfigEditor />
    </div>
  );
}

export default App;
