import random

import streamlit as st
from streamlit_folium import folium_static

from src.domain.city import City, Priority
from src.domain.vehicle import Vehicle
from src.engine.genetic_algorithm import (
    calculate_fitness,
    generate_random_population,
    mutate,
    order_crossover,
    sort_population,
    decode_vrp_routes,
    calculate_distance,
)
from src.ui.charts import plot_fitness_curve, plot_route_map, plot_folium_route, plot_altair_route

st.set_page_config(page_title="TSP Optimizer", layout="wide")

st.title("🏥 Otimização de Rotas Médicas (TSP Base)")

# Configurações na barra lateral
st.sidebar.header("⚙️ Parâmetros do Algoritmo Genético")
POPULATION_SIZE = st.sidebar.slider("Tamanho da População", 10, 500, 100)
N_GENERATIONS = st.sidebar.slider("Número de Gerações", 10, 1000, 150)
MUTATION_PROBABILITY = st.sidebar.slider("Probabilidade de Mutação", 0.0, 1.0, 0.3)
UPDATE_INTERVAL = st.sidebar.slider("Intervalo de Atualização (Gerações)", 1, 100, 10)

st.sidebar.header("🚚 Configurações da Frota (VRP)")
N_VEHICLES = st.sidebar.slider("Número de Veículos", 1, 10, 3)
VEHICLE_CAPACITY = st.sidebar.slider("Capacidade do Veículo (kg)", 10, 100, 30)
VEHICLE_AUTONOMY = st.sidebar.slider("Autonomia do Veículo (km)", 20, 500, 150)

st.sidebar.header("🏥 Configurações do Problema")
N_CITIES = st.sidebar.slider("Número de Hospitais", 5, 50, 15)

