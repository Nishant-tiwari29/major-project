import axios from 'axios';
import {
  Depot,
  Vehicle,
  DeliveryRequest,
  OptimizationJob,
  BenchmarkResponse,
  ScenarioSimulationResponse
} from '../types/logistics';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000/api/v1' : '/api/v1');

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const api = {
  getDepots: async (): Promise<Depot[]> => {
    const res = await apiClient.get<Depot[]>('/fleet/depots');
    return res.data;
  },

  getVehicles: async (): Promise<Vehicle[]> => {
    const res = await apiClient.get<Vehicle[]>('/fleet/vehicles');
    return res.data;
  },

  getPendingOrders: async (): Promise<DeliveryRequest[]> => {
    const res = await apiClient.get<DeliveryRequest[]>('/orders/pending');
    return res.data;
  },

  optimizeRoutes: async (payload: {
    objective_mode: string;
    algorithm_choice: string;
    include_ev_charging?: boolean;
    traffic_multiplier?: number;
  }): Promise<OptimizationJob> => {
    const res = await apiClient.post<OptimizationJob>('/optimize/solve', payload);
    return res.data;
  },

  runBenchmark: async (instanceSize: number = 6): Promise<BenchmarkResponse> => {
    const res = await apiClient.post<BenchmarkResponse>('/benchmark/run', {
      instance_size: instanceSize,
      algorithms: ['bitmask_dp', 'branch_and_bound', 'clarke_wright', 'nearest_neighbor']
    });
    return res.data;
  },

  runSimulation: async (payload: {
    fuel_price_multiplier: number;
    traffic_multiplier: number;
    road_closures: number[][];
  }): Promise<ScenarioSimulationResponse> => {
    const res = await apiClient.post<ScenarioSimulationResponse>('/simulate/scenario', payload);
    return res.data;
  },

  trainML: async (): Promise<any> => {
    const res = await apiClient.post('/ml/train');
    return res.data;
  }
};
