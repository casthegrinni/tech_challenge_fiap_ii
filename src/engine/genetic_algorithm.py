import copy
import math
import random
from typing import List, Tuple
from src.domain.city import City, Priority
from src.domain.vehicle import Vehicle

default_problems = {
    5: [(733, 251), (706, 87), (546, 97), (562, 49), (576, 253)],
    10: [
        (470, 169),
        (602, 202),
        (754, 239),
        (476, 233),
        (468, 301),
        (522, 29),
        (597, 171),
        (487, 325),
        (746, 232),
        (558, 136),
    ],
    12: [
        (728, 67),
        (560, 160),
        (602, 312),
        (712, 148),
        (535, 340),
        (720, 354),
        (568, 300),
        (629, 260),
        (539, 46),
        (634, 343),
        (491, 135),
        (768, 161),
    ],
    15: [
        (512, 317),
        (741, 72),
        (552, 50),
        (772, 346),
        (637, 12),
        (589, 131),
        (732, 165),
        (605, 15),
        (730, 38),
        (576, 216),
        (589, 381),
        (711, 387),
        (563, 228),
        (494, 22),
        (787, 288),
    ],
}


def generate_random_population(
    cities_location: List[Tuple[float, float]], population_size: int
) -> List[List[Tuple[float, float]]]:
    """
    Generate a random population of routes for a given set of cities.

    Parameters:
    - cities_location (List[Tuple[float, float]]): A list of tuples representing the locations of cities,
      where each tuple contains the latitude and longitude.
    - population_size (int): The size of the population, i.e., the number of routes to generate.

    Returns:
    List[List[Tuple[float, float]]]: A list of routes, where each route is represented as a list of city locations.
    """
    return [
        random.sample(cities_location, len(cities_location))
        for _ in range(population_size)
    ]


def calculate_distance(
    point1: Tuple[float, float], point2: Tuple[float, float]
) -> float:
    """
    Calculate the Haversine distance between two geographic coordinates (latitude, longitude) in kilometers.

    Parameters:
    - point1 (Tuple[float, float]): The coordinates of the first point (latitude, longitude).
    - point2 (Tuple[float, float]): The coordinates of the second point (latitude, longitude).

    Returns:
    float: The Haversine distance between the two points in kilometers.
    """
    lat1, lon1 = point1
    lat2, lon2 = point2

    R = 6371.0  # Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c


def decode_vrp_routes(
    giant_tour: List[Tuple[float, float]],
    vehicles: List[Vehicle],
    depot_location: Tuple[float, float],
    city_map: dict
) -> Tuple[List[List[Tuple[float, float]]], List[Tuple[float, float]]]:
    """
    Decodifica o 'Giant Tour' (permutação de localizações) em rotas individuais para cada veículo.
    Retorna:
    - Uma lista contendo as rotas de cada veículo (cada rota é uma lista de coordenadas iniciando e terminando no depósito).
    - Uma lista de coordenadas de hospitais que não puderam ser atendidos por falta de capacidade/autonomia da frota.
    """
    routes = [[] for _ in vehicles]
    unvisited = list(giant_tour)

    for v_idx, vehicle in enumerate(vehicles):
        route = [depot_location]
        current_loc = depot_location
        remaining_capacity = vehicle.capacity
        remaining_autonomy = vehicle.autonomy

        while unvisited:
            next_loc = unvisited[0]
            city = city_map[next_loc]

            # Calcular distância de ida e retorno ao depósito
            dist_to_next = calculate_distance(current_loc, next_loc)
            dist_back_to_depot = calculate_distance(next_loc, depot_location)

            # Verificar se cabe na carga e se a autonomia cobre o trajeto completo (ida + retorno ao depósito)
            if remaining_capacity >= city.demand and remaining_autonomy >= (dist_to_next + dist_back_to_depot):
                route.append(next_loc)
                remaining_capacity -= city.demand
                remaining_autonomy -= dist_to_next
                current_loc = next_loc
                unvisited.pop(0)  # Remove da fila de não visitados
            else:
                # O veículo não consegue atender esse hospital. Retorna ao depósito
                break

        # Se a rota visitou cidades além do depósito, adiciona o retorno ao depósito
        if len(route) > 1:
            route.append(depot_location)
            routes[v_idx] = route
        else:
            routes[v_idx] = [depot_location, depot_location]  # Rota vazia

    return routes, unvisited


