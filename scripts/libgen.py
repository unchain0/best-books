from libgen_api_enhanced import LibgenSearch
from libgen_api_enhanced.book import Book
import requests
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout
from .utils import filter_results, get_author, get_title
from pathlib import Path
import time


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
        results = self.search.search_title_filtered(
            query=self.title,
            filters={"extension": "epub"},
        )
        return filter_results(results, self.author)

    def download(self, folder: Path, book: Book, max_retries: int = 5) -> bool:
        """
        Baixa o livro para a pasta especificada com timeout e retry

        Args:
            folder: Pasta onde salvar o arquivo
            book: Livro a ser baixado
            max_retries: Número máximo de tentativas em caso de falha

        Returns:
            True se o download foi realizado, False se o arquivo já existia
        """
        book.resolve_direct_download_link()

        # Sanitiza o nome do arquivo (remove caracteres inválidos)
        safe_filename = "".join(
            c for c in book.title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        safe_filename = safe_filename[:200]  # Limita o tamanho do nome

        filepath = folder / f"{safe_filename}.epub"

        # Verifica se o arquivo já existe
        if filepath.exists():
            print("    ⏭️  Arquivo já existe, pulando download")
            return False

        # Download com timeout, streaming e retry
        for attempt in range(max_retries):
            try:
                resp = self.session.get(
                    book.resolved_download_link,
                    timeout=(30, 180),  # (connect timeout, read timeout)
                    stream=True,
                )
                resp.raise_for_status()

                # Buffer maior para escrita mais rápida
                with open(filepath, "wb", buffering=1024 * 1024) as f:
                    # Chunk maior = menos overhead, download mais rápido
                    for chunk in resp.iter_content(
                        chunk_size=1024 * 1024
                    ):  # 1MB chunks
                        if chunk:
                            f.write(chunk)

                return True

            except (Timeout, ConnectionError, ChunkedEncodingError, Exception) as e:
                # Remove arquivo parcial em caso de erro
                if filepath.exists():
                    filepath.unlink()

                if attempt < max_retries - 1:
                    wait_time = 2**attempt  # Backoff exponencial: 1s, 2s, 4s, 8s
                    print(
                        f"    🔄 Erro (tentativa {attempt + 1}/{max_retries}): {type(e).__name__}"
                    )
                    print(
                        f"    ⏳ Aguardando {wait_time}s antes de tentar novamente..."
                    )
                    time.sleep(wait_time)
                else:
                    # Última tentativa falhou, relança a exceção
                    raise

        return True


if __name__ == "__main__":
    libgen = Libgen(title="The Self-Taught Programmer", author="Cory Althoff")
    results = libgen.search_title()
    libgen.download(Path("."), results[0])
