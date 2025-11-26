from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Dict, Any

class RouteOptimizer:
    """
    Wrapper for Google OR-Tools to solve VRP with Time Windows.
    """

    def __init__(self, data_model: Dict[str, Any], time_limit_seconds: int = 30):
        self.data = data_model
        self.time_limit_seconds = time_limit_seconds
        self.manager = None
        self.routing = None
        self.solution = None

    def solve(self) -> List[List[int]]:
        """
        Solves the VRP and returns a list of routes (list of node indices).
        """
        # Create the routing index manager.
        self.manager = pywrapcp.RoutingIndexManager(
            len(self.data['time_matrix']),
            self.data['num_vehicles'],
            self.data['depot']
        )

        # Create Routing Model.
        self.routing = pywrapcp.RoutingModel(self.manager)

        # 1. Define Transit Callback (Time)
        def time_callback(from_index, to_index):
            from_node = self.manager.IndexToNode(from_index)
            to_node = self.manager.IndexToNode(to_index)
            
            travel_time = self.data['time_matrix'][from_node][to_node]
            
            # Add service time of the source node (if it's a customer)
            # Logic: Arrival at B = Arrival at A + Service at A + Travel A->B
            service_time = 0
            if from_node != self.data['depot']:
                service_time = self.data.get('service_time', 0)
                
            return travel_time + service_time

        transit_callback_index = self.routing.RegisterTransitCallback(time_callback)
        
        # Define cost of each arc.
        self.routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add Fixed Cost to minimize number of vehicles
        # This ensures the solver uses the minimum number of vehicles necessary
        self.routing.SetFixedCostOfAllVehicles(100000)

        # 2. Add Time Window Constraints
        time = 'Time'
        max_time = self.data.get('max_time_minutes', 480)
        
        self.routing.AddDimension(
            transit_callback_index,
            1440,  # allow waiting time up to 24h
            1440,  # maximum time per vehicle (24h) - effectively removing hard shift limit
            False,  # Don't force start cumul to zero
            time
        )
        time_dimension = self.routing.GetDimensionOrDie(time)
        
        # Add time window constraints for each location except depot.
        for location_idx, (start, end) in enumerate(self.data['time_windows']):
            if location_idx == self.data['depot']:
                continue
            index = self.manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(start, end)

        # Add time window constraints for the depot start and end
        # Relax depot end time to 1440 (24h) to allow late returns (overtime)
        depot_idx = self.data['depot']
        for vehicle_id in range(self.data['num_vehicles']):
            index = self.routing.Start(vehicle_id)
            time_dimension.CumulVar(index).SetRange(self.data['time_windows'][depot_idx][0], 1440)

        # 3. Add Capacity Constraints
        def demand_callback(from_index):
            from_node = self.manager.IndexToNode(from_index)
            return self.data['demands'][from_node]

        demand_callback_index = self.routing.RegisterUnaryTransitCallback(demand_callback)
        self.routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            self.data['vehicle_capacities'],
            True,  # start cumul to zero
            'Capacity'
        )

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = self.time_limit_seconds

        # Solve the problem.
        self.solution = self.routing.SolveWithParameters(search_parameters)

        return self._extract_routes()

    def _extract_routes(self) -> List[List[int]]:
        """
        Extracts routes from the OR-Tools solution object.
        """
        routes = []
        if not self.solution:
            return routes

        for vehicle_id in range(self.data['num_vehicles']):
            index = self.routing.Start(vehicle_id)
            route = []
            while not self.routing.IsEnd(index):
                node_index = self.manager.IndexToNode(index)
                if node_index != self.data['depot']:
                    route.append(node_index)
                index = self.solution.Value(self.routing.NextVar(index))
            routes.append(route)
        return routes

    def solve_greedy(self) -> List[List[int]]:
        """
        Solves VRP using a simple Nearest Neighbor heuristic (simulating manual planning).
        Now respects Capacity AND Max Route Duration (End of Shift).
        """
        routes = []
        unvisited = set(range(1, len(self.data['time_matrix']))) 
        max_time = self.data.get('max_time_minutes', 480)
        
        while unvisited:
            route = []
            current_load = 0
            current_time = 0
            current_node = self.data['depot']
            vehicle_capacity = self.data['vehicle_capacities'][0] 
            
            while True:
                nearest = None
                min_dist = float('inf')
                
                for candidate in unvisited:
                    dist_to = self.data['time_matrix'][current_node][candidate]
                    dist_back = self.data['time_matrix'][candidate][self.data['depot']]
                    demand = self.data['demands'][candidate]
                    service_time = self.data.get('service_time', 10)
                    
                    # Check Capacity
                    if current_load + demand > vehicle_capacity:
                        continue
                        
                    # Check Time (Trip to Node + Service + Trip Back to Depot <= Max Time)
                    if current_time + dist_to + service_time + dist_back > max_time:
                        continue
                    
                    if dist_to < min_dist:
                        min_dist = dist_to
                        nearest = candidate
                
                if nearest is None:
                    break 
                
                # Move to nearest
                route.append(nearest)
                unvisited.remove(nearest)
                current_load += self.data['demands'][nearest]
                current_time += min_dist + 10 # Add travel + service
                current_node = nearest
            
            routes.append(route)
            
        return routes
