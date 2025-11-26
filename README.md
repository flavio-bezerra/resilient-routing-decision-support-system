# 🚛 Sistema de Suporte à Decisão de Roteamento Resiliente

![Streamlit App Preview](streamlit_video.gif)

## 📌 Visão Geral

Este projeto é um sistema de suporte à decisão de alta fidelidade projetado para operações logísticas em **São Paulo, Brasil**. Diferente de solucionadores VRP (Vehicle Routing Problem) padrão, este sistema integra **restrições geográficas do mundo real**, **tempos de serviço realistas** e um **motor climático estocástico** para simular e otimizar entregas de última milha sob incerteza.

Ele demonstra capacidades avançadas em:

- **Pesquisa Operacional:** Resolução de CVRP com Janelas de Tempo (VRPTW) usando Google OR-Tools.
- **Simulação:** Simulação de eventos discretos (SimPy) para modelar impactos climáticos nos tempos de viagem e custos operacionais.
- **Engenharia Geoespacial:** Geração de dados sintéticos baseada em clusters urbanos reais (distribuição Gaussiana) e cálculos de distância Haversine com fatores de atrito urbano.
- **Análise Financeira:** Comparação direta de custos e eficiência (Saving) entre o modelo otimizado por IA e um baseline manual (algoritmo guloso).

## 🏗 Arquitetura

O projeto segue uma **Arquitetura Limpa** modular:

1.  **`src/data_gen.py`**:

    - Gera localizações de clientes realistas usando clusters Gaussianos ao redor de hubs principais de SP (Centro, Itaim, Guarulhos, Osasco).
    - Calcula uma **Matriz de Distância Haversine** (metros) e a converte para tempos de viagem baseados em velocidades de tráfego urbano realistas (**20 km/h**) + **Atrito Urbano** (3 min/viagem).
    - Gera janelas de tempo viáveis considerando o tempo de deslocamento e o **Tempo de Descarga** configurável.

2.  **`src/optimization.py`**:

    - Implementa o **RouteOptimizer** usando Google OR-Tools.
    - Resolve para o tempo mínimo de viagem respeitando a capacidade do veículo e as janelas de tempo do cliente.
    - **Gestão de Frota Inteligente:** Otimiza o número de veículos necessários, minimizando custos fixos.
    - **Resiliência:** Permite rotas com horas extras (soft constraints) para garantir que todos os clientes sejam atendidos, mesmo em cenários difíceis.

3.  **`src/simulation.py`**:

    - **Motor Climático**: Simula estados climáticos dinâmicos (Ensolarado, Chuva Leve, Tempestade Severa) com probabilidades configuráveis.
    - **Simulador Logístico**: Usa SimPy para executar as rotas planejadas. Aplica fatores de penalidade aos tempos de viagem com base no clima ativo (ex: Tempestade = +60% tempo de viagem) e calcula os custos de hora extra resultantes.
    - Considera tempos de descarga reais em cada cliente.

4.  **`app.py`**:
    - A interface frontend construída com **Streamlit**.
    - Fornece controles para parâmetros de simulação (número de clientes, frota disponível, probabilidades climáticas, horários de turno).
    - **Dashboard de Decisão:** Exibe métricas críticas como Veículos Necessários vs. Disponíveis, Fill Rate e Cenário Climático.
    - **Análise Financeira:** Calcula o "Saving" (economia) gerado pela IA em comparação com o planejamento manual.
    - Visualiza rotas em um mapa interativo de São Paulo usando **PyDeck**.

## 🚀 Como Executar

### Opção 1: Execução Local

1.  **Clone o repositório:**

    ```bash
    git clone https://github.com/seu-usuario/resilient-routing-dss.git
    cd resilient-routing-dss
    ```

2.  **Instale as dependências:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute a aplicação:**
    ```bash
    streamlit run app.py
    ```

## 📊 Principais Recursos

- **Geografia do Mundo Real:** Chega de pontos aleatórios no oceano. Clientes são gerados em bairros realistas de São Paulo.
- **Parâmetros Operacionais Reais:** Velocidade urbana de 20km/h, tempo de descarga configurável e gestão de turnos de trabalho.
- **Análise de Impacto Climático:** Veja como um aumento de 10% na probabilidade de tempestade afeta seus custos de hora extra e atrasos.
- **Comparação Financeira (Saving):** Demonstração clara do ROI da otimização, comparando custos operacionais e horas extras contra um cenário manual.
- **Gestão de Capacidade:** Alertas automáticos quando a frota disponível não é suficiente para a demanda.
