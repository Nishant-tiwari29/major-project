# Product Requirements Document (PRD) & Software Requirements Specification (SRS)
## Intelligent Logistics & Vehicle Routing Optimizer 2.0

---

## 1. Executive Summary
The **Intelligent Logistics & Vehicle Routing Optimizer 2.0** is an enterprise-grade decision-support platform designed to solve multi-depot, heterogeneous fleet Vehicle Routing Problems with Time Windows (MD-VRPTW), capacity limits, driver regulations, Electric Vehicle (EV) charging stops, and carbon emissions minimization. 

Unlike basic routing wrappers that delegate computation to black-box APIs, this system implements core Computer Science graph algorithms, dynamic programming solvers, and branch-and-bound pruning engines from first principles.

---

## 2. Mathematical Problem Formulation

### 2.1 Sets & Indices
- $\mathcal{D} = \{0, \dots, D-1\}$: Depots
- $\mathcal{C} = \{D, \dots, D + N - 1\}$: Customer delivery locations
- $\mathcal{S} = \{D + N, \dots, D + N + K - 1\}$: EV Charging stations
- $\mathcal{V} = \mathcal{D} \cup \mathcal{C} \cup \mathcal{S}$: All network vertices
- $\mathcal{K}$: Set of heterogeneous vehicles

### 2.2 Decision Variables
- $x_{ijk} \in \{0, 1\}$: 1 if vehicle $k$ traverses edge $(i, j)$; 0 otherwise.
- $t_{ik} \ge 0$: Arrival time of vehicle $k$ at vertex $i$.
- $w_{ik} \ge 0$: Cumulative load (weight) carried by vehicle $k$ arriving at vertex $i$.
- $v_{ik} \ge 0$: Cumulative volume carried by vehicle $k$ arriving at vertex $i$.
- $SoC_{ik} \ge 0$: Battery State of Charge of electric vehicle $k$ at vertex $i$.

### 2.3 Objective Function (Multi-Objective Min-Max Scalarization)
$$\min Z = w_{\text{cost}} \hat{C} + w_{\text{time}} \hat{T} + w_{\text{dist}} \hat{D} + w_{\text{emissions}} \hat{E} + w_{\text{penalty}} \hat{P}$$
where each component $\hat{J}$ is normalized via:
$$\hat{J} = \frac{J - J^{\min}}{J^{\max} - J^{\min} + \epsilon}$$

### 2.4 Constraints
1. **Flow Conservation:**
   $$\sum_{j \in \mathcal{V}} x_{djk} = \sum_{i \in \mathcal{V}} x_{idk} \le 1 \quad \forall k \in \mathcal{K}, d \in \mathcal{D}$$
   $$\sum_{k \in \mathcal{K}} \sum_{i \in \mathcal{V}} x_{ijk} = 1 \quad \forall j \in \mathcal{C}$$
2. **Vehicle Capacity (Weight & Volume):**
   $$\sum_{i \in \mathcal{C}} q_i^{\text{weight}} \cdot \sum_{j \in \mathcal{V}} x_{ijk} \le Q_k^{\text{weight}} \quad \forall k \in \mathcal{K}$$
   $$\sum_{i \in \mathcal{C}} q_i^{\text{vol}} \cdot \sum_{j \in \mathcal{V}} x_{ijk} \le Q_k^{\text{vol}} \quad \forall k \in \mathcal{K}$$
3. **Delivery Time Windows:**
   $$e_i \le t_{ik} \le l_i \quad \forall i \in \mathcal{C}, k \in \mathcal{K}$$
   $$t_{jk} \ge t_{ik} + s_i + \text{dur}(i, j) - M(1 - x_{ijk})$$
4. **EV State of Charge & Reserve:**
   $$SoC_{jk} = SoC_{ik} - \alpha \cdot \text{dist}(i, j) + \Delta SoC_{\text{charge}}$$
   $$SoC_{ik} \ge 0.15 \cdot \text{Capacity}_k \quad \forall i \in \mathcal{V}$$

---

## 3. Functional Requirements (FR)

- **FR-1 (Graph Network Ingestion):** Ingests directed road network topologies, computing exact shortest paths via Dijkstra and A* with admissible Haversine heuristics.
- **FR-2 (Pairwise Distance/Duration Precomputation):** Computes $N \times N$ matrices for all depot and customer pairs using repeated Dijkstra or Floyd-Warshall APSP.
- **FR-3 (Exact TSP via Bitmask DP):** Implements Held-Karp $\mathcal{O}(n^2 2^n)$ algorithm for exact tours on subsets $N \le 16$, recording full parent pointers for route reconstruction.
- **FR-4 (2D Knapsack Vehicle Packing):** Solves 2D (weight and volume) knapsack dynamic programming to maximize delivery priority while preventing capacity overload.
- **FR-5 (VRPTW Branch and Bound):** Implements branch and bound with lower-bound pruning, early deadline detection, and capacity boundary pruning.
- **FR-6 (Clarke-Wright Savings Baseline):** Computes pairwise savings $s(i, j) = c(0, i) + c(0, j) - c(i, j)$ and applies 2-Opt local search to eliminate crossing paths.
- **FR-7 (EV Charging Inserter):** Tracks battery SoC along delivery routes; inserts fast-charging detour stops whenever SoC approaches the 15% reserve limit.
- **FR-8 (Dynamic What-If Simulator):** Simulates road closures, traffic spikes, and fuel price volatility; computes side-by-side delta metrics.
- **FR-9 (ML Edge Travel-Time Predictor):** Trains supervised regression models (Linear, Ridge, Decision Tree, KNN) on urban road observations; adjusts edge weights dynamically.
- **FR-10 (Empirical Benchmark Suite):** Executes all algorithms on identical datasets, reporting runtimes, memory usage, states explored, and the exact optimality gap.
- **FR-11 (Interactive GIS Dashboard):** Renders Leaflet OpenStreetMap with vehicle polylines, arrival ETAs, slack times, and charging detours.
- **FR-12 (Algorithm Visualizer):** Renders interactive step-by-step DP state tables and Branch & Bound tree exploration logs.

---

## 4. Non-Functional Requirements (NFR)

- **NFR-1 (Performance):** Graph SSSP across 100 nodes resolves in $< 20 \text{ ms}$; Bitmask DP on $N=10$ runs in $< 50 \text{ ms}$; Clarke-Wright on $N=50$ runs in $< 100 \text{ ms}$.
- **NFR-2 (Correctness & Soundness):** All heuristics explicitly compute the optimality gap against exact Bitmask DP ground truth. No approximate method is claimed to be globally optimal.
- **NFR-3 (Scalability):** System switches seamlessly between exact exponential solvers for small instances and polynomial heuristics for large fleet operations.
- **NFR-4 (Extensibility):** Clean decoupled architecture separating the DSA engine, ML prediction, API routing, and React UI.
