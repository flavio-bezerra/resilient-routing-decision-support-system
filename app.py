import datetime
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import simpy
from src.data_gen import RealWorldVRPCreator
from src.optimization import RouteOptimizer
from src.simulation import WeatherService, LogisticsSimulator

# Page Config
st.set_page_config(page_title="IA de Roteamento Resiliente", layout="wide", page_icon="🚛")

# Title & Context
st.title("🚛 Sistema de Suporte à Decisão de Roteamento Resiliente")
st.markdown("""
**Projeto de Portfólio Sênior** | *Geografia Real & Simulação Climática Dinâmica*

Este sistema otimiza rotas logísticas em **São Paulo, Brasil**, considerando:
1.  **Geografia Real:** Clusters Gaussianos ao redor de hubs comerciais (Centro, Itaim, Guarulhos, Osasco).
2.  **Tempos de Viagem Realistas:** Matriz de distância Haversine com restrições de velocidade urbana.
3.  **Clima Dinâmico:** Simulação de chuva/tempestades impactando tempos de viagem e causando horas extras.
""")

with st.expander("ℹ️ Como funciona a Lógica do Projeto (Detalhes Técnicos)"):
    st.markdown("""
    ### 1. Geração de Demanda (Engenharia Geoespacial)
    *   **Clusters Realistas:** Os clientes não são gerados aleatoriamente. Utilizamos **distribuições Gaussianas** centradas em hubs reais (Centro, Itaim, Guarulhos, Osasco) para simular a densidade populacional de bairros.
    *   **Matriz de Tempo:** As distâncias são calculadas usando a **Fórmula de Haversine** (considerando a curvatura da Terra) e convertidas em tempo com base em uma velocidade média urbana (20 km/h) + atrito urbano.

    ### 2. Otimização (Pesquisa Operacional)
    *   **Solver:** Utilizamos o **Google OR-Tools** para resolver o *Vehicle Routing Problem with Time Windows (VRPTW)*.
    *   **Objetivo:** Minimizar o tempo total de viagem e o número de veículos utilizados.
    *   **Restrições:** Respeita estritamente a capacidade de carga, janelas de horário e o **Horário Final de Expediente**.

    ### 3. Simulação Estocástica (Weather Engine)
    *   Após o planejamento "ideal", a simulação testa a robustez das rotas na prática.
    *   A cada trecho da viagem, o clima é sorteado com base nas probabilidades configuradas:
        *   ☀️ **Ensolarado:** Tempo planejado (Fator 1.0x).
        *   🌧️ **Chuva Leve:** Trânsito lento (Fator 1.25x).
        *   ⛈️ **Tempestade:** Caos no trânsito (Fator 1.60x).

    ### 4. Métricas de Negócio
    *   **Fill Rate:** Taxa de ocupação média dos caminhões (Demanda da Rota / Capacidade).
    *   **Custo de Hora Extra:** Se os atrasos climáticos fizerem o veículo chegar após a janela permitida ou após o expediente, gera custo financeiro (R$ 2,50/min).
    """)

# Sidebar Controls
st.sidebar.header("⚙️ Configuração")

num_customers = st.sidebar.slider("Número de Clientes", min_value=20, max_value=300, value=50, step=10)
available_fleet = st.sidebar.slider("Frota Disponível (Sua Garagem)", min_value=1, max_value=50, value=15, step=1)
storm_prob = st.sidebar.slider("Probabilidade de Tempestade", 0.0, 0.5, 0.1)
rain_prob = st.sidebar.slider("Probabilidade de Chuva", 0.0, 0.5, 0.2)
start_time = st.sidebar.time_input("Horário de Início da Rota", value=datetime.time(8, 0))
end_time = st.sidebar.time_input("Horário Final de Expediente", value=datetime.time(18, 0))
service_time = st.sidebar.number_input("Tempo Médio de Descarga (min)", min_value=5, max_value=60, value=30, step=5)

# Calculate shift duration in minutes
dummy_date = datetime.date.today()
t1 = datetime.datetime.combine(dummy_date, start_time)
t2 = datetime.datetime.combine(dummy_date, end_time)
if t2 < t1:
    t2 += datetime.timedelta(days=1) # Handle overnight shifts if needed
shift_duration_minutes = int((t2 - t1).total_seconds() / 60)

