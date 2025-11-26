import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple, Dict
from scipy.spatial.distance import cdist

@dataclass
class Location:
    id: int
    lat: float
    lon: float
    demand: int
    is_depot: bool = False
    cluster: str = "Unknown"

class RealWorldVRPCreator:
    """
    Generates synthetic VRP data based on real-world geography of São Paulo.
    Uses Gaussian clusters to simulate realistic population density.
    """

    # Approximate coordinates for hubs in Greater São Paulo
    HUBS = {
        "Centro": (-23.5505, -46.6333),
        "Itaim": (-23.5840, -46.6780),
        "Guarulhos": (-23.4628, -46.5333),
        "Osasco": (-23.5329, -46.7920)
    }

    AVG_SPEED_KMH = 35.0
    
    def __init__(self, num_customers: int = 50, random_seed: int = 42):
        self.num_customers = num_customers
        self.random_seed = random_seed
        np.random.seed(self.random_seed)

    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """
        Calculates Haversine distance between two points in meters.
        Vectorized implementation for NumPy arrays.
        """
        R = 6371000  # Radius of Earth in meters
        
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        
        a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c

    def generate_locations(self) -> List[Location]:
        """
        Generates customer locations using Gaussian clusters around hubs.
        """
        locations = []
        
        # Depot is fixed at "Centro" for this scenario
        depot_lat, depot_lon = self.HUBS["Centro"]
        locations.append(Location(id=0, lat=depot_lat, lon=depot_lon, demand=0, is_depot=True, cluster="Depot"))

        # Distribute customers among hubs
        points_per_hub = self.num_customers // len(self.HUBS)
        remainder = self.num_customers % len(self.HUBS)
        
        customer_id = 1
        for i, (hub_name, (hub_lat, hub_lon)) in enumerate(self.HUBS.items()):
            count = points_per_hub + (1 if i < remainder else 0)
            
            # Generate points with small standard deviation (approx 2-3km spread)
            # 0.02 degrees is roughly 2.2km
            lats = np.random.normal(hub_lat, 0.02, count)
            lons = np.random.normal(hub_lon, 0.02, count)
            
            for lat, lon in zip(lats, lons):
                demand = np.random.randint(1, 10) # Random demand
                locations.append(Location(id=customer_id, lat=lat, lon=lon, demand=demand, cluster=hub_name))
                customer_id += 1
                
        return locations

    def calculate_time_matrix(self, locations: List[Location]) -> np.ndarray:
        """
        Calculates travel time matrix in minutes using Haversine distance and average speed.
        """
        coords = np.array([(loc.lat, loc.lon) for loc in locations])
        lats = coords[:, 0]
        lons = coords[:, 1]
        
        # Create meshgrid for vectorized calculation
        lat1, lat2 = np.meshgrid(lats, lats)
        lon1, lon2 = np.meshgrid(lons, lons)
        
        dist_matrix_meters = self._haversine_distance(lat1, lon1, lat2, lon2)
        
        # Convert to km
        dist_matrix_km = dist_matrix_meters / 1000.0
        
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Tuple, Dict
from scipy.spatial.distance import cdist

@dataclass
class Location:
    id: int
    lat: float
    lon: float
    demand: int
    is_depot: bool = False
    cluster: str = "Unknown"

