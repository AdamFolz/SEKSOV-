import { useState, useEffect } from 'react'
import './App.css'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [apiStatus, setApiStatus] = useState('Loading...')
  const [batches, setBatches] = useState([])

  useEffect(() => {
    // Check API health
    axios.get(`${API_URL}/api/health`)
      .then(res => setApiStatus('✅ API Connected'))
      .catch(err => setApiStatus('❌ API Error: ' + err.message))
  }, [])

  return (
    <div className="App">
      <header>
        <h1>💉 SEKSOV - Medication Tracking</h1>
        <p>Web Application</p>
      </header>

      <main>
        <div className="card">
          <h2>Status</h2>
          <p>{apiStatus}</p>
        </div>

        <div className="card">
          <h2>Features Coming Soon</h2>
          <ul>
            <li>👤 User Management</li>
            <li>📦 Batch Management</li>
            <li>💉 Injection Recording</li>
            <li>📊 History & Reports</li>
            <li>📱 Responsive Design</li>
          </ul>
        </div>

        <div className="card">
          <h2>Quick Start</h2>
          <pre>
# Install backend dependencies
cd backend
pip install -r requirements.txt
cp .env.example .env

# Install frontend dependencies
cd ../frontend
npm install
npm run dev
          </pre>
        </div>
      </main>
    </div>
  )
}

export default App