def calculate_vrp_fitness(
    giant_tour: List[Tuple[float, float]],
    vehicles: List[Vehicle],
    depot_location: Tuple[float, float],
    city_map: dict
) -> float:
    """
    Calcula o fitness de um Giant Tour.
    O fitness representa o custo total (queremos MINIMIZAR):
    Custo = Distância Total de todos os veículos + Penalidade por hospitais não visitados + Penalidade por entregas críticas tardias.
    """
    routes, unvisited = decode_vrp_routes(giant_tour, vehicles, depot_location, city_map)

    total_cost = 0.0

    # 1. Custo da distância percorrida e prioridades
    for route in routes:
        if len(route) <= 2:
            continue  # Rota vazia (depot -> depot)

        current_loc = route[0]
        route_dist = 0.0

        # Percorre a rota calculando distâncias e penalidades de prioridade
        for idx in range(1, len(route)):
            next_loc = route[idx]
            step_dist = calculate_distance(current_loc, next_loc)
            route_dist += step_dist
            current_loc = next_loc

            # Se for um hospital (ou seja, não é a volta final ao depósito), verifica a prioridade
            if idx < len(route) - 1:
                city = city_map[next_loc]
                # Penalidade de atraso (distância percorrida até a entrega):
                # Se for CRITICAL, adiciona 5x a distância percorrida até aqui como custo
                # Se for URGENT, adiciona 2x a distância percorrida até aqui como custo
                if city.priority == Priority.CRITICAL:
                    total_cost += 5.0 * route_dist
                elif city.priority == Priority.URGENT:
                    total_cost += 2.0 * route_dist

        total_cost += route_dist  # Adiciona a distância física total percorrida pelo veículo

    # 2. Penalidade severa por hospitais não visitados
    total_cost += len(unvisited) * 1000.0

    return total_cost


def calculate_fitness(
    path: List[Tuple[float, float]],
    vehicles: List[Vehicle] = None,
    depot_location: Tuple[float, float] = None,
    city_map: dict = None
) -> float:
    """
    Calcula a aptidão da rota (fitness). Comporta-se como TSP simples se parâmetros VRP não forem informados.
    """
    if vehicles is None or depot_location is None or city_map is None:
        # Modo de compatibilidade do TSP original
        distance = 0
        n = len(path)
        for i in range(n):
            distance += calculate_distance(path[i], path[(i + 1) % n])
        return distance

    return calculate_vrp_fitness(path, vehicles, depot_location, city_map)


def order_crossover(
    parent1: List[Tuple[float, float]], parent2: List[Tuple[float, float]]
) -> List[Tuple[float, float]]:
    """
    Perform order crossover (OX) between two parent sequences to create a child sequence.

    Parameters:
    - parent1 (List[Tuple[float, float]]): The first parent sequence.
    - parent2 (List[Tuple[float, float]]): The second parent sequence.

    Returns:
    List[Tuple[float, float]]: The child sequence resulting from the order crossover.
    """
    length = len(parent1)

    # Choose two random indices for the crossover
    start_index = random.randint(0, length - 1)
    end_index = random.randint(start_index + 1, length)

    # Initialize the child with a copy of the substring from parent1
    child = parent1[start_index:end_index]

    # Fill in the remaining positions with genes from parent2
    remaining_positions = [
        i for i in range(length) if i < start_index or i >= end_index
    ]
    remaining_genes = [gene for gene in parent2 if gene not in child]

    for position, gene in zip(remaining_positions, remaining_genes):
        child.insert(position, gene)

    return child


### demonstration: crossover test code
# Example usage:
# parent1 = [(1, 1), (2, 2), (3, 3), (4,4), (5,5), (6, 6)]
# parent2 = [(6, 6), (5, 5), (4, 4), (3, 3),  (2, 2), (1, 1)]

# # parent1 = [1, 2, 3, 4, 5, 6]
# # parent2 = [6, 5, 4, 3, 2, 1]


# child = order_crossover(parent1, parent2)
# print("Parent 1:", [0, 1, 2, 3, 4, 5, 6, 7, 8])
# print("Parent 1:", parent1)
# print("Parent 2:", parent2)
# print("Child   :", child)


# # Example usage:
# population = generate_random_population(5, 10)

# print(calculate_fitness(population[0]))


# population = [(random.randint(0, 100), random.randint(0, 100))
#           for _ in range(3)]


# TODO: implement a mutation_intensity and invert pieces of code instead of just swamping two.
def mutate(
    solution: List[Tuple[float, float]], mutation_probability: float
) -> List[Tuple[float, float]]:
    """
    Mutate a solution by inverting a segment of the sequence with a given mutation probability.

    Parameters:
    - solution (List[int]): The solution sequence to be mutated.
    - mutation_probability (float): The probability of mutation for each individual in the solution.

    Returns:
    List[int]: The mutated solution sequence.
    """
    mutated_solution = copy.deepcopy(solution)

    # Check if mutation should occur
    if random.random() < mutation_probability:
        # Ensure there are at least two cities to perform a swap
        if len(solution) < 2:
            return solution

        # Select a random index (excluding the last index) for swapping
        index = random.randint(0, len(solution) - 2)

        # Swap the cities at the selected index and the next index
        mutated_solution[index], mutated_solution[index + 1] = (
            solution[index + 1],
            solution[index],
        )

    return mutated_solution


