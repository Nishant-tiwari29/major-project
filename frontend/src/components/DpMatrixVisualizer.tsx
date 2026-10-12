import React from 'react';
import { Cpu, Binary, Info } from 'lucide-react';
import { OptimizationJob } from '../types/logistics';

interface DpMatrixVisualizerProps {
  job: OptimizationJob | null;
}

export const DpMatrixVisualizer: React.FC<DpMatrixVisualizerProps> = ({ job }) => {
  const dpSample = job?.dp_matrix_sample;

  if (!dpSample) {
    return (
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-8 text-center backdrop-blur">
        <Cpu className="w-12 h-12 text-slate-500 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-200">DP State Inspector Idle</h3>
        <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
          Execute an optimization run with the <strong className="text-indigo-400">Held-Karp Bitmask DP</strong> solver to inspect live dynamic programming states, transition costs, and subset bitmasks.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Mathematical Theory Card */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
            <Binary className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white">Held-Karp Bitmask Dynamic Programming Recurrence</h3>
            <div className="mt-2 font-mono text-xs bg-slate-900 border border-slate-800 rounded-lg p-3 text-indigo-300">
              dp(S, u) = min &#123; dp(S \ &#123;u&#125;, v) + cost(v, u) &#125; for all v &isin; S \ &#123;u&#125;
            </div>
            <div className="mt-2 text-xs text-slate-400 flex flex-wrap gap-4">
              <span>Time Complexity: <strong className="text-slate-200">&Theta;(n&sup2; &middot; 2&#x207F;)</strong></span>
              <span>Space Complexity: <strong className="text-slate-200">&Theta;(n &middot; 2&#x207F;)</strong></span>
              <span>Total State Subsets: <strong className="text-slate-200">{dpSample.total_subsets}</strong></span>
              <span>Customer Nodes: <strong className="text-slate-200">{dpSample.num_customers}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* DP State Table Explorer */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur">
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm font-semibold text-white">Sample Evaluated Memoization States (First 16 Subsets)</div>
          <div className="text-xs text-slate-400 flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5" />
            <span>Values indicate optimal path cost visiting bitmask subset ending at customer column</span>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400 uppercase tracking-wider">
                <th className="py-2.5 px-3">Mask (Dec)</th>
                <th className="py-2.5 px-3">Bitmask (Binary)</th>
                {[...Array(dpSample.num_customers)].map((_, i) => (
                  <th key={i} className="py-2.5 px-3">End Customer #{i + 1}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {dpSample.sample_states.map((row) => (
                <tr key={row.mask} className="hover:bg-slate-700/30 transition-colors">
                  <td className="py-2 px-3 font-semibold text-indigo-400">{row.mask}</td>
                  <td className="py-2 px-3">
                    <span className="bg-slate-900 px-2 py-0.5 rounded border border-slate-700/60 text-slate-300">
                      {row.binary}
                    </span>
                  </td>
                  {row.values.map((val, colIdx) => (
                    <td key={colIdx} className="py-2 px-3">
                      {val !== null ? (
                        <span className="text-emerald-400 font-semibold">{val.toFixed(1)} km</span>
                      ) : (
                        <span className="text-slate-600">&infin;</span>
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
