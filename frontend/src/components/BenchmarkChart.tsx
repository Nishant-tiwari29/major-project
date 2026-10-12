import React, { useState } from 'react';
import { BarChart3, Zap, ShieldCheck, Play, Award } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { BenchmarkResponse } from '../types/logistics';
import { api } from '../services/api';

export const BenchmarkChart: React.FC = () => {
  const [instanceSize, setInstanceSize] = useState<number>(6);
  const [loading, setLoading] = useState<boolean>(false);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);

  const handleRunBenchmark = async () => {
    setLoading(true);
    try {
      const res = await api.runBenchmark(instanceSize);
      setBenchmarkData(res);
    } catch (err) {
      console.error("Benchmark failed:", err);
    } finally {
      setLoading(false);
    }
  };

  const runtimeChartData = benchmarkData ? benchmarkData.results.map(r => ({
    name: r.algorithm_name.split(' ')[0],
    fullName: r.algorithm_name,
    runtime_ms: r.execution_time_ms,
    gap: r.optimality_gap_percent
  })) : [];

  return (
    <div className="space-y-5">
      {/* Control Panel */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur flex flex-wrap items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            Empirical Algorithm Benchmarking Suite
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Executes Exact (Held-Karp DP, Branch &amp; Bound) vs. Heuristics on strictly identical network instances.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400">Problem Size (Nodes):</label>
          <select
            value={instanceSize}
            onChange={(e) => setInstanceSize(parseInt(e.target.value))}
            className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200"
          >
            <option value={4}>4 Nodes (Instant Verification)</option>
            <option value={6}>6 Nodes (Standard CVRP)</option>
            <option value={8}>8 Nodes (Intermediate)</option>
            <option value={10}>10 Nodes (Held-Karp Stress Test)</option>
          </select>

          <button
            onClick={handleRunBenchmark}
            disabled={loading}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-xs transition-all shadow-md shadow-indigo-600/30 flex items-center gap-1.5"
          >
            {loading ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Benchmarking...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run Head-to-Head Benchmark</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Benchmark Visualizations & Table */}
      {benchmarkData && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Runtime Chart */}
            <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur h-[280px]">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Execution Runtime (ms)</h4>
              <ResponsiveContainer width="100%" height="90%">
                <BarChart data={runtimeChartData}>
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="runtime_ms" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Optimality Gap Chart */}
            <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur h-[280px]">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Optimality Gap vs Ground Truth (%)</h4>
              <ResponsiveContainer width="100%" height="90%">
                <BarChart data={runtimeChartData}>
                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                  <YAxis stroke="#94a3b8" fontSize={11} unit="%" />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', fontSize: '12px' }} />
                  <Bar dataKey="gap" radius={[4, 4, 0, 0]}>
                    {runtimeChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.gap === 0 ? '#10b981' : '#f59e0b'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Full Metrics Comparison Table */}
          <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur overflow-x-auto shadow-lg">
            <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
              <Award className="w-4 h-4 text-emerald-400" />
              Comparative Performance Matrix (Instance Size N = {benchmarkData.instance_size})
            </h4>

            <table className="w-full text-left text-xs font-sans">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400 uppercase tracking-wider text-[11px]">
                  <th className="py-2.5 px-3">Algorithm</th>
                  <th className="py-2.5 px-3">Execution Time</th>
                  <th className="py-2.5 px-3">States Explored</th>
                  <th className="py-2.5 px-3">Memory (KB)</th>
                  <th className="py-2.5 px-3">Tour Cost</th>
                  <th className="py-2.5 px-3">Optimality Gap</th>
                  <th className="py-2.5 px-3">Guarantee</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-200 font-mono text-[11px]">
                {benchmarkData.results.map((r, i) => (
                  <tr key={i} className="hover:bg-slate-700/20 transition-colors">
                    <td className="py-2.5 px-3 font-sans font-semibold text-slate-200">{r.algorithm_name}</td>
                    <td className="py-2.5 px-3 text-sky-400">{r.execution_time_ms.toFixed(2)} ms</td>
                    <td className="py-2.5 px-3 text-slate-300">{r.states_explored.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-400">{r.memory_usage_kb.toFixed(1)} KB</td>
                    <td className="py-2.5 px-3 font-semibold text-white">{r.solution_cost.toFixed(2)} km</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${r.optimality_gap_percent === 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'}`}>
                        {r.optimality_gap_percent === 0 ? '0.0% (OPTIMAL)' : `+${r.optimality_gap_percent.toFixed(1)}% GAP`}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      {r.is_optimal_guaranteed ? (
                        <span className="flex items-center gap-1 text-emerald-400 text-[10px] font-semibold">
                          <ShieldCheck className="w-3.5 h-3.5" /> Proven Exact
                        </span>
                      ) : (
                        <span className="text-slate-500 text-[10px]">Heuristic Bound</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
