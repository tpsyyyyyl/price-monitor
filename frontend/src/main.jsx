import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import { getToken } from './api'
import { applyStoredTheme } from './useTheme'

applyStoredTheme()
import Login from './pages/Login'
import Extract from './pages/Extract'
import Dashboard from './pages/Dashboard'
import ProductDetail from './pages/ProductDetail'

function Private({ children }) {
  return getToken() ? children : <Navigate to="/login" replace />
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Private><Extract /></Private>} />
        <Route path="/tracker" element={<Private><Dashboard /></Private>} />
        <Route path="/product/:id" element={<Private><ProductDetail /></Private>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
