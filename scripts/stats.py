from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text


@dataclass
class DownloadStats:
    """Estatísticas de download"""

    total_books: int = 0
    downloaded: int = 0
    already_existed: int = 0
    failed: int = 0
    not_found: int = 0

    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    download_times: list[float] = field(default_factory=list)  # Em segundos
    download_sizes: list[int] = field(default_factory=list)  # Em bytes

    def start(self) -> None:
        """Inicia o tracking de tempo"""
        self.start_time = datetime.now()

    def finish(self) -> None:
        """Finaliza o tracking de tempo"""
        self.end_time = datetime.now()

    def add_download(self, duration: float, size: int = 0) -> None:
        """
        Registra um download bem-sucedido

        Args:
            duration: Tempo de download em segundos
            size: Tamanho do arquivo em bytes
        """
        self.downloaded += 1
        self.download_times.append(duration)
        if size > 0:
            self.download_sizes.append(size)

    def add_existing(self) -> None:
        """Registra um arquivo que já existia"""
        self.already_existed += 1

    def add_failed(self) -> None:
        """Registra um download que falhou"""
        self.failed += 1

    def add_not_found(self) -> None:
        """Registra um livro não encontrado"""
        self.not_found += 1

    @property
    def total_duration(self) -> timedelta:
        """Duração total do processo"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return timedelta(0)

    @property
    def avg_download_time(self) -> float:
        """Tempo médio de download (apenas downloads novos)"""
        if self.download_times:
            return sum(self.download_times) / len(self.download_times)
        return 0.0

    @property
    def total_download_time(self) -> float:
        """Tempo total gasto em downloads"""
        return sum(self.download_times)

    @property
    def avg_download_size(self) -> float:
        """Tamanho médio de download em MB"""
        if self.download_sizes:
            return sum(self.download_sizes) / len(self.download_sizes) / (1024 * 1024)
        return 0.0

    @property
    def total_download_size(self) -> float:
        """Tamanho total baixado em MB"""
        return sum(self.download_sizes) / (1024 * 1024)

    @property
    def avg_download_speed(self) -> float:
        """Velocidade média de download em MB/s"""
        if self.download_times and self.download_sizes:
            total_mb = sum(self.download_sizes) / (1024 * 1024)
            total_time = sum(self.download_times)
            if total_time > 0:
                return total_mb / total_time
        return 0.0

    @property
    def success_rate(self) -> float:
        """Taxa de sucesso em porcentagem"""
        total_attempts = self.downloaded + self.failed + self.not_found
        if total_attempts > 0:
            return (self.downloaded / total_attempts) * 100
        return 0.0

    def display_summary(self, console: Console) -> None:
        """
        Exibe um resumo visual das estatísticas

        Args:
            console: Console do Rich para exibição
        """
        # Tabela de resultados
        results_table = Table(
            title="📊 Resumo de Downloads", show_header=True, header_style="bold cyan"
        )
        results_table.add_column("Categoria", style="cyan", width=25)
        results_table.add_column("Quantidade", justify="right", style="green")

        results_table.add_row("📚 Total de livros processados", str(self.total_books))
        results_table.add_row(
            "✅ Downloads novos", str(self.downloaded), style="bold green"
        )
        results_table.add_row(
            "⏭️  Já existiam", str(self.already_existed), style="yellow"
        )
        results_table.add_row("❌ Falhas", str(self.failed), style="red")
        results_table.add_row(
            "⚠️  Não encontrados", str(self.not_found), style="orange1"
        )

        # Tabela de performance
        perf_table = Table(
            title="⚡ Métricas de Performance",
            show_header=True,
            header_style="bold magenta",
        )
        perf_table.add_column("Métrica", style="magenta", width=30)
        perf_table.add_column("Valor", justify="right", style="green")

        # Tempo total
        total_time = self.total_duration
        hours, remainder = divmod(total_time.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_str = (
            f"{hours}h {minutes}m {seconds}s" if hours > 0 else f"{minutes}m {seconds}s"
        )
        perf_table.add_row("⏱️  Tempo total", time_str)

        # Tempo médio por download
        if self.avg_download_time > 0:
            avg_time_str = f"{self.avg_download_time:.2f}s"
            perf_table.add_row("⏱️  Tempo médio/download", avg_time_str)

        # Velocidade média
        if self.avg_download_speed > 0:
            speed_str = f"{self.avg_download_speed:.2f} MB/s"
            perf_table.add_row("🚀 Velocidade média", speed_str)

        # Tamanho médio
        if self.avg_download_size > 0:
            size_str = f"{self.avg_download_size:.2f} MB"
            perf_table.add_row("📦 Tamanho médio/arquivo", size_str)

        # Total baixado
        if self.total_download_size > 0:
            total_size_str = f"{self.total_download_size:.2f} MB"
            perf_table.add_row("💾 Total baixado", total_size_str, style="bold green")

        # Taxa de sucesso
        success_str = f"{self.success_rate:.1f}%"
        perf_table.add_row("✨ Taxa de sucesso", success_str, style="bold cyan")

        # Exibe as tabelas
        console.print()
        console.print(results_table)
        console.print()
        console.print(perf_table)
        console.print()

        # Mensagem final
        if self.success_rate >= 90:
            message = "🎉 Excelente! A maioria dos livros foram baixados com sucesso!"
            style = "bold green"
        elif self.success_rate >= 70:
            message = "✅ Bom trabalho! Maioria dos downloads completados."
            style = "bold yellow"
        else:
            message = "⚠️  Alguns problemas foram encontrados. Verifique os logs."
            style = "bold red"

        console.print(
            Panel(Text(message, justify="center"), style=style, border_style=style)
        )
