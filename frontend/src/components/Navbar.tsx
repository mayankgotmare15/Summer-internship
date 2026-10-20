import React from 'react';
import type { UserProfile } from '../types';

interface NavbarProps {
  currentUser: UserProfile;
  onSelectRole: (role: string) => void;
  activeTab: 'intake' | 'triage' | 'health';
  setActiveTab: (tab: 'intake' | 'triage' | 'health') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  onSelectRole,
  activeTab,
  setActiveTab,
}) => {
  return (
    <header className="bg-nero text-san border-b border-nero-700 sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('intake')}>
          <div className="w-9 h-9 rounded-lg bg-orange flex items-center justify-center font-bold text-nero shadow-sm">
            <span className="text-xl leading-none">▮▮</span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight text-white font-sans">RouteDesk</span>
              <span className="text-[10px] uppercase font-mono tracking-wider bg-orange/20 text-orange border border-orange/40 px-1.5 py-0.5 rounded">
                MLOps v1.1
              </span>
            </div>
            <p className="text-xs text-muted-dark font-sans hidden sm:block">
              IT Ticket Auto-Routing & Priority Engine
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 sm:space-x-2">
          <button
            type="button"
            onClick={() => setActiveTab('intake')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'intake'
                ? 'bg-orange text-nero font-semibold'
                : 'text-san hover:bg-nero-800'
            }`}
          >
            Ticket Intake
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('triage')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center space-x-1.5 ${
              activeTab === 'triage'
                ? 'bg-orange text-nero font-semibold'
                : 'text-san hover:bg-nero-800'
            }`}
          >
            <span>Review Queue</span>
            <span className="bg-orange/20 text-orange text-[10px] px-1.5 py-0.2 rounded-full font-bold">
              3
            </span>
          </button>
        </nav>

        {/* Role Switcher & Persona */}
        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center space-x-2 text-xs text-muted-dark bg-nero-800 px-3 py-1.5 rounded-full border border-nero-700">
            <span className="w-2 h-2 rounded-full bg-status-success animate-pulse"></span>
            <span>Champion: <strong className="text-san">v1-baseline (τ=0.69)</strong></span>
          </div>

          <div className="relative">
            <select
              aria-label="Active Demo Persona"
              value={currentUser.role}
              onChange={(e) => onSelectRole(e.target.value)}
              className="bg-nero-800 text-san border border-nero-700 text-xs sm:text-sm rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-orange cursor-pointer"
            >
              <option value="requester">👤 Requester (Aarav)</option>
              <option value="agent">🛡️ Triage Agent (Karan)</option>
              <option value="engineer">🔧 Resolver (Priya)</option>
              <option value="team_lead">👥 Team Lead (Riya)</option>
              <option value="manager">📊 Manager (Rahul)</option>
              <option value="admin">⚡ Admin (Siddharth)</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};
