import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import {
  CalendarDays,
  GitBranch,
  LogOut,
  PieChart,
  Settings,
  ShieldCheck,
  Target,
  Timer as TimerIcon,
} from 'lucide-react';
import { Login } from './pages/Login';
import { Timer } from './pages/Timer';
import { Classification } from './pages/Classification';
import { Heatmap } from './pages/Heatmap';
import { TimeTrace } from './pages/TimeTrace';
import { Targets } from './pages/Targets';
import { Review } from './pages/Review';
import { Discipline } from './pages/Discipline';
import { Admin } from './pages/Admin';
import { NotificationBell } from './components/NotificationBell';
import { apiClient } from './api/client';
import { isNetworkOnline, syncOfflineTimers } from './utils/offlineTimer';
import './App.css';

const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  if (!apiClient.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  useEffect(() => {
    const runStartupSync = () => {
      if (apiClient.isAuthenticated() && isNetworkOnline()) {
        void syncOfflineTimers(apiClient);
      }
    };

    runStartupSync();
    window.addEventListener('online', runStartupSync);

    return () => {
      window.removeEventListener('online', runStartupSync);
    };
  }, []);

  const handleLogout = () => {
    apiClient.clearAuth();
    window.location.href = '/login';
  };

  const role = apiClient.getUserRole();
  const navItems = [
    { to: '/timer', label: '计时', icon: TimerIcon },
    { to: '/classification', label: '统计', icon: PieChart },
    { to: '/time-trace', label: '时痕', icon: GitBranch },
    { to: '/heatmap', label: '热力', icon: CalendarDays },
    { to: '/targets', label: '目标', icon: Target },
    { to: '/review', label: '复盘', icon: CalendarDays },
    { to: '/discipline', label: '自律', icon: ShieldCheck },
  ];

  return (
    <div className="app-layout">
      <nav className="navbar">
        <div className="nav-brand">ETime</div>
        <div className="nav-links">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink key={item.to} to={item.to}>
                <Icon size={17} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
          {role === 'admin' && (
            <NavLink to="/admin">
              <Settings size={17} />
              <span>管理</span>
            </NavLink>
          )}
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
          path="/classification"
          element={
            <ProtectedRoute>
              <Layout>
                <Classification />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="/stats" element={<Navigate to="/classification" replace />} />
        <Route path="/summary" element={<Navigate to="/classification" replace />} />
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
          path="/time-trace"
          element={
            <ProtectedRoute>
              <Layout>
                <TimeTrace />
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
          path="/review"
          element={
            <ProtectedRoute>
              <Layout>
                <Review />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/discipline"
          element={
            <ProtectedRoute>
              <Layout>
                <Discipline />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute>
              {apiClient.isAdmin() ? (
                <Layout>
                  <Admin />
                </Layout>
              ) : (
                <Navigate to="/timer" replace />
              )}
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/timer" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
