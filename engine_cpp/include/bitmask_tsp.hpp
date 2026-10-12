#ifndef BITMASK_TSP_HPP
#define BITMASK_TSP_HPP

#include <vector>
#include <string>

struct TSPResult {
    double optimal_cost;
    std::vector<int> optimal_route;
    long long states_explored;
    double execution_time_ms;
};

class BitmaskTSPSolver {
public:
    static TSPResult solve(const std::vector<std::vector<double>>& cost_matrix);
};

#endif // BITMASK_TSP_HPP