if st.sidebar.button("🚀 Executar Simulação"):
    with st.spinner("Gerando Dados do Mundo Real..."):
        creator = RealWorldVRPCreator(num_customers=num_customers)
        # Pass a large number of vehicles (equal to num_customers) to the solver to ensure feasibility
        # The solver will minimize the number of vehicles used due to the fixed cost.
        # We use num_customers as a safe upper bound (worst case: 1 vehicle per customer).
        data_model = creator.create_data_model(max_time_minutes=shift_duration_minutes, service_time=service_time, num_vehicles=num_customers)
        locations = data_model['locations']
        
        # Convert locations to DataFrame for PyDeck
        df_locs = pd.DataFrame([
            {
                "id": loc.id, 
                "lat": loc.lat, 
                "lon": loc.lon, 
                "type": "Depósito" if loc.is_depot else "Cliente",
                "color": [255, 0, 0, 200] if loc.is_depot else [0, 128, 255, 140],
                "size": 200 if loc.is_depot else 80
            } 
            for loc in locations
        ])

    with st.spinner("Otimizando Rotas (OR-Tools) & Gerando Baseline Manual..."):
        optimizer = RouteOptimizer(data_model)
        routes_opt = optimizer.solve()
        routes_manual = optimizer.solve_greedy()
    
    with st.spinner("Simulando Impactos Climáticos (SimPy)..."):
        env_opt = simpy.Environment()
        env_manual = simpy.Environment()
        
        weather_service = WeatherService(storm_prob=storm_prob, rain_prob=rain_prob)
        
        # Simulação Otimizada
        simulator_opt = LogisticsSimulator(env_opt, data_model, routes_opt, weather_service)
        results_opt = simulator_opt.run()
        
        # Simulação Manual (Baseline)
        simulator_manual = LogisticsSimulator(env_manual, data_model, routes_manual, weather_service)
        results_manual = simulator_manual.run()
        
        # Converter minutos relativos para horário real
        if not results_opt.empty:
            ref_date = datetime.datetime.combine(datetime.date.today(), start_time)
            def minutes_to_time(minutes):
                return (ref_date + datetime.timedelta(minutes=minutes)).strftime("%H:%M")
            results_opt["Hora Chegada"] = results_opt["Hora Chegada"].apply(minutes_to_time)

    if not routes_opt:
        st.error("⚠️ Nenhuma rota viável encontrada! Tente aumentar a capacidade do veículo ou reduzir restrições.")
    else:
        # --- Dashboard de Decisão (Novos Cards) ---
        st.subheader("📋 Dashboard de Decisão")
        
        # Calcular métricas para os cards
        vehicles_needed = len([r for r in routes_opt if r])
        total_entregas = sum(len(r) for r in routes_opt)
        
        # Verificar Capacidade da Frota
        if vehicles_needed > available_fleet:
            st.error(f"🚨 **ALERTA DE CAPACIDADE:** Você precisa de **{vehicles_needed}** veículos, mas só tem **{available_fleet}** na garagem! Algumas entregas não poderão ser feitas.")
        else:
            st.success(f"✅ **FROTA SUFICIENTE:** Você usará **{vehicles_needed}** de **{available_fleet}** veículos disponíveis.")

        # Calcular Fill Rate (Taxa de Ocupação)
        fill_rates = []
        for i, route in enumerate(routes_opt):
            if not route: continue
            route_demand = sum(data_model['demands'][node] for node in route)
            capacity = data_model['vehicle_capacities'][i]
            fill_rates.append(route_demand / capacity)
        
        avg_fill_rate = np.mean(fill_rates) * 100 if fill_rates else 0
        
        # Distribuição do Clima (Tipos de Escolha / Cenário)
        clima_counts = results_opt["Clima"].value_counts()
        clima_dominante = clima_counts.idxmax() if not clima_counts.empty else "N/A"
        pct_tempestade = (len(results_opt[results_opt["Clima"] == "Tempestade Severa"]) / len(results_opt) * 100) if not results_opt.empty else 0
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Veículos Necessários", f"{vehicles_needed}", delta=f"{available_fleet - vehicles_needed} Livres" if vehicles_needed <= available_fleet else f"-{vehicles_needed - available_fleet} Faltantes", delta_color="normal" if vehicles_needed <= available_fleet else "inverse")
        c2.metric("Entregas Realizadas", f"{total_entregas} / {num_customers}")
        c3.metric("Taxa de Ocupação (Média)", f"{avg_fill_rate:.1f}%")
        c4.metric("Cenário Climático", f"{clima_dominante}")
        c5.metric("Exposição a Tempestades", f"{pct_tempestade:.1f}%")

        # --- Visualização ---
        st.subheader("📍 Visualização Geográfica das Rotas (São Paulo)")
        
        layers = []

        # Scatter Layer (Pontos)
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            df_locs,
            get_position=["lon", "lat"],
            get_color="color",
            get_radius="size",
            pickable=True,
            auto_highlight=True,
            stroked=True,
            filled=True,
            radius_min_pixels=5,
            radius_max_pixels=30,
        )
        layers.append(scatter_layer)
        
        # Path Layer (Rotas)
        path_data = []
        colors = [
            [255, 165, 0], # Laranja
            [0, 255, 0],   # Verde
            [255, 0, 255], # Magenta
            [0, 255, 255], # Ciano
            [255, 255, 0]  # Amarelo
        ]
        
        for i, route in enumerate(routes_opt):
            if not route: continue
            
            path_coords = []
            depot = locations[0]
            path_coords.append([depot.lon, depot.lat])
            
            for node_idx in route:
                loc = locations[node_idx]
                path_coords.append([loc.lon, loc.lat])
                
            path_data.append({
                "path": path_coords,
                "color": colors[i % len(colors)],
                "name": f"Veículo {i+1}"
            })
            
        path_layer = pdk.Layer(
            "PathLayer",
            path_data,
            get_path="path",
            get_color="color",
            width_scale=20,
            width_min_pixels=3,
            pickable=True
        )
        layers.append(path_layer)

        view_state = pdk.ViewState(
            latitude=-23.5505,
            longitude=-46.6333,
            zoom=10,
            pitch=40
        )

        r = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip={"text": "{type} ID: {id}"},
            map_style="mapbox://styles/mapbox/dark-v10"
        )
        st.pydeck_chart(r)

        # --- Análise Financeira & Saving ---
        st.subheader("💰 Análise Financeira & Saving Estimado")
        
        # Parâmetros de Custo
        CUSTO_OPERACIONAL_MIN = 1.00 # R$ por minuto (Combustível + Motorista)
        
        # 1. Cenário Otimizado (Realizado na Simulação)
        total_tempo_viagem_opt = results_opt["Tempo Real"].sum()
        custo_ops_otimizado = total_tempo_viagem_opt * CUSTO_OPERACIONAL_MIN
        custo_overtime_otimizado = results_opt["Custo Hora Extra"].sum()
        custo_total_otimizado = custo_ops_otimizado + custo_overtime_otimizado
        
        # 2. Cenário Manual (Simulado via Nearest Neighbor)
        total_tempo_viagem_manual = results_manual["Tempo Real"].sum()
        custo_ops_manual = total_tempo_viagem_manual * CUSTO_OPERACIONAL_MIN
        custo_overtime_manual = results_manual["Custo Hora Extra"].sum()
        custo_total_manual = custo_ops_manual + custo_overtime_manual
        
        # 3. Saving
        saving_total = custo_total_manual - custo_total_otimizado
        saving_pct = (saving_total / custo_total_manual * 100) if custo_total_manual > 0 else 0
        
        # Exibir Métricas Financeiras
        f1, f2, f3 = st.columns(3)
        f1.metric("Custo Total (Otimizado)", f"R$ {custo_total_otimizado:,.2f}", delta=f"R$ {saving_total:,.2f} (Saving)")
        f2.metric("Custo Total (Manual)", f"R$ {custo_total_manual:,.2f}")
        f3.metric("Saving Relativo", f"{saving_pct:.1f}%", delta="Eficiência")

        # 2. Resultados da Simulação
        st.subheader("📊 Resultados Detalhados da Simulação (Otimizada)")
        
        col1, col2, col3 = st.columns(3)
        
        avg_delay = results_opt["Atraso"].mean()
        storm_count = len(results_opt[results_opt["Clima"] == "Tempestade Severa"])
        
        col1.metric("Custo Hora Extra (Otimizado)", f"R$ {custo_overtime_otimizado:,.2f}")
        col2.metric("Atraso Médio por Viagem", f"{avg_delay:.1f} min")
        col3.metric("Eventos de Tempestade", f"{storm_count}")

        with st.expander("ℹ️ Racional de Cálculo das Métricas e Saving"):
            st.markdown("""
            **Racional Financeiro (Saving):**
            O *Saving* é calculado comparando duas simulações paralelas:
            
            1.  **Cenário Otimizado (IA):** Rotas geradas pelo algoritmo **OR-Tools (VRPTW)**, que considera janelas de tempo e minimiza a distância global.
            2.  **Cenário Manual (Baseline):** Rotas geradas por um algoritmo **Guloso (Vizinho Mais Próximo)**, simulando um planejador humano que apenas escolhe o próximo ponto mais perto, sem otimização global.
            
            Ambos os cenários são submetidos à **mesma simulação climática** (probabilidades de chuva/tempestade) para garantir uma comparação justa.
            
            *   **Custo Operacional:** R$ 1,00 por minuto de viagem (Combustível + Mão de obra).
            *   **Fórmula do Saving:** `Custo Total Manual - Custo Total Otimizado`.
            
            **Entenda as colunas da tabela detalhada:**
            
            1.  **Tempo Base:** Tempo de viagem ideal (sem trânsito/clima).
            2.  **Tempo Real:** Tempo efetivo considerando o clima.
            3.  **Custo Hora Extra:** Penalidade por atraso na janela de tempo (R$ 2,50/min).
            """)

        st.dataframe(results_opt, use_container_width=True)

else:
    st.info("Ajuste os parâmetros na barra lateral e clique em 'Executar Simulação' para iniciar.")
