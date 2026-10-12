import React, { useState } from 'react';
import { Sliders, TrendingUp, AlertTriangle, Play, CheckCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { ScenarioSimulationResponse } from '../types/logistics';
import { api } from '../services/api';

export const WhatIfSimulator: React.FC = () => {
  const [fuelMultiplier, setFuelMultiplier] = useState<number>(1.2);
  const [trafficMultiplier, setTrafficMultiplier] = useState<number>(1.4);
  const [roadClosure, setRoadClosure] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);
  const [simData, setSimData] = useState<ScenarioSimulationResponse | null>(null);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await api.runSimulation({
        fuel_price_multiplier: fuelMultiplier,
        traffic_multiplier: trafficMultiplier,
        road_closures: roadClosure ? [[0, 5]] : []
      });
      setSimData(res);
    } catch (err) {
      console.error("Simulation failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const chartData = simData ? [
    {
      metric: 'Distance (km)',
      Baseline: simData.baseline_plan.total_distance_km,
      Simulated: simData.simulated_plan.total_distance_km
    },
    {
      metric: 'Duration (min)',
      Baseline: simData.baseline_plan.total_duration_min,
      Simulated: simData.simulated_plan.total_duration_min
    },
    {
      metric: 'Cost ($)',
      Baseline: simData.baseline_plan.total_cost,
      Simulated: simData.simulated_plan.total_cost
    },
    {
      metric: 'CO2 (kg)',
      Baseline: simData.baseline_plan.total_co2_kg,
      Simulated: simData.simulated_plan.total_co2_kg
    }
  ] : [];

  return (
    <div className="space-y-5">
      {/* Parameter Modulation Panel */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-semibold text-white">Scenario Perturbation Controls</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Fuel Price Slider */}
          <div>
            <div className="flex justify-between text-xs font-medium text-slate-300 mb-2">
              <span>Fuel Price Multiplier</span>
              <span className="text-indigo-400 font-bold">{fuelMultiplier.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.8"
              max="2.0"
              step="0.05"
              value={fuelMultiplier}
              onChange={(e) => setFuelMultiplier(parseFloat(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>-20% Subsidized</span>
              <span>Baseline (1.0x)</span>
              <span>+100% Crisis Surge</span>
            </div>
          </div>

          {/* Traffic Congestion Slider */}
          <div>
            <div className="flex justify-between text-xs font-medium text-slate-300 mb-2">
              <span>Traffic Congestion Surge</span>
              <span className="text-amber-400 font-bold">{trafficMultiplier.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="1.0"
              max="2.5"
              step="0.1"
              value={trafficMultiplier}
              onChange={(e) => setTrafficMultiplier(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>Normal Flow (1.0x)</span>
              <span>Moderate Rush</span>
              <span>Severe Gridlock (2.5x)</span>
            </div>
          </div>

          {/* Road Closures Toggle */}
          <div className="flex flex-col justify-center">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                checked={roadClosure}
                onChange={(e) => setRoadClosure(e.target.checked)}
                className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700 focus:ring-indigo-500"
              />
              <span className="text-sm font-medium text-slate-300">Simulate Arterial Road Closure (Depot 0 &harr; Connaught C1)</span>
            </label>
            <span className="text-[11px] text-slate-500 mt-1 ml-7">Forces optimization engine to compute non-trivial bypass detours</span>
          </div>
        </div>

        <div className="mt-5 pt-4 border-t border-slate-700/60 flex justify-end">
          <button
            onClick={handleSimulate}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-all shadow-md shadow-indigo-600/30 flex items-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Executing Simulation...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Run Scenario Simulation</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Simulation Results Comparison */}
      {simData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Side-by-Side Delta Metrics */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur shadow-lg">
            <h3 className="text-base font-semibold text-white mb-4 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Operational Impact &amp; &Delta; Deltas
            </h3>

            <div className="space-y-3">
              {[
                { label: 'Operating Cost', base: `$${simData.baseline_plan.total_cost.toFixed(2)}`, sim: `$${simData.simulated_plan.total_cost.toFixed(2)}`, delta: `+$${simData.delta.delta_cost}`, pct: `+${simData.delta.delta_cost_percent}%` },
                { label: 'Travel Duration', base: `${Math.round(simData.baseline_plan.total_duration_min)} min`, sim: `${Math.round(simData.simulated_plan.total_duration_min)} min`, delta: `+${simData.delta.delta_duration_min} min`, pct: `+${simData.delta.delta_duration_percent}%` },
                { label: 'Total Distance', base: `${simData.baseline_plan.total_distance_km.toFixed(1)} km`, sim: `${simData.simulated_plan.total_distance_km.toFixed(1)} km`, delta: `+${simData.delta.delta_distance_km} km`, pct: `+${simData.delta.delta_distance_percent}%` },
                { label: 'CO2 Emissions', base: `${simData.baseline_plan.total_co2_kg.toFixed(1)} kg`, sim: `${simData.simulated_plan.total_co2_kg.toFixed(1)} kg`, delta: `+${simData.delta.delta_co2_kg} kg`, pct: `+${simData.delta.delta_co2_percent}%` },
              ].map((item, idx) => (
                <div key={idx} className="bg-slate-900/60 border border-slate-800 rounded-lg p-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-400 font-medium block">{item.label}</span>
                    <span className="text-slate-300 font-mono text-[11px]">{item.base} &rarr; <strong className="text-white">{item.sim}</strong></span>
                  </div>
                  <div className="text-right">
                    <span className="text-rose-400 font-bold block">{item.delta}</span>
                    <span className="text-rose-400/80 font-mono text-[10px]">({item.pct})</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Comparative Chart */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur shadow-lg h-[320px]">
            <h3 className="text-sm font-semibold text-white mb-2">Baseline vs. Perturbed Scenario Comparison</h3>
            <ResponsiveContainer width="100%" height="90%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <XAxis dataKey="metric" stroke="#94a3b8" fontSize={11} />
                <YAxis stroke="#94a3b8" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="Baseline" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Simulated" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};
