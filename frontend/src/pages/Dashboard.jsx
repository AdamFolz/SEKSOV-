import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import '../styles/Dashboard.css'

export function Dashboard() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1>💉 SEKSOV</h1>
            <p>Healthcare Management System</p>
          </div>
          <div className="user-menu">
            <div className="user-info">
              <span>{user?.username}</span>
              <small>Logged in</small>
            </div>
            <button onClick={handleLogout} className="btn-logout">Logout</button>
          </div>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-label">Active Batches</div>
              <div className="stat-value">0</div>
              <div className="stat-icon">📦</div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-label">Total Injections</div>
              <div className="stat-value">0</div>
              <div className="stat-icon">💉</div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-label">Completed Batches</div>
              <div className="stat-value">0</div>
              <div className="stat-icon">✅</div>
            </div>
          </div>
          
          <div className="stat-card">
            <div className="stat-content">
              <div className="stat-label">Total Users</div>
              <div className="stat-value">1</div>
              <div className="stat-icon">👥</div>
            </div>
          </div>
        </div>

        <div className="cards-section">
          <h2>Quick Actions</h2>
          <div className="cards-grid">
            <div className="feature-card">
              <div className="card-icon">📦</div>
              <h3 className="card-title">Manage Batches</h3>
              <p className="card-description">Create and manage medication solution batches with automatic volume tracking.</p>
              <button className="btn-secondary">Manage Batches</button>
            </div>

            <div className="feature-card">
              <div className="card-icon">💉</div>
              <h3 className="card-title">Record Injection</h3>
              <p className="card-description">Record new injections and automatically track remaining batch volume.</p>
              <button className="btn-secondary">Record Injection</button>
            </div>

            <div className="feature-card">
              <div className="card-icon">📊</div>
              <h3 className="card-title">View History</h3>
              <p className="card-description">Access detailed injection history with timestamps and volume information.</p>
              <button className="btn-secondary">View History</button>
            </div>

            <div className="feature-card">
              <div className="card-icon">⚙️</div>
              <h3 className="card-title">Settings</h3>
              <p className="card-description">Configure application settings and manage your preferences.</p>
              <button className="btn-secondary">Go to Settings</button>
            </div>

            <div className="feature-card">
              <div className="card-icon">📈</div>
              <h3 className="card-title">Analytics</h3>
              <p className="card-description">View comprehensive analytics and reports on medication usage.</p>
              <button className="btn-secondary">View Analytics</button>
            </div>

            <div className="feature-card">
              <div className="card-icon">👨‍💼</div>
              <h3 className="card-title">My Profile</h3>
              <p className="card-description">Manage your account settings and personal information.</p>
              <button className="btn-secondary">Edit Profile</button>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
