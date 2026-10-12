import React from 'react';
import { Route, Clock, DollarSign, Leaf, AlertTriangle, ShieldCheck } from 'lucide-react';
import { OptimizationJob } from '../types/logistics';

interface MetricCardsProps {
  job: OptimizationJob | null;
  loading: boolean;
}

export const MetricCards: React.FC<MetricCardsProps> = ({ job, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 animate-pulse">
            <div className="h-4 bg-slate-700 rounded w-1/2 mb-3"></div>
            <div className="h-7 bg-slate-600 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: 'Total Distance',
      value: job ? `${job.total_distance_km.toFixed(1)} km` : '0.0 km',
      icon: Route,
      color: 'text-indigo-400',
      bg: 'bg-indigo-500/10 border-indigo-500/20'
    },
    {
      label: 'Estimated Cost',
      value: job ? `$${job.total_cost.toFixed(2)}` : '$0.00',
      icon: DollarSign,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500/10 border-emerald-500/20'
    },
    {
      label: 'Total Duration',
      value: job ? `${Math.round(job.total_duration_min)} min` : '0 min',
      icon: Clock,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      label: 'CO2 Emissions',
      value: job ? `${job.total_co2_kg.toFixed(1)} kg` : '0.0 kg',
      icon: Leaf,
      color: 'text-teal-400',
      bg: 'bg-teal-500/10 border-teal-500/20'
    },
    {
      label: 'Window Violations',
      value: job ? `${job.violation_count}` : '0',
      icon: AlertTriangle,
      color: job && job.violation_count > 0 ? 'text-rose-400' : 'text-slate-400',
      bg: job && job.violation_count > 0 ? 'bg-rose-500/10 border-rose-500/20' : 'bg-slate-800/40 border-slate-700/40'
    },
    {
      label: 'Solver Runtime',
      value: job ? `${job.execution_time_ms.toFixed(1)} ms` : '0.0 ms',
      icon: ShieldCheck,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((c, i) => {
        const Icon = c.icon;
        return (
          <div key={i} className={`rounded-xl border p-4 bg-slate-800/80 backdrop-blur ${c.bg} transition-all duration-200 hover:scale-[1.02]`}>
            <div className="flex items-center justify-between text-slate-400 text-xs mb-2">
              <span className="font-medium uppercase tracking-wider">{c.label}</span>
              <Icon className={`w-4 h-4 ${c.color}`} />
            </div>
            <div className="text-xl font-bold text-white tracking-tight">{c.value}</div>
          </div>
        );
      })}
    </div>
  );
};
