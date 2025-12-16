import React from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { Login } from './pages/Login';
import { Timer } from './pages/Timer';
import { Stats } from './pages/Stats';
import { Heatmap } from './pages/Heatmap';
import { Targets } from './pages/Targets';
import { Admin } from './pages/Admin';
import { NotificationBell } from './components/NotificationBell';
import { apiClient } from './api/client';
import './App.css';

const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  if (!apiClient.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const handleLogout = () => {
    apiClient.removeToken();
    window.location.href = '/login';
  };

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="nav-brand">ETime</div>
        <div className="nav-links">
          <Link to="/timer">计时器</Link>
          <Link to="/stats">统计</Link>
          <Link to="/heatmap">热力图</Link>
          <Link to="/targets">目标</Link>
          <Link to="/admin">管理</Link>
        </div>
        <div className="nav-actions">
          <NotificationBell />
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={18} /> 退出
          </button>
        </div>
      </nav>
      <main className="main-content">{children}</main>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/timer"
          element={
            <ProtectedRoute>
              <Layout>
                <Timer />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/stats"
          element={
            <ProtectedRoute>
              <Layout>
                <Stats />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/heatmap"
          element={
            <ProtectedRoute>
              <Layout>
                <Heatmap />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/targets"
          element={
            <ProtectedRoute>
              <Layout>
                <Targets />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              <Layout>
                <Admin />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/timer" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
