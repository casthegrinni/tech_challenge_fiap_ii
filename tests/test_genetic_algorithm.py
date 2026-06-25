import math
import random
import unittest
from unittest.mock import patch

from src.domain.city import City, Priority
from src.domain.vehicle import Vehicle
from src.engine.genetic_algorithm import (
    calculate_distance,
    calculate_fitness,
    calculate_vrp_fitness,
    decode_vrp_routes,
    generate_random_population,
    mutate,
    order_crossover,
    sort_population,
)


class TestGeneticAlgorithm(unittest.TestCase):
    def setUp(self):
        self.cities = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]

    # Testa se a população inicial tem o tamanho esperado e se cada indivíduo é uma permutação das cidades.
    def test_generate_random_population_returns_permutations_with_expected_size(self):
        random.seed(42)

        population = generate_random_population(self.cities, population_size=5)

        self.assertEqual(len(population), 5)
        for individual in population:
            self.assertEqual(len(individual), len(self.cities))
            self.assertCountEqual(individual, self.cities)

    # Testa se a distância entre dois pontos iguais é zero.
    def test_calculate_distance_returns_zero_for_same_point(self):
        self.assertEqual(calculate_distance((10.0, -20.0), (10.0, -20.0)), 0.0)

    # Testa se a distância entre coordenadas usa o cálculo Haversine em quilômetros.
    def test_calculate_distance_uses_haversine_kilometers(self):
        distance = calculate_distance((0.0, 0.0), (0.0, 1.0))

        self.assertTrue(math.isclose(distance, 111.195, rel_tol=1e-4))

    # Testa se o fitness TSP soma a rota completa voltando para a cidade inicial.
    def test_calculate_fitness_tsp_closes_the_cycle(self):
        path = [(0.0, 0.0), (0.0, 1.0), (0.0, 2.0)]

        fitness = calculate_fitness(path)

        expected = (
            calculate_distance(path[0], path[1])
            + calculate_distance(path[1], path[2])
            + calculate_distance(path[2], path[0])
        )
        self.assertTrue(math.isclose(fitness, expected, rel_tol=1e-9))

    # Testa se calculate_fitness usa o cálculo VRP quando frota, depósito e mapa de cidades são informados.
    def test_calculate_fitness_delegates_to_vrp_when_vrp_parameters_are_present(self):
        depot = (0.0, 0.0)
        hospital = City(
            id=1,
            name="H1",
            x=0.1,
            y=0.0,
            demand=10.0,
            priority=Priority.REGULAR,
        )
        tour = [hospital.coordinates]
        vehicles = [Vehicle(id=1, name="V1", capacity=20.0, autonomy=100.0)]
        city_map = {hospital.coordinates: hospital}

        self.assertEqual(
            calculate_fitness(tour, vehicles, depot, city_map),
            calculate_vrp_fitness(tour, vehicles, depot, city_map),
        )

    # Testa se uma cidade impossível de atender permanece como não visitada e gera rota vazia para o veículo.
    def test_decode_vrp_routes_returns_unvisited_when_fleet_cannot_serve_city(self):
        depot = (0.0, 0.0)
        hospital = City(
            id=1,
            name="H1",
            x=0.1,
            y=0.0,
            demand=50.0,
            priority=Priority.REGULAR,
        )
        vehicles = [Vehicle(id=1, name="V1", capacity=10.0, autonomy=100.0)]

        routes, unvisited = decode_vrp_routes(
            [hospital.coordinates],
            vehicles,
            depot,
            {hospital.coordinates: hospital},
        )

        self.assertEqual(routes, [[depot, depot]])
        self.assertEqual(unvisited, [hospital.coordinates])

    # Testa se o fitness VRP aplica a penalidade de 1000 pontos para hospitais não visitados.
    def test_calculate_vrp_fitness_adds_penalty_for_unvisited_hospitals(self):
        depot = (0.0, 0.0)
        hospital = City(
            id=1,
            name="H1",
            x=0.1,
            y=0.0,
            demand=50.0,
            priority=Priority.REGULAR,
        )
        vehicles = [Vehicle(id=1, name="V1", capacity=10.0, autonomy=100.0)]

        fitness = calculate_vrp_fitness(
            [hospital.coordinates],
            vehicles,
            depot,
            {hospital.coordinates: hospital},
        )

        self.assertEqual(fitness, 1000.0)

    # Testa se o crossover mantém o trecho do primeiro pai e preenche o restante na ordem do segundo pai.
    def test_order_crossover_preserves_parent_slice_and_remaining_order(self):
        parent1 = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)]
        parent2 = [(5, 5), (4, 4), (3, 3), (2, 2), (1, 1)]

        with patch("src.engine.genetic_algorithm.random.randint", side_effect=[1, 4]):
            child = order_crossover(parent1, parent2)

        self.assertEqual(child, [(5, 5), (2, 2), (3, 3), (4, 4), (1, 1)])
        self.assertCountEqual(child, parent1)

    # Testa se a mutação troca duas cidades adjacentes quando a probabilidade de mutação é atingida.
    def test_mutate_swaps_adjacent_cities_when_probability_hits(self):
        solution = [(1, 1), (2, 2), (3, 3)]

        with patch("src.engine.genetic_algorithm.random.random", return_value=0.0):
            with patch("src.engine.genetic_algorithm.random.randint", return_value=1):
                mutated = mutate(solution, mutation_probability=1.0)

        self.assertEqual(mutated, [(1, 1), (3, 3), (2, 2)])
        self.assertEqual(solution, [(1, 1), (2, 2), (3, 3)])

    # Testa se a mutação mantém a solução original quando a probabilidade de mutação não é atingida.
    def test_mutate_keeps_solution_when_probability_misses(self):
        solution = [(1, 1), (2, 2), (3, 3)]

        with patch("src.engine.genetic_algorithm.random.random", return_value=1.0):
            mutated = mutate(solution, mutation_probability=0.5)

        self.assertEqual(mutated, solution)

    # Testa se a população é ordenada do menor fitness para o maior fitness.
    def test_sort_population_orders_by_lowest_fitness(self):
        population = [["worst"], ["best"], ["middle"]]
        fitness = [30.0, 10.0, 20.0]

        sorted_population, sorted_fitness = sort_population(population, fitness)

        self.assertEqual(list(sorted_population), [["best"], ["middle"], ["worst"]])
        self.assertEqual(list(sorted_fitness), [10.0, 20.0, 30.0])


if __name__ == "__main__":
    unittest.main()