if st.button("🚀 Iniciar Otimização"):
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Criar colunas para os dois gráficos
    col1, col2 = st.columns(2)
    chart_placeholder = col1.empty()
    map_placeholder = col2.empty()

    # 1. Geração de Hospitais na região de São Paulo com Demanda e Prioridade
    depot_location = (-23.5505, -46.6333)
    hospitals = []
    for i in range(N_CITIES):
        # 70% REGULAR, 20% URGENT, 10% CRITICAL
        p_val = random.random()
        if p_val < 0.7:
            priority = Priority.REGULAR
        elif p_val < 0.9:
            priority = Priority.URGENT
        else:
            priority = Priority.CRITICAL
            
        demand = random.uniform(2.0, 8.0) # Demanda entre 2kg e 8kg
        
        hospitals.append(
            City(
                id=i+1,
                name=f"Hospital {i+1}",
                x=random.uniform(-23.65, -23.45), # Latitude
                y=random.uniform(-46.75, -46.55), # Longitude
                demand=round(demand, 1),
                priority=priority
            )
        )
    cities_locations = [h.coordinates for h in hospitals]
    city_map = {h.coordinates: h for h in hospitals}

    # 2. Inicialização da Frota de Veículos (VRP)
    vehicles = [
        Vehicle(
            id=i,
            name=f"Veículo {i+1}",
            capacity=VEHICLE_CAPACITY,
            autonomy=VEHICLE_AUTONOMY
        )
        for i in range(N_VEHICLES)
    ]

    # 3. Inicialização do Algoritmo Genético (permutações dos hospitais)
    population = generate_random_population(cities_locations, POPULATION_SIZE)

    best_fitness_values = []

    # 4. Loop Principal da Evolução
    for generation in range(N_GENERATIONS):
        # Avaliação com VRP
        population_fitness = [
            calculate_fitness(individual, vehicles=vehicles, depot_location=depot_location, city_map=city_map)
            for individual in population
        ]
        population, population_fitness = sort_population(population, population_fitness)

        # Registro do melhor indivíduo
        best_fitness = population_fitness[0]
        best_solution = population[0]
        best_fitness_values.append(best_fitness)

        # Nova Geração (Elitismo)
        new_population = [population[0]]

        while len(new_population) < POPULATION_SIZE:
            # Seleção (Roleta/Torneio simplificado pegando os top 10)
            parent1, parent2 = random.choices(population[:10], k=2)

            # Crossover
            child1 = order_crossover(parent1, parent2)

            # Mutação
            child1 = mutate(child1, MUTATION_PROBABILITY)

            new_population.append(child1)

        population = new_population

        # Atualização da Interface Visual
        if generation % UPDATE_INTERVAL == 0 or generation == N_GENERATIONS - 1:
            progress_bar.progress((generation + 1) / N_GENERATIONS)
            status_text.text(
                f"Geração {generation + 1}/{N_GENERATIONS} - Melhor Custo: {best_fitness:.2f}"
            )

            # 1. Gráfico de convergência usando st.line_chart para performance em tempo real
            chart_placeholder.line_chart(best_fitness_values)

            # 2. Gráfico interativo de rotas nativo usando Altair (com candidatos em cinza no fundo)
            best_decoded, _ = decode_vrp_routes(best_solution, vehicles, depot_location, city_map)
            
            candidates_decoded = []
            if len(population) > 1:
                num_candidates = min(5, len(population) - 1)
                for cand in random.sample(population[1:], num_candidates):
                    cand_decoded, _ = decode_vrp_routes(cand, vehicles, depot_location, city_map)
                    candidates_decoded.append(cand_decoded)

            altair_chart = plot_altair_route(cities_locations, best_decoded, depot_location, city_map, candidate_routes=candidates_decoded)
            map_placeholder.altair_chart(altair_chart, use_container_width=True)

    # Decodificar rota campeã final
    final_routes, final_unvisited = decode_vrp_routes(best_solution, vehicles, depot_location, city_map)

    st.success(
        f"Otimização concluída! Melhor custo final obtido: {best_fitness_values[-1]:.2f}"
    )

    # 5. Relatório Detalhado de Utilização da Frota
    st.subheader("📊 Relatório de Utilização da Frota")
    report_data = []
    for idx, route in enumerate(final_routes):
        if len(route) > 2:
            cargo = sum(city_map[p].demand for p in route[1:-1])
            dist = 0.0
            for k in range(len(route) - 1):
                dist += calculate_distance(route[k], route[k+1])
                
            report_data.append({
                "Veículo": vehicles[idx].name,
                "Status": "Ativo",
                "Hospitais Visitados": len(route) - 2,
                "Carga Entregue (kg)": f"{cargo:.1f} / {VEHICLE_CAPACITY} kg ({cargo/VEHICLE_CAPACITY*100:.1f}%)",
                "Distância Percorrida (km)": f"{dist:.1f} / {VEHICLE_AUTONOMY} km ({dist/VEHICLE_AUTONOMY*100:.1f}%)"
            })
        else:
            report_data.append({
                "Veículo": vehicles[idx].name,
                "Status": "Ocioso",
                "Hospitais Visitados": 0,
                "Carga Entregue (kg)": "0.0 kg",
                "Distância Percorrida (km)": "0.0 km"
            })
            
    st.table(report_data)
    
    if final_unvisited:
        st.warning(f"⚠️ Atenção: {len(final_unvisited)} hospitais não puderam ser atendidos pela frota devido a limites de carga ou autonomia!")
        unvisited_names = [city_map[p].name for p in final_unvisited]
        st.write(f"Hospitais não atendidos: {', '.join(unvisited_names)}")
    else:
        st.info("✅ Todos os hospitais foram atendidos com sucesso pela frota disponível!")

    # 6. Mapa interativo do Folium renderizado após a conclusão do algoritmo
    st.subheader("🗺️ Mapa Interativo de Entrega (Resultado Final)")
    fig_folium = plot_folium_route(cities_locations, final_routes, depot_location, city_map)
    folium_static(fig_folium, width=1000, height=500)
