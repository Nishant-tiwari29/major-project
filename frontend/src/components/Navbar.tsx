import React from 'react';
import { Truck, Map, Cpu, GitBranch, Sliders, BarChart3, Database } from 'lucide-react';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  systemStatus: string;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, systemStatus }) => {
  const navItems = [
    { id: 'dashboard', label: 'Route Map', icon: Map },
    { id: 'dp_matrix', label: 'DP State Table', icon: Cpu },
    { id: 'bb_tree', label: 'B&B Search Tree', icon: GitBranch },
    { id: 'simulation', label: 'What-If Simulator', icon: Sliders },
    { id: 'benchmark', label: 'Algorithm Benchmarks', icon: BarChart3 },
    { id: 'fleet', label: 'Fleet & Orders', icon: Database },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">
              <Truck className="w-6 h-6" />
            </div>
            <div>
              <div className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                Logistics Optimizer <span className="text-xs bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded border border-indigo-500/30">2.0</span>
              </div>
              <div className="text-xs text-slate-400">DSA & AI-Driven Multi-Depot Vehicle Routing</div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Engine Status */}
          <div className="flex items-center space-x-2">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
            </span>
            <span className="text-xs font-medium text-emerald-400 uppercase tracking-wider">{systemStatus}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
