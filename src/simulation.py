import simpy
import random
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class WeatherState:
    name: str
    travel_time_factor: float

class WeatherService:
    """
    Manages weather simulation and its impact on logistics.
    """
    STATES = {
        'Ensolarado': WeatherState('Ensolarado', 1.0),
        'Chuva Leve': WeatherState('Chuva Leve', 1.25),
        'Tempestade Severa': WeatherState('Tempestade Severa', 1.60)
    }

    def __init__(self, storm_prob: float = 0.1, rain_prob: float = 0.2):
        self.storm_prob = storm_prob
        self.rain_prob = rain_prob
        self.sunny_prob = 1.0 - (storm_prob + rain_prob)
        
        if self.sunny_prob < 0:
            raise ValueError("A soma das probabilidades não pode exceder 1.0")

    def get_current_weather(self) -> WeatherState:
        """
        Determina aleatoriamente o clima atual com base nas probabilidades.
        """
        r = random.random()
        if r < self.storm_prob:
            return self.STATES['Tempestade Severa']
        elif r < self.storm_prob + self.rain_prob:
            return self.STATES['Chuva Leve']
        else:
            return self.STATES['Ensolarado']

class LogisticsSimulator:
    """
    Simula a execução do roteamento de veículos usando SimPy, considerando condições climáticas dinâmicas.
    """
    
    def __init__(self, env: simpy.Environment, data_model: Dict[str, Any], routes: List[List[int]], weather_service: WeatherService):
        self.env = env
        self.data = data_model
        self.routes = routes
        self.weather_service = weather_service
        self.logs = []
        self.total_overtime_cost = 0.0
        self.OVERTIME_RATE_PER_MIN = 2.5 # Unidade monetária por minuto

    def drive(self, vehicle_id: int, route: List[int]):
        """
        Processo de um único veículo percorrendo sua rota.
        """
        current_node = self.data['depot']
        current_time = 0 # Relativo ao início do dia
        
        for next_node in route:
            # 1. Determinar Tempo de Viagem (Base)
            base_travel_time = self.data['time_matrix'][current_node][next_node]
            
            # 2. Verificar Clima
            weather = self.weather_service.get_current_weather()
            
            # 3. Aplicar Fator Climático
            actual_travel_time = base_travel_time * weather.travel_time_factor
            
            # 4. Simular Viagem
            yield self.env.timeout(actual_travel_time)
            current_time = self.env.now
            
            # 5. Registrar Evento
            self.logs.append({
                "Veículo": vehicle_id,
                "De": current_node,
                "Para": next_node,
                "Clima": weather.name,
                "Tempo Base": base_travel_time,
                "Tempo Real": round(actual_travel_time, 2),
                "Hora Chegada": round(current_time, 2),
                "Atraso": round(actual_travel_time - base_travel_time, 2)
            })
            
            # 6. Verificar Janelas de Tempo & Hora Extra
            _, latest_allowed = self.data['time_windows'][next_node]
            if current_time > latest_allowed:
                overtime = current_time - latest_allowed
                cost = overtime * self.OVERTIME_RATE_PER_MIN
                self.total_overtime_cost += cost
                self.logs[-1]["Custo Hora Extra"] = round(cost, 2)
            else:
                self.logs[-1]["Custo Hora Extra"] = 0.0

            # 7. Tempo de Serviço (Dinâmico)
            service_time = self.data.get('service_time', 10)
            yield self.env.timeout(service_time)
            current_node = next_node

        # --- Retorno ao Depósito ---
        # Após o último cliente, o veículo deve voltar ao depósito
        depot = self.data['depot']
        base_travel_time = self.data['time_matrix'][current_node][depot]
        weather = self.weather_service.get_current_weather()
        actual_travel_time = base_travel_time * weather.travel_time_factor
        
        yield self.env.timeout(actual_travel_time)
        current_time = self.env.now
        
        self.logs.append({
            "Veículo": vehicle_id,
            "De": current_node,
            "Para": depot,
            "Clima": weather.name,
            "Tempo Base": base_travel_time,
            "Tempo Real": round(actual_travel_time, 2),
            "Hora Chegada": round(current_time, 2),
            "Atraso": round(actual_travel_time - base_travel_time, 2)
        })
        
        # Verificar se estourou o expediente (max_time_minutes)
        max_time = self.data.get('max_time_minutes', 480)
        if current_time > max_time:
            overtime = current_time - max_time
            cost = overtime * self.OVERTIME_RATE_PER_MIN
            self.total_overtime_cost += cost
            self.logs[-1]["Custo Hora Extra"] = round(cost, 2)
        else:
            self.logs[-1]["Custo Hora Extra"] = 0.0

    def run(self):
        """
        Inicia a simulação para todos os veículos.
        """
        for i, route in enumerate(self.routes):
            if route:
                self.env.process(self.drive(i, route))
        
        self.env.run()
        
        if not self.logs:
            return pd.DataFrame(columns=["Veículo", "De", "Para", "Clima", "Tempo Base", "Tempo Real", "Hora Chegada", "Atraso", "Custo Hora Extra"])
            
        return pd.DataFrame(self.logs)
