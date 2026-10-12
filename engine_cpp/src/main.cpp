#include "bitmask_tsp.hpp"
#include <iostream>
#include <vector>
#include <iomanip>

int main(int argc, char* argv[]) {
    // Demo 5-city benchmark problem
    std::vector<std::vector<double>> cost_matrix = {
        {0.0, 10.0, 15.0, 20.0, 25.0},
        {10.0, 0.0, 35.0, 25.0, 18.0},
        {15.0, 35.0, 0.0, 30.0, 20.0},
        {20.0, 25.0, 30.0, 0.0, 12.0},
        {25.0, 18.0, 20.0, 12.0, 0.0}
    };

    std::cout << "[C++ Engine] Running Held-Karp Bitmask DP for N = " << cost_matrix.size() << " nodes..." << std::endl;
    TSPResult res = BitmaskTSPSolver::solve(cost_matrix);

    std::cout << "Optimal Tour Cost: " << std::fixed << std::setprecision(2) << res.optimal_cost << std::endl;
    std::cout << "Optimal Sequence:  ";
    for (size_t i = 0; i < res.optimal_route.size(); ++i) {
        std::cout << res.optimal_route[i] << (i + 1 < res.optimal_route.size() ? " -> " : "");
    }
    std::cout << std::endl;
    std::cout << "States Explored:   " << res.states_explored << std::endl;
    std::cout << "Execution Time:    " << res.execution_time_ms << " ms" << std::endl;

    return 0;
}
