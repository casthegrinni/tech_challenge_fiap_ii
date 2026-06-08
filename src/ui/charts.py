import matplotlib.pyplot as plt
import folium
import altair as alt
import pandas as pd
from src.domain.city import Priority

def plot_fitness_curve(best_fitness_values):
    """
    Gera o gráfico de convergência (Evolução do Fitness).
    """
    fig_fitness, ax_fitness = plt.subplots(figsize=(5, 4))
    ax_fitness.plot(best_fitness_values, color="red", linewidth=2)
    ax_fitness.set_title("Evolução do Fitness")
    ax_fitness.set_xlabel("Geração")
    ax_fitness.set_ylabel("Distância")
    
    # Fechar a figura internamente para liberar memória (o Streamlit a renderiza de qualquer forma)
    plt.close(fig_fitness)
    return fig_fitness

def plot_route_map(cities_locations, best_solution):
    """
    Gera o mapa visual das cidades e a melhor rota encontrada.
    """
    fig_map, ax_map = plt.subplots(figsize=(5, 4))

    # Desenha as cidades (Hospitais)
    xs, ys = zip(*cities_locations)
    ax_map.scatter(xs, ys, color="blue", s=50, label="Hospitais")

    # Desenha a rota (conectando a última à primeira cidade no final)
    path = best_solution + [best_solution[0]]
    px, py = zip(*path)
    ax_map.plot(px, py, color="green", linestyle="-", linewidth=1, alpha=0.6)

    ax_map.set_title("Melhor Rota Encontrada")
    
    plt.close(fig_map)
    return fig_map

def plot_folium_route(cities_locations, decoded_routes, depot_location, city_map):
    """
    Gera o mapa interativo do Folium com as rotas de cada veículo e hospitais.
    """
    m = folium.Map(location=[depot_location[0], depot_location[1]], zoom_start=12, tiles="OpenStreetMap")

    # Adicionar marcador do depósito (Verde)
    folium.Marker(
        location=[depot_location[0], depot_location[1]],
        popup="Depósito Central",
        tooltip="Depósito Central",
        icon=folium.Icon(color="green", icon="home", prefix="glyphicon")
    ).add_to(m)

    # Adicionar marcadores dos hospitais com cores por prioridade
    # Vermelho para CRITICAL, Laranja para URGENT, Azul para REGULAR
    for loc in cities_locations:
        city = city_map[loc]
        
        if city.priority == Priority.CRITICAL:
            color = "red"
            icon = "exclamation-sign"
            prio_label = "Crítica"
        elif city.priority == Priority.URGENT:
            color = "orange"
            icon = "warning-sign"
            prio_label = "Urgente"
        else:
            color = "blue"
            icon = "plus-sign"
            prio_label = "Regular"
            
        tooltip_text = f"<b>{city.name}</b><br>Prioridade: {prio_label}<br>Demanda: {city.demand:.1f} kg"
        
        folium.Marker(
            location=[loc[0], loc[1]],
            popup=tooltip_text,
            tooltip=city.name,
            icon=folium.Icon(color=color, icon=icon, prefix="glyphicon")
        ).add_to(m)

    # Cores distintas para as linhas de cada veículo
    route_colors = ["#FF3B30", "#34C759", "#007AFF", "#AF52DE", "#FF9500", "#5856D6"]
    
    for v_idx, route in enumerate(decoded_routes):
        if len(route) <= 2:
            continue
            
        color = route_colors[v_idx % len(route_colors)]
        
        folium.PolyLine(
            locations=route,
            color=color,
            weight=4,
            opacity=0.8,
            tooltip=f"Rota Veículo {v_idx+1}"
        ).add_to(m)

    return m

