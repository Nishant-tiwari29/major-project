import React from 'react';
import { GitBranch, ShieldAlert, Clock, Layers } from 'lucide-react';
import { OptimizationJob } from '../types/logistics';

interface BbTreeVisualizerProps {
  job: OptimizationJob | null;
}

export const BbTreeVisualizer: React.FC<BbTreeVisualizerProps> = ({ job }) => {
  const treeSample = job?.search_tree_sample;

  if (!treeSample) {
    return (
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-8 text-center backdrop-blur">
        <GitBranch className="w-12 h-12 text-slate-500 mx-auto mb-3" />
        <h3 className="text-lg font-semibold text-slate-200">Branch & Bound Tree Inspector Idle</h3>
        <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
          Execute an optimization run using the <strong className="text-indigo-400">Branch & Bound with Pruning</strong> solver to visualize search tree expansions and lower-bound pruning actions.
        </p>
      </div>
    );
  }

  const statCards = [
    {
      label: 'Tree Nodes Explored',
      value: treeSample.total_nodes_explored,
      icon: Layers,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    },
    {
      label: 'Pruned by Lower Bound',
      value: treeSample.pruned_by_bound,
      icon: ShieldAlert,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      label: 'Pruned by Time Window',
      value: treeSample.pruned_by_time,
      icon: Clock,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    },
    {
      label: 'Pruned by Capacity',
      value: treeSample.pruned_by_capacity,
      icon: GitBranch,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    }
  ];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'solution':
        return <span className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded text-[10px] font-semibold">OPTIMAL TOUR</span>;
      case 'pruned_bound':
        return <span className="bg-amber-500/20 text-amber-400 border border-amber-500/30 px-2 py-0.5 rounded text-[10px] font-semibold">BOUND PRUNED</span>;
      case 'pruned_time':
        return <span className="bg-rose-500/20 text-rose-400 border border-rose-500/30 px-2 py-0.5 rounded text-[10px] font-semibold">TIME PRUNED</span>;
      default:
        return <span className="bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 px-2 py-0.5 rounded text-[10px] font-semibold">BRANCH EXPLORED</span>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Pruning Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {statCards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div key={i} className={`rounded-xl border p-4 bg-slate-800/80 backdrop-blur ${c.bg}`}>
              <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
                <span>{c.label}</span>
                <Icon className={`w-4 h-4 ${c.color}`} />
              </div>
              <div className="text-2xl font-bold text-white font-mono">{c.value}</div>
            </div>
          );
        })}
      </div>

      {/* Tree Exploration Log */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur">
        <h3 className="text-sm font-semibold text-white mb-3">Branch & Bound Exploration Tree Hierarchy (Sample)</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
          {treeSample.sample_tree.map((node, i) => (
            <div
              key={i}
              className="bg-slate-900/80 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between text-xs hover:border-slate-700 transition-colors"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono text-slate-500 text-[11px]">{node.id}</span>
                <span className="text-slate-200 font-medium">{node.label}</span>
              </div>
              {getStatusBadge(node.status)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
