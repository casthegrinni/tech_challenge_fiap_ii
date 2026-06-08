import unittest
from src.domain.city import City, Priority
from src.domain.vehicle import Vehicle
from src.engine.genetic_algorithm import decode_vrp_routes, calculate_vrp_fitness

class TestVRPOptimization(unittest.TestCase):
    def setUp(self):
        self.depot_loc = (0.0, 0.0)
        
        # Hospitais para testes de decodificação
        self.h1 = City(id=1, name="H1", x=0.1, y=0.0, demand=10.0, priority=Priority.REGULAR)
        self.h2 = City(id=2, name="H2", x=0.2, y=0.0, demand=10.0, priority=Priority.CRITICAL)
        self.h3 = City(id=3, name="H3", x=0.3, y=0.0, demand=10.0, priority=Priority.REGULAR)
        
        self.hospitals = [self.h1, self.h2, self.h3]
        self.city_map = {h.coordinates: h for h in self.hospitals}
        self.giant_tour = [self.h1.coordinates, self.h2.coordinates, self.h3.coordinates]

    def test_decode_vrp_routes_capacity_limit(self):
        # Cada veículo tem capacidade 15, e cada hospital demanda 10.
        vehicles = [
            Vehicle(id=1, name="V1", capacity=15.0, autonomy=500.0),
            Vehicle(id=2, name="V2", capacity=15.0, autonomy=500.0),
            Vehicle(id=3, name="V3", capacity=15.0, autonomy=500.0),
        ]
        
        routes, unvisited = decode_vrp_routes(
            self.giant_tour, vehicles, self.depot_loc, self.city_map
        )
        
        self.assertEqual(len(unvisited), 0)
        self.assertEqual(len(routes[0]), 3) # Depot -> H1 -> Depot
        self.assertEqual(len(routes[1]), 3) # Depot -> H2 -> Depot
        self.assertEqual(len(routes[2]), 3) # Depot -> H3 -> Depot

    def test_decode_vrp_routes_autonomy_limit(self):
        # Cada veículo tem capacidade suficiente (50), mas autonomia limitada.
        # H3 está a 33.36 km do depósito, então a viagem de ida e volta para H3 requer 66.72 km.
        # V2 precisa de autonomia suficiente para cobrir H3 (definimos 80 km).
        vehicles = [
            Vehicle(id=1, name="V1", capacity=50.0, autonomy=50.0),
            Vehicle(id=2, name="V2", capacity=50.0, autonomy=80.0),
        ]
        
        routes, unvisited = decode_vrp_routes(
            self.giant_tour, vehicles, self.depot_loc, self.city_map
        )
        
        # O veículo 1 atende H1 e H2 (44.48 km)
        # O veículo 2 atende H3 (66.72 km)
        self.assertEqual(len(unvisited), 0)
        self.assertEqual(len(routes[0]), 4) # Depot -> H1 -> H2 -> Depot
        self.assertEqual(routes[0][1], self.h1.coordinates)
        self.assertEqual(routes[0][2], self.h2.coordinates)
        self.assertEqual(routes[1][1], self.h3.coordinates)

    def test_vrp_fitness_critical_priority(self):
        # Para testar o impacto das prioridades, criamos coordenadas simétricas:
        # H_reg (regular) em (0.1, 0.0) -> ~11.12 km do depósito
        # H_crit (crítico) em (-0.1, 0.0) -> ~11.12 km do depósito
        # A distância total Depot -> H_reg -> H_crit -> Depot é igual a Depot -> H_crit -> H_reg -> Depot.
        h_reg = City(id=1, name="H_REG", x=0.1, y=0.0, demand=10.0, priority=Priority.REGULAR)
        h_crit = City(id=2, name="H_CRIT", x=-0.1, y=0.0, demand=10.0, priority=Priority.CRITICAL)
        
        local_city_map = {
            h_reg.coordinates: h_reg,
            h_crit.coordinates: h_crit
        }
        
        vehicles = [
            Vehicle(id=1, name="V1", capacity=50.0, autonomy=500.0)
        ]
        
        # Caso A: Atende o crítico por último (Depot -> H_reg -> H_crit -> Depot)
        tour_a = [h_reg.coordinates, h_crit.coordinates]
        fitness_a = calculate_vrp_fitness(tour_a, vehicles, self.depot_loc, local_city_map)
        
        # Caso B: Atende o crítico primeiro (Depot -> H_crit -> H_reg -> Depot)
        tour_b = [h_crit.coordinates, h_reg.coordinates]
        fitness_b = calculate_vrp_fitness(tour_b, vehicles, self.depot_loc, local_city_map)
        
        # O Caso B (crítico primeiro) deve ter um custo de fitness menor (melhor) do que o Caso A
        self.assertLess(fitness_b, fitness_a)

if __name__ == '__main__':
    unittest.main()
