import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import { OptimizationJob, Depot } from '../types/logistics';

// Fix Leaflet default icon issues in Webpack/Vite
const depotIcon = new L.DivIcon({
  className: 'custom-depot-pin',
  html: `<div style="background-color: #10b981; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.4);"><span style="color: white; font-weight: bold; font-size: 13px;">D</span></div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14]
});

const deliveryIcon = (order: number, priority: number) => new L.DivIcon({
  className: 'custom-delivery-pin',
  html: `<div style="background-color: ${priority >= 4 ? '#ef4444' : '#6366f1'}; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"><span style="color: white; font-weight: bold; font-size: 11px;">${order}</span></div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const chargingIcon = new L.DivIcon({
  className: 'custom-charge-pin',
  html: `<div style="background-color: #f59e0b; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 2px solid #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"><span style="color: white; font-weight: bold; font-size: 12px;">⚡</span></div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const ROUTE_COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#06b6d4'];

interface MapViewProps {
  job: OptimizationJob | null;
  depots: Depot[];
  onTriggerOptimize: (algo: string, obj: string) => void;
  loading: boolean;
}

export const MapView: React.FC<MapViewProps> = ({ job, depots, onTriggerOptimize, loading }) => {
  const [selectedAlgo, setSelectedAlgo] = React.useState('branch_and_bound');
  const [selectedObj, setSelectedObj] = React.useState('balanced');

  const defaultCenter: [number, number] = [28.6139, 77.2090]; // Delhi metro center

  return (
    <div className="space-y-4">
      {/* Optimization Control Bar */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 backdrop-blur shadow-lg">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">DSA Optimizer</label>
            <select
              value={selectedAlgo}
              onChange={(e) => setSelectedAlgo(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="branch_and_bound">Branch & Bound with Pruning (Exact VRPTW)</option>
              <option value="bitmask_dp">Held-Karp Bitmask DP (Exact Global Optimal)</option>
              <option value="clarke_wright">Clarke-Wright Savings + 2-Opt (Scalable CVRP)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Objective Mode</label>
            <select
              value={selectedObj}
              onChange={(e) => setSelectedObj(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="balanced">Balanced (Cost, Time, CO2, Distance)</option>
              <option value="cheapest">Cheapest (Minimize Total Operating Expense)</option>
              <option value="fastest">Fastest (Minimize Total Transit Time)</option>
              <option value="greenest">Greenest (Minimize Carbon Emissions)</option>
              <option value="shortest">Shortest (Minimize Travel Distance)</option>
            </select>
          </div>
        </div>

        <button
          onClick={() => onTriggerOptimize(selectedAlgo, selectedObj)}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium px-5 py-2 rounded-lg text-sm transition-all shadow-md shadow-indigo-600/30 flex items-center gap-2"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              <span>Computing Optimal Tour...</span>
            </>
          ) : (
            <span>Execute Optimization Engine</span>
          )}
        </button>
      </div>

      {/* Map Container */}
      <div className="bg-slate-800/80 border border-slate-700/80 rounded-xl overflow-hidden h-[540px] shadow-lg relative">
        <MapContainer
          center={defaultCenter}
          zoom={11}
          scrollWheelZoom={true}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* Depot Markers */}
          {depots.map((d) => (
            <Marker key={`depot-${d.id}`} position={[d.latitude, d.longitude]} icon={depotIcon}>
              <Popup>
                <div className="text-slate-900 font-sans">
                  <div className="font-bold text-sm text-emerald-700">{d.name}</div>
                  <div className="text-xs text-slate-600">Central Distribution Hub</div>
                  <div className="text-xs text-slate-500 mt-1">Hours: {d.operating_hours}</div>
                </div>
              </Popup>
            </Marker>
          ))}

          {/* Route Polylines and Stop Markers */}
          {job && job.routes.map((route, rIdx) => {
            const polyCoords: [number, number][] = route.stops.map(s => [s.latitude, s.longitude]);
            const routeColor = ROUTE_COLORS[rIdx % ROUTE_COLORS.length];

            return (
              <React.Fragment key={`route-${rIdx}`}>
                <Polyline
                  positions={polyCoords}
                  pathOptions={{ color: routeColor, weight: 4, opacity: 0.85, dashArray: '6, 6' }}
                >
                  <Tooltip sticky>
                    <span className="text-xs font-semibold">Vehicle #{route.vehicle_id} ({route.route_distance_km} km)</span>
                  </Tooltip>
                </Polyline>

                {route.stops.map((stop, sIdx) => {
                  if (stop.stop_type === 'depot_start' || stop.stop_type === 'depot_end') return null;

                  return (
                    <Marker
                      key={`stop-${rIdx}-${sIdx}`}
                      position={[stop.latitude, stop.longitude]}
                      icon={stop.stop_type === 'charging' ? chargingIcon : deliveryIcon(sIdx, 3)}
                    >
                      <Popup>
                        <div className="text-slate-900 font-sans text-xs space-y-1">
                          <div className="font-bold text-indigo-700">{stop.location_name}</div>
                          <div>Stop #{sIdx} &bull; <span className="font-semibold capitalize">{stop.stop_type}</span></div>
                          {stop.waiting_time_min > 0 && (
                            <div className="text-amber-600">Waiting Time: {stop.waiting_time_min.toFixed(1)} min</div>
                          )}
                          <div className="text-slate-500">Slack Time: {stop.slack_time_min.toFixed(1)} min</div>
                          {stop.remaining_battery_kwh && (
                            <div className="text-emerald-600 font-medium">Battery SoC: {stop.remaining_battery_kwh.toFixed(1)} kWh</div>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </React.Fragment>
            );
          })}
        </MapContainer>

        {/* Floating Route Legend */}
        {job && job.routes.length > 0 && (
          <div className="absolute bottom-4 left-4 z-[1000] bg-slate-900/90 border border-slate-700/80 rounded-lg p-3 text-xs backdrop-blur shadow-xl space-y-1.5 max-w-xs">
            <div className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Active Vehicle Dispatches</div>
            {job.routes.map((r, i) => (
              <div key={i} className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: ROUTE_COLORS[i % ROUTE_COLORS.length] }}></div>
                  <span className="text-slate-300 font-medium">Vehicle #{r.vehicle_id}</span>
                </div>
                <span className="text-slate-400">{r.route_distance_km} km &bull; ${r.route_cost}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
