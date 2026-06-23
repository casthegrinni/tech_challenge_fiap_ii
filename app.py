import random
import json
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
from src.services.llm_service import configure_llm, generate_driver_instructions, generate_efficiency_report, chat_with_data

st.set_page_config(page_title="TSP Optimizer", layout="wide")

st.title("🏥 Otimização de Rotas Médicas (TSP Base)")

# Configurações na barra lateral
# Tenta carregar a API Key do arquivo de segredos (.streamlit/secrets.toml)
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    GEMINI_API_KEY = None

if GEMINI_API_KEY:
    configure_llm(GEMINI_API_KEY)

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
    st.session_state["run_optimization"] = True
    st.session_state["optimization_done"] = False

if st.session_state.get("run_optimization", False):
    
    if not st.session_state.get("optimization_done", False):
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Criar colunas para os dois gráficos
        col1, col2 = st.columns(2)
        chart_placeholder = col1.empty()
        map_placeholder = col2.empty()

        # 1. Geração de Hospitais
        depot_location = (-23.5505, -46.6333)
        hospitals = []
        for i in range(N_CITIES):
            p_val = random.random()
            if p_val < 0.7:
                priority = Priority.REGULAR
            elif p_val < 0.9:
                priority = Priority.URGENT
            else:
                priority = Priority.CRITICAL
                
            demand = random.uniform(2.0, 8.0)
            
            hospitals.append(
                City(
                    id=i+1,
                    name=f"Hospital {i+1}",
                    x=random.uniform(-23.65, -23.45),
                    y=random.uniform(-46.75, -46.55),
                    demand=round(demand, 1),
                    priority=priority
                )
            )
        cities_locations = [h.coordinates for h in hospitals]
        city_map = {h.coordinates: h for h in hospitals}

        # 2. Inicialização da Frota
        vehicles = [
            Vehicle(id=i, name=f"Veículo {i+1}", capacity=VEHICLE_CAPACITY, autonomy=VEHICLE_AUTONOMY)
            for i in range(N_VEHICLES)
        ]

        population = generate_random_population(cities_locations, POPULATION_SIZE)
        best_fitness_values = []

        # 4. Loop Principal
        for generation in range(N_GENERATIONS):
            population_fitness = [
                calculate_fitness(individual, vehicles=vehicles, depot_location=depot_location, city_map=city_map)
                for individual in population
            ]
            population, population_fitness = sort_population(population, population_fitness)

            best_fitness = population_fitness[0]
            best_solution = population[0]
            best_fitness_values.append(best_fitness)

            new_population = [population[0]]

            while len(new_population) < POPULATION_SIZE:
                parent1, parent2 = random.choices(population[:10], k=2)
                child1 = order_crossover(parent1, parent2)
                child1 = mutate(child1, MUTATION_PROBABILITY)
                new_population.append(child1)

            population = new_population

            if generation % UPDATE_INTERVAL == 0 or generation == N_GENERATIONS - 1:
                progress_bar.progress((generation + 1) / N_GENERATIONS)
                status_text.text(f"Geração {generation + 1}/{N_GENERATIONS} - Melhor Custo: {best_fitness:.2f}")

                chart_placeholder.line_chart(best_fitness_values)

                best_decoded, _ = decode_vrp_routes(best_solution, vehicles, depot_location, city_map)
                candidates_decoded = []
                if len(population) > 1:
                    num_candidates = min(5, len(population) - 1)
                    for cand in random.sample(population[1:], num_candidates):
                        cand_decoded, _ = decode_vrp_routes(cand, vehicles, depot_location, city_map)
                        candidates_decoded.append(cand_decoded)

                altair_chart = plot_altair_route(cities_locations, best_decoded, depot_location, city_map, candidate_routes=candidates_decoded)
                map_placeholder.altair_chart(altair_chart, use_container_width=True)

        final_routes, final_unvisited = decode_vrp_routes(best_solution, vehicles, depot_location, city_map)
        
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

        unvisited_names = [city_map[p].name for p in final_unvisited] if final_unvisited else []

        st.session_state["opt_results"] = {
            "best_fitness_values": best_fitness_values,
            "final_routes": final_routes,
            "final_unvisited": final_unvisited,
            "report_data": report_data,
            "unvisited_names": unvisited_names,
            "cities_locations": cities_locations,
            "depot_location": depot_location,
            "city_map": city_map,
            "vehicles": vehicles
        }
        st.session_state["optimization_done"] = True

    # RENDER SECTION
    res = st.session_state["opt_results"]
    best_fitness_values = res["best_fitness_values"]
    final_routes = res["final_routes"]
    final_unvisited = res["final_unvisited"]
    report_data = res["report_data"]
    unvisited_names = res["unvisited_names"]
    cities_locations = res["cities_locations"]
    depot_location = res["depot_location"]
    city_map = res["city_map"]
    vehicles = res["vehicles"]

    st.success(f"Otimização concluída! Melhor custo final obtido: {best_fitness_values[-1]:.2f}")

    st.subheader("📊 Relatório de Utilização da Frota")
    st.table(report_data)

    if final_unvisited:
        st.warning(f"⚠️ Atenção: {len(final_unvisited)} hospitais não puderam ser atendidos pela frota devido a limites de carga ou autonomia!")
        st.write(f"Hospitais não atendidos: {', '.join(unvisited_names)}")
    else:
        st.info("✅ Todos os hospitais foram atendidos com sucesso pela frota disponível!")

    st.subheader("🗺️ Mapa Interativo de Entrega (Resultado Final)")
    fig_folium = plot_folium_route(cities_locations, final_routes, depot_location, city_map)
    folium_static(fig_folium, width=1000, height=500)

    # 7. Integração com LLMs
    st.divider()
    st.header("🤖 Assistente de IA (Google Gemini)")

    if not GEMINI_API_KEY:
        st.warning("⚠️ Insira sua Gemini API Key no arquivo `.streamlit/secrets.toml` para habilitar as funcionalidades de Inteligência Artificial.")
    else:
        tab1, tab2, tab3 = st.tabs(["📝 Instruções para Motoristas", "📊 Relatório de Eficiência", "💬 Chatbot Logístico"])
        
        with tab1:
            st.markdown("Gere instruções detalhadas em linguagem natural para as equipes de entrega baseadas nas rotas acima.")
            if st.button("Gerar Instruções"):
                with st.spinner("A IA está escrevendo o roteiro..."):
                    instrucoes = generate_driver_instructions(final_routes, city_map, vehicles)
                    st.write(instrucoes)
                    
        with tab2:
            st.markdown("Crie um relatório executivo analisando a eficiência das rotas e sugerindo melhorias.")
            if st.button("Gerar Relatório de Eficiência"):
                with st.spinner("Analisando dados logísticos..."):
                    relatorio = generate_efficiency_report(report_data, unvisited_names)
                    st.write(relatorio)
                    
        with tab3:
            st.markdown("Faça perguntas sobre os resultados do roteamento atual (Ex: 'Qual veículo rodou mais?' ou 'Qual a prioridade do Hospital 2?').")
            
            context_data = {
                "relatorio_frota": report_data,
                "hospitais_nao_visitados": unvisited_names,
                "custo_total_otimizado": round(best_fitness_values[-1], 2)
            }
            
            user_q = st.text_input("Pergunte algo sobre a frota (Pressione Enter para enviar):")
            if user_q:
                st.markdown(f"**👤 Você:** {user_q}")
                with st.spinner("Consultando dados..."):
                    resposta_ia = chat_with_data(json.dumps(context_data, ensure_ascii=False), user_q)
                    st.success(f"**🤖 Gemini:** {resposta_ia}")