class RealWorldVRPCreator:
    """
    Generates synthetic VRP data based on real-world geography of São Paulo.
    Uses Gaussian clusters to simulate realistic population density.
    """

    # Approximate coordinates for hubs in Greater São Paulo
    HUBS = {
        "Centro": (-23.5505, -46.6333),
        "Itaim": (-23.5840, -46.6780),
        "Guarulhos": (-23.4628, -46.5333),
        "Osasco": (-23.5329, -46.7920)
    }

    AVG_SPEED_KMH = 20.0 # Reduced to realistic urban speed (traffic, lights)
    
    def __init__(self, num_customers: int = 50, random_seed: int = 42):
        self.num_customers = num_customers
        self.random_seed = random_seed
        np.random.seed(self.random_seed)

    def _haversine_distance(self, lat1, lon1, lat2, lon2) -> float:
        """
        Calculates Haversine distance between two points in meters.
        Vectorized implementation for NumPy arrays.
        """
        R = 6371000  # Radius of Earth in meters
        
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        dphi = np.radians(lat2 - lat1)
        dlambda = np.radians(lon2 - lon1)
        
        a = np.sin(dphi/2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c

    def generate_locations(self) -> List[Location]:
        """
        Generates customer locations using Gaussian clusters around hubs.
        """
        locations = []
        
        # Depot is fixed at "Centro" for this scenario
        depot_lat, depot_lon = self.HUBS["Centro"]
        locations.append(Location(id=0, lat=depot_lat, lon=depot_lon, demand=0, is_depot=True, cluster="Depot"))

        # Distribute customers among hubs
        points_per_hub = self.num_customers // len(self.HUBS)
        remainder = self.num_customers % len(self.HUBS)
        
        customer_id = 1
        for i, (hub_name, (hub_lat, hub_lon)) in enumerate(self.HUBS.items()):
            count = points_per_hub + (1 if i < remainder else 0)
            
            # Generate points with small standard deviation (approx 2-3km spread)
            # 0.02 degrees is roughly 2.2km
            lats = np.random.normal(hub_lat, 0.02, count)
            lons = np.random.normal(hub_lon, 0.02, count)
            
            for lat, lon in zip(lats, lons):
                demand = np.random.randint(1, 10) # Random demand
                locations.append(Location(id=customer_id, lat=lat, lon=lon, demand=demand, cluster=hub_name))
                customer_id += 1
                
        return locations

    def calculate_time_matrix(self, locations: List[Location]) -> np.ndarray:
        """
        Calculates travel time matrix in minutes using Haversine distance and average speed.
        Adds 'urban friction' (traffic lights, parking) to make it more realistic.
        """
        coords = np.array([(loc.lat, loc.lon) for loc in locations])
        lats = coords[:, 0]
        lons = coords[:, 1]
        
        # Create meshgrid for vectorized calculation
        lat1, lat2 = np.meshgrid(lats, lats)
        lon1, lon2 = np.meshgrid(lons, lons)
        
        dist_matrix_meters = self._haversine_distance(lat1, lon1, lat2, lon2)
        
        # Convert to km
        dist_matrix_km = dist_matrix_meters / 1000.0
        
        # Time = Distance / Speed
        # Result in hours, convert to minutes
        time_matrix_minutes = (dist_matrix_km / self.AVG_SPEED_KMH) * 60
        
        # Add Urban Friction: +3 minutes per trip (except self-loops)
        # This accounts for traffic lights, turning, parking maneuvers
        friction = 3.0
        time_matrix_minutes = time_matrix_minutes + friction
        np.fill_diagonal(time_matrix_minutes, 0) # No cost to stay in place
        
        return np.round(time_matrix_minutes).astype(int)

    def create_data_model(self, max_time_minutes: int = 480, service_time: int = 30, num_vehicles: int = None):
        """
        Creates the data model for OR-Tools.
        """
        locations = self.generate_locations()
        time_matrix = self.calculate_time_matrix(locations)
        
        # Time Windows (Simplified)
        # Depot: 0 to max_time
        # Customers: Random windows within [0, max_time]
        time_windows = [(0, max_time_minutes)] # Depot
        
        for i in range(1, len(locations)):
            # Logic: Window start is roughly proportional to distance from depot + random slack
            dist_from_depot = time_matrix[0][i]
            earliest_start = int(dist_from_depot)
            latest_start = max_time_minutes - service_time - 30 # Must start before end - service
            
            if latest_start < earliest_start:
                latest_start = earliest_start + 10
                
            start = np.random.randint(earliest_start, max(earliest_start + 1, latest_start))
            end = min(start + 180, max_time_minutes) # 3h window
            time_windows.append((start, end))

        # Fleet Sizing
        if num_vehicles is None:
            # Dynamic Fleet Sizing (Fallback)
            total_demand = sum(l.demand for l in locations)
            avg_capacity = 50
            min_vehicles = int(np.ceil(total_demand / avg_capacity * 1.2))
            num_vehicles = max(5, min_vehicles) 
        
        return {
            "time_matrix": time_matrix,
            "time_windows": time_windows,
            "num_vehicles": num_vehicles,
            "depot": 0,
            "demands": [l.demand for l in locations],
            "vehicle_capacities": [50] * num_vehicles,
            "locations": locations,
            "max_time_minutes": max_time_minutes,
            "service_time": service_time
        }
