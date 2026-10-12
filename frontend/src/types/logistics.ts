export interface Depot {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  address?: string;
  operating_hours: string;
}

export interface Vehicle {
  id: number;
  depot_id: number;
  license_plate: string;
  vehicle_type: string;
  max_weight_kg: number;
  max_volume_m3: number;
  max_range_km: number;
  cost_per_km: number;
  cost_per_hour: number;
  is_electric: boolean;
  battery_capacity_kwh: number;
  current_battery_kwh: number;
  emissions_factor_g_co2_per_km: number;
  is_available: boolean;
}

export interface Package {
  id: number;
  weight_kg: number;
  volume_m3: number;
  fragile: boolean;
  requires_cold_chain: boolean;
  tracking_code?: string;
}

export interface Customer {
  id: number;
  name: string;
  contact_email?: string;
  phone?: string;
  latitude: number;
  longitude: number;
  address?: string;
}

export interface DeliveryRequest {
  id: number;
  customer_id: number;
  depot_id?: number;
  window_start: string;
  window_end: string;
  priority: number;
  service_time_min: number;
  status: string;
  packages: Package[];
  customer?: Customer;
}

export interface RouteStop {
  id?: number;
  stop_order: number;
  delivery_request_id?: number;
  stop_type: 'depot_start' | 'delivery' | 'charging' | 'depot_end';
  location_name?: string;
  latitude: number;
  longitude: number;
  estimated_arrival?: string;
  estimated_departure?: string;
  waiting_time_min: number;
  slack_time_min: number;
  remaining_battery_kwh?: number;
}

export interface PlannedRoute {
  id?: number;
  vehicle_id: number;
  route_distance_km: number;
  route_duration_min: number;
  route_cost: number;
  route_co2_kg: number;
  summary_polyline?: string;
  stops: RouteStop[];
}

export interface OptimizationJob {
  id: string;
  created_at: string;
  objective_mode: string;
  algorithm_name: string;
  total_distance_km: number;
  total_duration_min: number;
  total_cost: number;
  total_co2_kg: number;
  violation_count: number;
  status: string;
  execution_time_ms: number;
  routes: PlannedRoute[];
  dp_matrix_sample?: {
    num_customers: number;
    total_subsets: number;
    sample_states: Array<{
      mask: number;
      binary: string;
      values: Array<number | null>;
    }>;
  };
  search_tree_sample?: {
    total_nodes_explored: number;
    pruned_by_bound: number;
    pruned_by_time: number;
    pruned_by_capacity: number;
    sample_tree: Array<{
      id: string;
      parent: string;
      label: string;
      status: string;
    }>;
  };
}

export interface BenchmarkResult {
  algorithm_name: string;
  execution_time_ms: number;
  memory_usage_kb: number;
  states_explored: number;
  solution_cost: number;
  total_distance_km: number;
  total_duration_min: number;
  optimality_gap_percent: number;
  is_optimal_guaranteed: boolean;
}

export interface BenchmarkResponse {
  instance_size: number;
  results: BenchmarkResult[];
}

export interface ScenarioDelta {
  delta_distance_km: number;
  delta_distance_percent: number;
  delta_duration_min: number;
  delta_duration_percent: number;
  delta_cost: number;
  delta_cost_percent: number;
  delta_co2_kg: number;
  delta_co2_percent: number;
  delta_violations: number;
}

export interface ScenarioSimulationResponse {
  baseline_plan: OptimizationJob;
  simulated_plan: OptimizationJob;
  delta: ScenarioDelta;
  rerouted_vehicle_ids: number[];
  unassigned_order_ids: number[];
}
