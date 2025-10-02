import os
from dataclasses import dataclass


@dataclass
class PerformanceConfig:
    """Configuração de performance calculada dinamicamente"""

    cpu_cores: int
    list_workers: int  # Número de listas processadas em paralelo
    downloads_per_list: int  # Número de downloads por lista
    total_concurrent_downloads: int  # Total de downloads simultâneos no sistema

    def __str__(self) -> str:
        return (
            f"CPU Cores: {self.cpu_cores} | "
            f"Listas paralelas: {self.list_workers} | "
            f"Downloads/lista: {self.downloads_per_list} | "
            f"Total simultâneo: {self.total_concurrent_downloads}"
        )


def calculate_optimal_workers() -> PerformanceConfig:
    """
    Calcula o número ideal de workers baseado no hardware do usuário

    Estratégia:
    - Detecta número de cores da CPU
    - Calcula workers para listas e downloads
    - Balanceia para não sobrecarregar (máximo ~10 downloads simultâneos)
    - Garante pelo menos 1 worker de cada tipo

    Returns:
        PerformanceConfig com configurações otimizadas
    """
    # Detecta CPU cores
    cpu_cores = os.cpu_count() or 4  # Fallback para 4 se não detectar

    # Tenta obter memória RAM disponível
    try:
        import psutil

        memory_gb = psutil.virtual_memory().available / (1024**3)
        has_low_memory = memory_gb < 4  # Menos de 4GB disponível
    except (ImportError, Exception):
        has_low_memory = False  # Assume memória suficiente se psutil não disponível

    # Calcula workers para listas em paralelo
    # Regra: min(cores / 2, 3) - não processar muitas listas ao mesmo tempo
    # para evitar sobrecarga de rede e memória
    if cpu_cores <= 2:
        list_workers = 1
    elif cpu_cores <= 4:
        list_workers = 2
    elif cpu_cores <= 8:
        list_workers = 3
    else:
        list_workers = min(cpu_cores // 2, 4)  # Máximo 4 listas paralelas

    # Se memória baixa, reduz listas paralelas
    if has_low_memory and list_workers > 2:
        list_workers = 2

    # Calcula downloads por lista
    # Regra: distribuir cores entre listas, mas não ultrapassar 6 downloads totais
    # Reduzido para evitar rate limiting do Libgen (HTTP 500 errors)
    max_total_downloads = 6  # Limite conservador para não sobrecarregar rede e evitar rate limiting

    # Downloads por lista baseado em cores disponíveis
    if cpu_cores <= 2:
        downloads_per_list = 2
    elif cpu_cores <= 4:
        downloads_per_list = 3
    elif cpu_cores <= 8:
        downloads_per_list = 4
    else:
        downloads_per_list = 5

    # Ajusta para não exceder máximo total
    total_concurrent = list_workers * downloads_per_list
    if total_concurrent > max_total_downloads:
        downloads_per_list = max(1, max_total_downloads // list_workers)
        total_concurrent = list_workers * downloads_per_list

    # Se memória baixa, reduz downloads por lista
    if has_low_memory:
        downloads_per_list = max(1, downloads_per_list // 2)
        total_concurrent = list_workers * downloads_per_list

    return PerformanceConfig(
        cpu_cores=cpu_cores,
        list_workers=list_workers,
        downloads_per_list=downloads_per_list,
        total_concurrent_downloads=total_concurrent
    )


def get_performance_summary(config: PerformanceConfig) -> str:
    """
    Retorna um resumo legível da configuração de performance
    
    Args:
        config: Configuração de performance
        
    Returns:
        String formatada com informações de performance
    """
    efficiency = "Alta" if config.total_concurrent_downloads >= 6 else "Moderada" if config.total_concurrent_downloads >= 3 else "Conservadora"
    
    return f"""
⚙️  Configuração de Performance:
   • CPU Cores detectados: {config.cpu_cores}
   • Listas processadas simultaneamente: {config.list_workers}
   • Downloads por lista: {config.downloads_per_list}
   • Total de downloads simultâneos: {config.total_concurrent_downloads}
   • Eficiência: {efficiency}
"""