### Demonstration: mutation test code
# # Example usage:
# original_solution = [(1, 1), (2, 2), (3, 3), (4, 4)]
# mutation_probability = 1

# mutated_solution = mutate(original_solution, mutation_probability)
# print("Original Solution:", original_solution)
# print("Mutated Solution:", mutated_solution)


def sort_population(
    population: List[List[Tuple[float, float]]], fitness: List[float]
) -> Tuple[List[List[Tuple[float, float]]], List[float]]:
    """
    Sort a population based on fitness values.

    Parameters:
    - population (List[List[Tuple[float, float]]]): The population of solutions, where each solution is represented as a list.
    - fitness (List[float]): The corresponding fitness values for each solution in the population.

    Returns:
    Tuple[List[List[Tuple[float, float]]], List[float]]: A tuple containing the sorted population and corresponding sorted fitness values.
    """
    # Combine lists into pairs
    combined_lists = list(zip(population, fitness))

    # Sort based on the values of the fitness list
    sorted_combined_lists = sorted(combined_lists, key=lambda x: x[1])

    # Separate the sorted pairs back into individual lists
    sorted_population, sorted_fitness = zip(*sorted_combined_lists)

    return sorted_population, sorted_fitness


if __name__ == "__main__":
    N_CITIES = 12
    POPULATION_SIZE = 100
    N_GENERATIONS = 50
    MUTATION_PROBABILITY = 0.3

    # Configuração VRP de teste
    depot_loc = (-23.5505, -46.6333)
    
    # Criar cidades/hospitais com demandas e prioridades aleatórias
    hospitals = []
    cities_locations = []
    for i in range(N_CITIES):
        lat = random.uniform(-23.65, -23.45)
        lon = random.uniform(-46.75, -46.55)
        priority = random.choice([Priority.REGULAR, Priority.URGENT, Priority.CRITICAL])
        demand = random.uniform(1.0, 5.0)
        hospital = City(id=i+1, name=f"Hospital {i+1}", x=lat, y=lon, demand=demand, priority=priority)
        hospitals.append(hospital)
        cities_locations.append((lat, lon))
        
    city_map = {c.coordinates: c for c in hospitals}
    
    # Criar frota de veículos
    vehicles = [
        Vehicle(id=1, name="Veículo A", capacity=15.0, autonomy=100.0),
        Vehicle(id=2, name="Veículo B", capacity=15.0, autonomy=100.0),
        Vehicle(id=3, name="Veículo C", capacity=15.0, autonomy=100.0),
    ]

    # CREATE INITIAL POPULATION (permutação das localizações dos hospitais)
    population = generate_random_population(cities_locations, POPULATION_SIZE)

    # Lists to store best fitness and generation
    best_fitness_values = []
    best_solutions = []

    for generation in range(N_GENERATIONS):
        population_fitness = [
            calculate_fitness(individual, vehicles=vehicles, depot_location=depot_loc, city_map=city_map)
            for individual in population
        ]

        population, population_fitness = sort_population(population, population_fitness)

        best_fitness = population_fitness[0]
        best_solution = population[0]

        best_fitness_values.append(best_fitness)
        best_solutions.append(best_solution)

        print(f"Generation {generation}: Best VRP Fitness = {best_fitness:.2f}")

        new_population = [population[0]]  # Keep the best individual: ELITISM

        while len(new_population) < POPULATION_SIZE:
            # SELECTION (Top 10)
            parent1, parent2 = random.choices(population[:10], k=2)

            # CROSSOVER
            child1 = order_crossover(parent1, parent2)

            ## MUTATION
            child1 = mutate(child1, MUTATION_PROBABILITY)

            new_population.append(child1)

        population = new_population

    # Decodificar melhor rota para exibir detalhes
    routes, unvisited = decode_vrp_routes(population[0], vehicles, depot_loc, city_map)
    print("\n--- Resultado da Otimização VRP ---")
    print(f"Hospitais não visitados por falta de frota: {len(unvisited)}")
    for i, route in enumerate(routes):
        if len(route) > 2:
            visited_names = [city_map[p].name for p in route[1:-1]]
            print(f"Rota {vehicles[i].name}: Depósito -> {' -> '.join(visited_names)} -> Depósito")
        else:
            print(f"Rota {vehicles[i].name}: Inativo")
