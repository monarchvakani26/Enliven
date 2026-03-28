import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import LiveFeedPage from './pages/LiveFeedPage';
import DashboardPage from './pages/DashboardPage';
import TesterPage from './pages/TesterPage';
import './index.css';

const navItems = [
  { to: '/feed',      icon: '📡', label: 'Live Feed' },
  { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  { to: '/tester',    icon: '🧪', label: 'Input Tester' },
];

function Sidebar() {
  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🛡️</div>
        <div className="sidebar-logo-text">
          <strong>SafeSphere</strong>
          <span>AI Moderation</span>
        </div>
      </div>

      <div className="sidebar-nav">
        {navItems.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </div>

      <div className="sidebar-footer">
        <div className="status-dot">AI Engine Online</div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout">
        <Sidebar />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/feed" replace />} />
            <Route path="/feed" element={<LiveFeedPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/tester" element={<TesterPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
