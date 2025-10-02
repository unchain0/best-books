import bs4
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TaskID
from rich.panel import Panel
from rich.text import Text
from .libgen import Libgen, DownloadResult
from .utils import slugify, BookInfo
from .logger import setup_logger
from .stats import DownloadStats
from .performance import calculate_optimal_workers, PerformanceConfig


class Scraper:
    """Classe para web scraping do site best-books.dev"""

    def __init__(self, base_url: str = "https://www.best-books.dev/", perf_config: PerformanceConfig | None = None):
        """
        Inicializa o scraper

        Args:
            base_url: URL base do site a ser raspado
            perf_config: Configuração de performance (auto-detecta se None)
        """
        self.base_url = base_url
        self.books_dir = Path("books")
        
        # Calcula workers ideais baseado no hardware
        self.perf_config = perf_config or calculate_optimal_workers()
        
        # Rich console
        self.console = Console()
        
        # Logger e estatísticas
        self.logger = setup_logger()
        self.stats = DownloadStats()
        
        # Lock para atualizações thread-safe de estatísticas
        self.stats_lock = Lock()
        
        # Progresso de listas (dict thread-safe)
        self.list_progress: dict[str, dict[str, int]] = {}

    def _get_all_lists(self) -> list[tuple[str, str]]:
        """Obtém todas as listas de livros do site"""
        self.console.print("[bold cyan]🔍 Buscando listas de livros...[/bold cyan]")
        self.logger.info("Buscando listas de livros")
        
        resp = requests.get(self.base_url)
        resp.encoding = 'utf-8'  # Força encoding UTF-8
        soup = bs4.BeautifulSoup(resp.text, "html.parser")

        # Encontra todos os links de listas
        list_links = soup.find_all("a", class_="button-2")

        lists = []
        for link in list_links:
            title = link.text.strip()
            url = link.get("href")
            # Garante que url é string antes de usar
            if url and isinstance(url, str) and url.startswith("/list/"):
                full_url = self.base_url.rstrip("/") + url
                lists.append((title, full_url))

        self.console.print(f"[green]✔[/green] Encontradas [bold]{len(lists)}[/bold] listas")
        self.logger.info(f"Encontradas {len(lists)} listas")
        return lists

    def _get_books_from_list(self, list_url: str) -> list[BookInfo]:
        """Extrai os livros de uma lista específica"""
        self.logger.info(f"Acessando lista: {list_url}")
        resp = requests.get(list_url)
        resp.encoding = 'utf-8'  # Força encoding UTF-8
        soup = bs4.BeautifulSoup(resp.text, "html.parser")

        books = []
        # Encontra todos os itens de livros
        book_items = soup.find_all("div", class_="collection-item-2")

        for item in book_items:
            # Título do livro
            title_elem = item.find("h3", class_="heading-5")
            if not title_elem:
                continue

            # Autor do livro
            author_elem = item.find("div", class_="text-block-8")
            if not author_elem:
                continue

            books.append(
                BookInfo(title=title_elem.text.strip(), author=author_elem.text.strip())
            )

        self.logger.info(f"Encontrados {len(books)} livros")
        return books

    def _download_book(self, book: BookInfo, folder: Path) -> DownloadResult:
        """Baixa um livro usando a classe Libgen"""
        try:
            self.logger.info(f"Buscando: {book.title} ({book.author})")

            # Busca o livro no Libgen
            libgen = Libgen(title=book.title, author=book.author)
            results = libgen.search_title()

            if not results:
                self.logger.warning(f"Livro não encontrado no Libgen: {book.title}")
                return DownloadResult(success=False, error="Não encontrado")

            # Baixa o primeiro resultado
            self.logger.info(f"Baixando: {book.title}")
            result = libgen.download(folder, results[0], logger=self.logger)
            
            return result

        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout ao baixar: {book.title}")
            return DownloadResult(success=False, error="Timeout")
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erro HTTP ao baixar {book.title}: {e}")
            return DownloadResult(success=False, error=str(e))
        except Exception as e:
            self.logger.error(f"Erro ao baixar {book.title}: {e}")
            return DownloadResult(success=False, error=str(e))

    def _process_list(self, list_title: str, list_url: str, progress: Progress) -> None:
        """Processa uma lista completa: extrai e baixa todos os livros"""
        self.logger.info(f"Processando lista: {list_title}")
        
        # Cria pasta para a lista
        list_folder = self.books_dir / slugify(list_title)
        list_folder.mkdir(exist_ok=True)
        self.logger.info(f"Pasta: {list_folder}")

        # Obtém livros da lista
        books = self._get_books_from_list(list_url)

        if not books:
            self.logger.warning("Nenhum livro encontrado nesta lista")
            return
        
        with self.stats_lock:
            self.stats.total_books += len(books)
        
        # Cria a task AGORA que sabemos o total (não antes)
        task_id = progress.add_task(
            f"📚 [bold blue]{list_title}[/bold blue]",
            total=len(books)
        )
            
        # Baixa livros em paralelo
        with ThreadPoolExecutor(max_workers=self.perf_config.downloads_per_list) as executor:
            # Submete todos os downloads
            future_to_book = {
                executor.submit(self._download_book, book, list_folder): book
                for book in books
            }
                
            # Processa resultados conforme completam
            try:
                for future in as_completed(future_to_book):
                    book = future_to_book[future]
                    
                    try:
                        result: DownloadResult = future.result()
                        
                        with self.stats_lock:
                            if result.success:
                                if result.already_existed:
                                    self.stats.add_existing()
                                else:
                                    self.stats.add_download(result.duration, result.size)
                            elif result.error and "não encontrado" in result.error.lower():
                                self.stats.add_not_found()
                            else:
                                self.stats.add_failed()
                    
                    except Exception as e:
                        self.logger.error(f"Erro inesperado ao processar {book.title}: {e}")
                        with self.stats_lock:
                            self.stats.add_failed()
                    
                    progress.update(task_id, advance=1)
            
            except KeyboardInterrupt:
                # Cancela todas as futures pendentes
                self.console.print("\n[bold yellow]⚠️  Cancelando downloads...[/bold yellow]")
                for future in future_to_book:
                    future.cancel()
                executor.shutdown(wait=False)
                raise
        
        self.logger.info(f"Lista '{list_title}' concluída")
        # Marca como concluída
        progress.update(task_id, description=f"✔ [green]{list_title}[/green]")

    def _print_summary(self) -> None:
        """Imprime resumo final do processo"""
        self.console.print("\n")
        self.console.print(Panel(
            Text("🎉 PROCESSO CONCLUÍDO!", justify="center", style="bold green"),
            border_style="green"
        ))
        
        # Exibe estatísticas
        self.stats.display_summary(self.console)
        
        # Informações adicionais
        self.console.print(f"[cyan]📁 Pasta de downloads:[/cyan] [bold]{self.books_dir.absolute()}[/bold]")
        self.console.print("[cyan]📝 Arquivo de log:[/cyan] [bold]logs/[/bold]")
        self.logger.info("Processo concluído")

    def run(self) -> None:
        """Executa o scraping e download completo de todas as listas"""
        self.stats.start()
        
        try:
            # Banner inicial
            self.console.print(Panel(
                Text("📚 Best Books Downloader", justify="center", style="bold cyan"),
                border_style="cyan"
            ))
            self.console.print()
            
            # Exibe configurações de performance
            self.console.print("[bold cyan]⚙️  Configuração de Performance:[/bold cyan]")
            self.console.print(f"   [dim]•[/dim] CPU Cores detectados: [bold]{self.perf_config.cpu_cores}[/bold]")
            self.console.print(f"   [dim]•[/dim] Listas processadas simultaneamente: [bold green]{self.perf_config.list_workers}[/bold green]")
            self.console.print(f"   [dim]•[/dim] Downloads por lista: [bold green]{self.perf_config.downloads_per_list}[/bold green]")
            self.console.print(f"   [dim]•[/dim] Total de downloads simultâneos: [bold green]{self.perf_config.total_concurrent_downloads}[/bold green]")
            
            efficiency = "Alta" if self.perf_config.total_concurrent_downloads >= 8 else "Moderada" if self.perf_config.total_concurrent_downloads >= 4 else "Conservadora"
            efficiency_color = "green" if efficiency == "Alta" else "yellow" if efficiency == "Moderada" else "red"
            self.console.print(f"   [dim]•[/dim] Eficiência: [bold {efficiency_color}]{efficiency}[/bold {efficiency_color}]")
            self.console.print()
            
            # Cria pasta books/
            self.books_dir.mkdir(exist_ok=True)

            # Obtém todas as listas
            lists = self._get_all_lists()
            self.console.print()

            # Progress bar consolidada para todas as listas
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40, complete_style="green", finished_style="green", pulse_style="green"),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=self.console,
                refresh_per_second=2,  # Atualiza apenas 2x por segundo (menos pisca-pisca)
                transient=False,  # Não limpa as linhas ao terminar
                expand=False
            ) as progress:
                
                # Processa listas em paralelo
                with ThreadPoolExecutor(max_workers=self.perf_config.list_workers) as list_executor:
                    # Submete todas as listas
                    futures = {
                        list_executor.submit(
                            self._process_list, 
                            list_title, 
                            list_url,
                            progress
                        ): list_title
                        for list_title, list_url in lists
                    }
                    
                    # Aguarda conclusão
                    try:
                        for future in as_completed(futures):
                            list_title = futures[future]
                            try:
                                future.result()
                            except Exception as e:
                                self.logger.error(f"Erro ao processar lista {list_title}: {e}")
                    
                    except KeyboardInterrupt:
                        self.console.print("\n[bold yellow]⚠️  Cancelando todas as listas...[/bold yellow]")
                        for future in futures:
                            future.cancel()
                        list_executor.shutdown(wait=False)
                        raise
            
            self.stats.finish()
            
            # Exibe resumo final
            self._print_summary()
        
        except KeyboardInterrupt:
            self.console.print("\n")
            self.console.print(Panel(
                Text("❌ PROCESSO CANCELADO PELO USUÁRIO", justify="center", style="bold red"),
                border_style="red"
            ))
            self.stats.finish()
            
            # Exibe estatísticas parciais
            self.console.print("\n[yellow]Estatísticas parciais:[/yellow]")
            self.stats.display_summary(self.console)
            
            self.console.print("\n[cyan]📝 Logs completos:[/cyan] [bold]logs/[/bold]")
            self.logger.info("Processo cancelado pelo usuário (Ctrl+C)")
            
            # Re-levanta a exceção para sair do programa
            raise


def run_scraper():
    """Função wrapper para manter compatibilidade com código existente"""
    scraper = Scraper()
    scraper.run()