def plot_altair_route(cities_locations, decoded_routes, depot_location, city_map, candidate_routes=None):
    """
    Gera o mapa de rotas interativo e nativo usando Altair, adaptado para múltiplas rotas de veículos (VRP).
    """
    # 1. Preparar dados dos hospitais + Depósito
    hospitals_data = []
    # Adicionar depósito
    hospitals_data.append({
        'Latitude': depot_location[0],
        'Longitude': depot_location[1],
        'Nome': 'Depósito Central',
        'Prioridade': 'Depósito',
        'Demanda (kg)': 0.0
    })
    # Adicionar hospitais
    for loc in cities_locations:
        city = city_map[loc]
        priority_label = {3: 'Crítica', 2: 'Urgente', 1: 'Regular'}[city.priority]
        hospitals_data.append({
            'Latitude': loc[0],
            'Longitude': loc[1],
            'Nome': city.name,
            'Prioridade': priority_label,
            'Demanda (kg)': city.demand
        })
        
    df_points = pd.DataFrame(hospitals_data)

    # 2. Preparar dados das rotas dos veículos
    route_data = []
    for v_idx, route in enumerate(decoded_routes):
        if len(route) <= 2:
            continue
        for order_idx, p in enumerate(route):
            route_data.append({
                'Latitude': p[0],
                'Longitude': p[1],
                'Ordem': order_idx,
                'Veículo': f"Veículo {v_idx+1}"
            })
            
    df_routes = pd.DataFrame(route_data) if route_data else pd.DataFrame(columns=['Latitude', 'Longitude', 'Ordem', 'Veículo'])

    # Configurar cores para prioridades
    priority_color_scale = alt.Scale(
        domain=['Depósito', 'Crítica', 'Urgente', 'Regular'],
        range=['#2CA02C', '#FF4B4B', '#FFA500', '#1F77B4']
    )

    # Gráfico de dispersão (Hospitais)
    points = alt.Chart(df_points).mark_circle(size=140, stroke='white', strokeWidth=1).encode(
        x=alt.X('Longitude:Q', scale=alt.Scale(zero=False)),
        y=alt.Y('Latitude:Q', scale=alt.Scale(zero=False)),
        color=alt.Color('Prioridade:N', scale=priority_color_scale, legend=alt.Legend(title="Legenda")),
        tooltip=['Nome', 'Prioridade', 'Demanda (kg)', 'Latitude', 'Longitude']
    )

    # Gráfico de linhas (Rotas dos Veículos)
    lines = alt.Chart(df_routes).mark_line(strokeWidth=3.0, opacity=0.9).encode(
        x=alt.X('Longitude:Q', scale=alt.Scale(zero=False)),
        y=alt.Y('Latitude:Q', scale=alt.Scale(zero=False)),
        order='Ordem:Q',
        color=alt.Color('Veículo:N', scale=alt.Scale(scheme='category10')),
        detail='Veículo:N'
    )

    # Gráfico das rotas candidatas (opcional, desenhado ao fundo)
    df_candidates_list = []
    if candidate_routes:
        for c_idx, c_routes in enumerate(candidate_routes):
            for v_idx, route in enumerate(c_routes):
                if len(route) <= 2:
                    continue
                for order_idx, p in enumerate(route):
                    df_candidates_list.append({
                        'Latitude': p[0],
                        'Longitude': p[1],
                        'Ordem': order_idx,
                        'Route_ID': f"Cand_{c_idx}_V_{v_idx}"
                    })

    if df_candidates_list:
        df_candidates = pd.DataFrame(df_candidates_list)
        candidate_lines = alt.Chart(df_candidates).mark_line(
            color='#CCCCCC',
            strokeWidth=1.0,
            opacity=0.35
        ).encode(
            x=alt.X('Longitude:Q', scale=alt.Scale(zero=False)),
            y=alt.Y('Latitude:Q', scale=alt.Scale(zero=False)),
            order='Ordem:Q',
            detail='Route_ID:N'
        )
        chart = (candidate_lines + lines + points).properties(
            title="Rotas de Entrega Otimizadas em Tempo Real",
            height=350
        ).interactive()
    else:
        chart = (lines + points).properties(
            title="Rotas de Entrega Otimizadas em Tempo Real",
            height=350
        ).interactive()

    return chart
