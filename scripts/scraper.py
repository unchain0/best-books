import bs4
import requests
from pathlib import Path
import time
from .libgen import Libgen
from .utils import slugify, BookInfo


class Scraper:
    """Classe para web scraping do site best-books.dev"""

    def __init__(self, base_url: str = "https://www.best-books.dev/"):
        """
        Inicializa o scraper

        Args:
            base_url: URL base do site a ser raspado
        """
        self.base_url = base_url
        self.books_dir = Path("books")
        self.total_downloaded = 0
        self.total_failed = 0

    def _get_all_lists(self) -> list[tuple[str, str]]:
        """Obtém todas as listas de livros do site"""
        print("🔍 Buscando listas de livros...")
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

        print(f"✔ Encontradas {len(lists)} listas")
        return lists

    def _get_books_from_list(self, list_url: str) -> list[BookInfo]:
        """Extrai os livros de uma lista específica"""
        print(f"  📖 Acessando lista: {list_url}")
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

        print(f"  ✓ Encontrados {len(books)} livros")
        return books

    def _download_book(self, book: BookInfo, folder: Path) -> bool:
        """Baixa um livro usando a classe Libgen"""
        try:
            print(f"    🔍 Buscando: {book.title} ({book.author})")

            # Busca o livro no Libgen
            libgen = Libgen(title=book.title, author=book.author)
            results = libgen.search_title()

            if not results:
                print("    ⚠️  Livro não encontrado no Libgen")
                return False

            # Baixa o primeiro resultado
            print("    ⬇️  Baixando...")
            downloaded = libgen.download(folder, results[0])

            # Se retornou False, arquivo já existia (já foi impresso)
            if downloaded:
                print("    ✔ Download concluído!")
                return True
            else:
                # Arquivo já existia, conta como sucesso
                return True

        except requests.exceptions.Timeout:
            print("    ⏱️  Timeout ao baixar - servidor demorou muito")
            return False
        except requests.exceptions.HTTPError as e:
            if "504" in str(e) or "Gateway Timeout" in str(e):
                print("    ⏱️  Timeout do servidor (504) - tentando próximo...")
            else:
                print(f"    ❌ Erro HTTP: {e}")
            return False
        except Exception as e:
            print(f"    ❌ Erro ao baixar: {e}")
            return False

    def _process_list(self, list_title: str, list_url: str) -> None:
        """Processa uma lista completa: extrai e baixa todos os livros"""
        print(f"\n{'=' * 60}")
        print(f"📚 Processando lista: {list_title}")
        print(f"{'=' * 60}")

        # Cria pasta para a lista
        list_folder = self.books_dir / slugify(list_title)
        list_folder.mkdir(exist_ok=True)
        print(f"📁 Pasta: {list_folder}")

        # Obtém livros da lista
        books = self._get_books_from_list(list_url)

        if not books:
            print("  ⚠️  Nenhum livro encontrado nesta lista")
            return

        # Baixa cada livro
        for i, book in enumerate(books, 1):
            print(f"\n  [{i}/{len(books)}]")

            if self._download_book(book, list_folder):
                self.total_downloaded += 1
            else:
                self.total_failed += 1

            # Aguarda entre downloads
            if i < len(books):
                time.sleep(2)

        # Aguarda entre listas
        time.sleep(3)

    def _print_summary(self) -> None:
        """Imprime resumo final do processo"""
        print(f"\n{'=' * 60}")
        print("🎉 PROCESSO CONCLUÍDO!")
        print(f"{'=' * 60}")
        print(f"✔ Livros baixados com sucesso: {self.total_downloaded}")
        print(f"❌ Livros não encontrados/erro: {self.total_failed}")
        print(f"📁 Todos os livros estão na pasta: {self.books_dir.absolute()}")

    def run(self) -> None:
        """Executa o scraping e download completo de todas as listas"""
        # Cria pasta books/
        self.books_dir.mkdir(exist_ok=True)

        # Obtém todas as listas
        lists = self._get_all_lists()

        # Processa cada lista
        for list_title, list_url in lists:
            self._process_list(list_title, list_url)

        # Exibe resumo final
        self._print_summary()


def run_scraper():
    """Função wrapper para manter compatibilidade com código existente"""
    scraper = Scraper()
    scraper.run()
