import React from 'react';
import { Depot, Vehicle, DeliveryRequest } from '../types/logistics';
import { Truck, Warehouse, Package as PackageIcon, Zap } from 'lucide-react';

interface FleetTableProps {
  depots: Depot[];
  vehicles: Vehicle[];
  orders: DeliveryRequest[];
}

export const FleetTable: React.FC<FleetTableProps> = ({ depots, vehicles, orders }) => {
  return (
    <div className="space-y-6">
      {/* Depots & Vehicles Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Depots Card */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur shadow-lg">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Warehouse className="w-4 h-4 text-emerald-400" />
            Registered Depots &amp; Distribution Hubs
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400 uppercase tracking-wider text-[11px]">
                  <th className="py-2 px-3">ID</th>
                  <th className="py-2 px-3">Hub Name</th>
                  <th className="py-2 px-3">Coordinates</th>
                  <th className="py-2 px-3">Operating Hours</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {depots.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-700/20">
                    <td className="py-2.5 px-3 font-mono text-indigo-400">#{d.id}</td>
                    <td className="py-2.5 px-3 font-semibold text-white">{d.name}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">{d.latitude.toFixed(4)}, {d.longitude.toFixed(4)}</td>
                    <td className="py-2.5 px-3 text-slate-300">{d.operating_hours}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Heterogeneous Vehicles Card */}
        <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur shadow-lg">
          <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
            <Truck className="w-4 h-4 text-indigo-400" />
            Heterogeneous Fleet Specifications
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-700 text-slate-400 uppercase tracking-wider text-[11px]">
                  <th className="py-2 px-3">Plate</th>
                  <th className="py-2 px-3">Type</th>
                  <th className="py-2 px-3">Capacity</th>
                  <th className="py-2 px-3">Powertrain</th>
                  <th className="py-2 px-3">Rate ($/km)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 text-slate-300">
                {vehicles.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-700/20">
                    <td className="py-2.5 px-3 font-mono text-slate-200">{v.license_plate}</td>
                    <td className="py-2.5 px-3 uppercase text-[11px] font-semibold text-indigo-300">{v.vehicle_type}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px]">{v.max_weight_kg} kg &bull; {v.max_volume_m3} m&sup3;</td>
                    <td className="py-2.5 px-3">
                      {v.is_electric ? (
                        <span className="flex items-center gap-1 text-emerald-400 font-medium">
                          <Zap className="w-3.5 h-3.5" /> EV ({v.battery_capacity_kwh} kWh)
                        </span>
                      ) : (
                        <span className="text-slate-400">Diesel ({v.emissions_factor_g_co2_per_km}g/km)</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-emerald-400">${v.cost_per_km.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-5 backdrop-blur shadow-lg">
        <h3 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
          <PackageIcon className="w-4 h-4 text-amber-400" />
          Pending Delivery Requests &amp; Time Windows
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-700 text-slate-400 uppercase tracking-wider text-[11px]">
                <th className="py-2 px-3">Order ID</th>
                <th className="py-2 px-3">Customer</th>
                <th className="py-2 px-3">Delivery Window</th>
                <th className="py-2 px-3">Priority</th>
                <th className="py-2 px-3">Package Weight &amp; Volume</th>
                <th className="py-2 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-300">
              {orders.map((o) => {
                const totalWeight = o.packages?.reduce((acc, p) => acc + p.weight_kg, 0) || 0;
                const totalVolume = o.packages?.reduce((acc, p) => acc + p.volume_m3, 0) || 0;
                return (
                  <tr key={o.id} className="hover:bg-slate-700/20">
                    <td className="py-2.5 px-3 font-mono text-indigo-400">#{o.id}</td>
                    <td className="py-2.5 px-3 font-semibold text-white">{o.customer?.name || 'Customer'}</td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-300">
                      {new Date(o.window_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(o.window_end).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${o.priority >= 4 ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-700 text-slate-300'}`}>
                        P{o.priority} {o.priority === 5 ? 'URGENT' : ''}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-400">
                      {totalWeight.toFixed(1)} kg &bull; {totalVolume.toFixed(2)} m&sup3;
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] font-medium uppercase">
                        {o.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
