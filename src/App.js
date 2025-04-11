// src/App.js
import React from 'react';
import ResumeUpload from './components/ResumeUpload';
import './App.css';


function App() {
  return (
    <div>
       <div className="app">
      <header className="app-header">
        <h1>👔 ResumeTwin</h1>
      </header>

      {/* The rest of your app here */}
    </div><ResumeUpload />
    </div>
  );
}

export default App;

