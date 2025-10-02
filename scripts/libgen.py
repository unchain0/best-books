from libgen_api_enhanced import LibgenSearch
from libgen_api_enhanced.book import Book
import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from .utils import filter_results, get_author, get_title
from pathlib import Path
import time
from typing import Optional
from dataclasses import dataclass
import logging
from contextlib import contextmanager
import sys


@contextmanager
def suppress_libgen_output():
    """Suprime apenas prints específicos da biblioteca libgen-api-enhanced"""
    
    # Cria um wrapper para stdout/stderr que filtra mensagens específicas
    class FilteredWriter:
        def __init__(self, original_stream):
            self.original_stream = original_stream
            self.buffer = ""
            
        def write(self, text):
            # Bloqueia mensagens específicas da biblioteca libgen-api-enhanced
            if text and any(msg in text for msg in [
                "No results table found",
                "Error during search page retrieval",
                "HTTP error 500",
                "Connection broken",
                "IncompleteRead"
            ]):
                return len(text)
            # Passa tudo o resto para o stream original
            return self.original_stream.write(text)
        
        def flush(self):
            self.original_stream.flush()
        
        def __getattr__(self, name):
            # Delega outros atributos para o stream original
            return getattr(self.original_stream, name)
    
    # Salva streams originais
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    # Salva print original
    import builtins
    original_print = builtins.print
    
    def filtered_print(*args, **kwargs):
        text = ' '.join(str(arg) for arg in args)
        # Bloqueia mensagens de erro da biblioteca libgen
        if not any(msg in text for msg in [
            "No results table found",
            "Error during search page retrieval",
            "HTTP error 500",
            "Connection broken",
            "IncompleteRead"
        ]):
            original_print(*args, **kwargs)
    
    try:
        # Substitui stdout/stderr com versões filtradas
        sys.stdout = FilteredWriter(old_stdout)
        sys.stderr = FilteredWriter(old_stderr)
        
        # Substitui print builtin
        builtins.print = filtered_print
        
        yield
    finally:
        # Restaura tudo
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        builtins.print = original_print


@dataclass
class DownloadResult:
    """Resultado de um download"""
    success: bool
    already_existed: bool = False
    duration: float = 0.0  # segundos
    size: int = 0  # bytes
    error: Optional[str] = None


class Libgen:
    def __init__(self, mirror: str = "li", *, title: str = "", author: str = ""):
        self.search = LibgenSearch(mirror=mirror)
        self.title = get_title(title)
        self.author = get_author(author)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def __del__(self):
        """Fecha a session ao destruir o objeto"""
        if hasattr(self, "session"):
            self.session.close()

    def search_title(self) -> list[Book]:
        # Suprime mensagens "No results table found on search page"
        # sem afetar as progress bars do Rich
        with suppress_libgen_output():
            results = self.search.search_title_filtered(
                query=self.title,
                filters={"extension": "epub"},
            )
        return filter_results(results, self.author)

    def download(self, folder: Path, book: Book, max_retries: int = 5, logger: Optional[logging.Logger] = None) -> DownloadResult:
        """
        Baixa o livro para a pasta especificada com timeout e retry

        Args:
            folder: Pasta onde salvar o arquivo
            book: Livro a ser baixado
            max_retries: Número máximo de tentativas em caso de falha
            logger: Logger para registrar informações detalhadas

        Returns:
            DownloadResult com informações sobre o download
        """
        start_time = time.time()
        book.resolve_direct_download_link()

        # Sanitiza o nome do arquivo (remove caracteres inválidos)
        safe_filename = "".join(
            c for c in book.title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        safe_filename = safe_filename[:200]  # Limita o tamanho do nome

        filepath = folder / f"{safe_filename}.epub"

        # Verifica se o arquivo já existe
        if filepath.exists():
            if logger:
                logger.info(f"Arquivo já existe: {safe_filename}.epub")
            return DownloadResult(
                success=True,
                already_existed=True,
                size=filepath.stat().st_size
            )

        # Download com timeout, streaming e retry
        for attempt in range(max_retries):
            try:
                download_start = time.time()
                resp = self.session.get(
                    book.resolved_download_link,
                    timeout=(30, 180),  # (connect timeout, read timeout)
                    stream=True,
                )
                resp.raise_for_status()

                # Buffer maior para escrita mais rápida
                total_size = 0
                with open(filepath, "wb", buffering=1024 * 1024) as f:
                    # Chunk maior = menos overhead, download mais rápido
                    for chunk in resp.iter_content(
                        chunk_size=1024 * 1024
                    ):  # 1MB chunks
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)

                duration = time.time() - start_time
                if logger:
                    speed_mbps = (total_size / (1024 * 1024)) / (time.time() - download_start) if (time.time() - download_start) > 0 else 0
                    logger.info(f"Download concluído: {safe_filename}.epub ({total_size / (1024*1024):.2f} MB, {speed_mbps:.2f} MB/s)")
                
                return DownloadResult(
                    success=True,
                    duration=duration,
                    size=total_size
                )

            except (Timeout, ConnectionError, ChunkedEncodingError, Exception) as e:
                # Remove arquivo parcial em caso de erro
                if filepath.exists():
                    filepath.unlink()

                error_msg = f"{type(e).__name__}: {str(e)}"
                if logger:
                    logger.warning(f"Tentativa {attempt + 1}/{max_retries} falhou: {error_msg}")
                
                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Backoff exponencial: 1s, 2s, 4s, 8s
                    if logger:
                        logger.info(f"Aguardando {wait_time}s antes de tentar novamente...")
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou
                    duration = time.time() - start_time
                    if logger:
                        logger.error(f"Download falhou após {max_retries} tentativas: {safe_filename}.epub")
                    return DownloadResult(
                        success=False,
                        duration=duration,
                        error=error_msg
                    )

        # Não deve chegar aqui, mas por garantia
        return DownloadResult(success=False, error="Erro desconhecido")


if __name__ == "__main__":
    libgen = Libgen(title="The Self-Taught Programmer", author="Cory Althoff")
    results = libgen.search_title()
    libgen.download(Path("."), results[0])
