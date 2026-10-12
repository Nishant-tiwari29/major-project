import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { MetricCards } from './components/MetricCards';
import { MapView } from './components/MapView';
import { DpMatrixVisualizer } from './components/DpMatrixVisualizer';
import { BbTreeVisualizer } from './components/BbTreeVisualizer';
import { WhatIfSimulator } from './components/WhatIfSimulator';
import { BenchmarkChart } from './components/BenchmarkChart';
import { FleetTable } from './components/FleetTable';
import { api } from './services/api';
import { Depot, Vehicle, DeliveryRequest, OptimizationJob } from './types/logistics';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [depots, setDepots] = useState<Depot[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [orders, setOrders] = useState<DeliveryRequest[]>([]);
  const [currentJob, setCurrentJob] = useState<OptimizationJob | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [systemStatus, setSystemStatus] = useState<string>('Engine Ready');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dList, vList, oList] = await Promise.all([
          api.getDepots(),
          api.getVehicles(),
          api.getPendingOrders()
        ]);
        setDepots(dList);
        setVehicles(vList);
        setOrders(oList);

        // Run default optimization on load to populate dashboard
        handleTriggerOptimize('branch_and_bound', 'balanced');
      } catch (err) {
        console.error('Failed to load initial logistics data:', err);
        setSystemStatus('Offline / Error');
      }
    };

    fetchData();
  }, []);

  const handleTriggerOptimize = async (algorithmChoice: string, objectiveMode: string) => {
    setLoading(true);
    setSystemStatus('Optimizing Routes');
    try {
      const job = await api.optimizeRoutes({
        algorithm_choice: algorithmChoice,
        objective_mode: objectiveMode,
        include_ev_charging: true
      });
      setCurrentJob(job);
      setSystemStatus('Engine Ready');
    } catch (err) {
      console.error('Optimization run failed:', err);
      setSystemStatus('Optimization Error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col font-sans">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} systemStatus={systemStatus} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* KPI Metric Summary Cards */}
        <MetricCards job={currentJob} loading={loading} />

        {/* Tab-driven View */}
        {activeTab === 'dashboard' && (
          <MapView
            job={currentJob}
            depots={depots}
            onTriggerOptimize={handleTriggerOptimize}
            loading={loading}
          />
        )}

        {activeTab === 'dp_matrix' && (
          <DpMatrixVisualizer job={currentJob} />
        )}

        {activeTab === 'bb_tree' && (
          <BbTreeVisualizer job={currentJob} />
        )}

        {activeTab === 'simulation' && (
          <WhatIfSimulator />
        )}

        {activeTab === 'benchmark' && (
          <BenchmarkChart />
        )}

        {activeTab === 'fleet' && (
          <FleetTable depots={depots} vehicles={vehicles} orders={orders} />
        )}
      </main>

      <footer className="border-t border-slate-800 bg-slate-900/60 py-4 text-center text-xs text-slate-500">
        B.Tech Major Project &bull; Intelligent Logistics &amp; Vehicle Routing Optimizer 2.0 &bull; Built with FastAPI, C++, and React
      </footer>
    </div>
  );
};

export default App;
