#include "bitmask_tsp.hpp"
#include <chrono>
#include <limits>
#include <algorithm>

const double INF = std::numeric_limits<double>::infinity();

TSPResult BitmaskTSPSolver::solve(const std::vector<std::vector<double>>& cost_matrix) {
    auto start_time = std::chrono::high_resolution_clock::now();
    int n = cost_matrix.size();

    if (n <= 1) {
        return {0.0, {0, 0}, 1, 0.0};
    }

    if (n == 2) {
        auto end_time = std::chrono::high_resolution_clock::now();
        double ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
        return {cost_matrix[0][1] + cost_matrix[1][0], {0, 1, 0}, 1, ms};
    }

    int num_cust = n - 1;
    int total_masks = 1 << num_cust;

    // Use flat 1D vector for optimal CPU cache spatial locality: index = mask * num_cust + u
    std::vector<double> dp(total_masks * num_cust, INF);
    std::vector<int> parent(total_masks * num_cust, -1);
    long long states_explored = num_cust;

    // Base cases: single customer reached directly from depot 0
    for (int u = 0; u < num_cust; ++u) {
        int mask = 1 << u;
        dp[mask * num_cust + u] = cost_matrix[0][u + 1];
        parent[mask * num_cust + u] = -1; // Came from depot
    }

    // Solve for subset sizes 2 to num_cust
    for (int size = 2; size <= num_cust; ++size) {
        for (int mask = 0; mask < total_masks; ++mask) {
            // __builtin_popcount uses hardware instruction (POPCNT)
            if (__builtin_popcount(mask) != size) continue;

            for (int u = 0; u < num_cust; ++u) {
                if (!(mask & (1 << u))) continue;

                int prev_mask = mask ^ (1 << u);
                int node_u = u + 1;
                double best_cost = INF;
                int best_prev = -1;

                for (int v = 0; v < num_cust; ++v) {
                    if (!(prev_mask & (1 << v))) continue;

                    int node_v = v + 1;
                    double cost = dp[prev_mask * num_cust + v] + cost_matrix[node_v][node_u];
                    if (cost < best_cost) {
                        best_cost = cost;
                        best_prev = v;
                    }
                }

                dp[mask * num_cust + u] = best_cost;
                parent[mask * num_cust + u] = best_prev;
                states_explored++;
            }
        }
    }

    // Complete tour returning to depot 0
    int final_mask = total_masks - 1;
    double optimal_cost = INF;
    int last_cust = -1;

    for (int u = 0; u < num_cust; ++u) {
        int node_u = u + 1;
        double cost = dp[final_mask * num_cust + u] + cost_matrix[node_u][0];
        if (cost < optimal_cost) {
            optimal_cost = cost;
            last_cust = u;
        }
    }

    // Route reconstruction
    std::vector<int> customers_rev;
    int curr_mask = final_mask;
    int curr_u = last_cust;

    while (curr_u != -1 && curr_mask > 0) {
        customers_rev.push_back(curr_u + 1);
        int prev_u = parent[curr_mask * num_cust + curr_u];
        curr_mask = curr_mask ^ (1 << curr_u);
        curr_u = prev_u;
    }

    std::reverse(customers_rev.begin(), customers_rev.end());
    std::vector<int> optimal_route = {0};
    optimal_route.insert(optimal_route.end(), customers_rev.begin(), customers_rev.end());
    optimal_route.push_back(0);

    auto end_time = std::chrono::high_resolution_clock::now();
    double ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();

    return {optimal_cost, optimal_route, states_explored, ms};
}
