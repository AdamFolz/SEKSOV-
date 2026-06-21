import { useAuth } from '../context/AuthContext'
import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import '../styles/Auth.css'

export function Register() {
  const { register, loading, error } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [localError, setLocalError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLocalError('')
    setSuccess('')
    
    if (!username || !email || !password || !confirmPassword) {
      setLocalError('Please fill all fields')
      return
    }
    
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match')
      return
    }
    
    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters')
      return
    }

    try {
      await register(username, email, password)
      setSuccess('Account created! Redirecting to login...')
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setLocalError(err.message)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-box">
        <div className="auth-header">
          <span className="auth-icon">💉</span>
          <h1>SEKSOV</h1>
          <p>Create Your Account</p>
        </div>
        
        {(error || localError) && (
          <div className="error-message">{error || localError}</div>
        )}
        
        {success && (
          <div className="success-message">{success}</div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Choose a username"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Min 6 characters"
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              disabled={loading}
            />
          </div>
          
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>
        
        <p className="auth-link">
          Already have an account? <a href="/login">Sign in</a>
        </p>
      </div>
    </div>
  )
}
