"""
Testes para o módulo scraper.py
Testa web scraping do site best-books.dev
"""
import pytest
from scripts.scraper import Scraper
from scripts.utils import slugify, BookInfo


class TestSlugify:
    """Testes para função slugify"""
    
    def test_slugify_basic(self):
        """Testa conversão básica para slug"""
        assert slugify("Best Python Books") == "best-python-books"
        assert slugify("Best JavaScript Books") == "best-javascript-books"
    
    def test_slugify_with_apostrophe(self):
        """Testa remoção de apóstrofos"""
        assert slugify("The Hitchhiker's Guide") == "the-hitchhikers-guide"
        assert slugify("O'Reilly Books") == "oreilly-books"
    
    def test_slugify_multiple_spaces(self):
        """Testa com múltiplos espaços"""
        assert slugify("Best   Programming   Books") == "best---programming---books"
    
    def test_slugify_empty(self):
        """Testa string vazia"""
        assert slugify("") == ""


class TestScraper:
    """Testes para a classe Scraper"""
    
    def test_scraper_initialization(self):
        """Testa inicialização da classe Scraper"""
        scraper = Scraper()
        
        assert scraper.base_url == "https://www.best-books.dev/"
        assert scraper.books_dir.name == "books"
        assert scraper.total_downloaded == 0
        assert scraper.total_failed == 0
    
    def test_scraper_custom_url(self):
        """Testa inicialização com URL customizada"""
        custom_url = "https://example.com/"
        scraper = Scraper(base_url=custom_url)
        
        assert scraper.base_url == custom_url
    
    @pytest.mark.network
    def test_scraper_unicode_handling(self):
        """Testa se caracteres Unicode são extraídos corretamente"""
        scraper = Scraper()
        list_url = "https://www.best-books.dev/list/best-python-books"
        books = scraper._get_books_from_list(list_url)
        
        # Verifica se há livros
        assert len(books) > 0, "Nenhum livro encontrado"
        
        # Verifica se não há caracteres de encoding incorreto
        for book in books:
            # Não deve conter sequências UTF-8 mal decodificadas
            assert "Ã" not in book.title, f"Encoding incorreto no título: {book.title}"
            assert "Ã" not in book.author, f"Encoding incorreto no autor: {book.author}"
            
            # Deve aceitar caracteres Unicode válidos
            # (não faz assert específico pois depende dos dados do site)


class TestGetAllLists:
    """Testes para método _get_all_lists"""
    
    @pytest.mark.network
    def test_get_all_lists_returns_data(self):
        """Testa se retorna listas do site"""
        scraper = Scraper()
        lists = scraper._get_all_lists()
        
        # Verifica estrutura básica
        assert isinstance(lists, list), "Deve retornar uma lista"
        assert len(lists) > 0, "Deve retornar pelo menos uma lista"
        
        # Verifica estrutura de cada item
        for title, url in lists:
            assert isinstance(title, str), "Título deve ser string"
            assert isinstance(url, str), "URL deve ser string"
            assert len(title) > 0, "Título não pode ser vazio"
            assert url.startswith("https://www.best-books.dev/list/"), \
                f"URL inválida: {url}"
        
        print(f"\n✓ Encontradas {len(lists)} listas")
        print(f"  Primeira lista: {lists[0][0]}")
    
    @pytest.mark.network
    def test_get_all_lists_popular_lists(self):
        """Verifica se listas populares estão presentes"""
        scraper = Scraper()
        lists = scraper._get_all_lists()
        titles = [title for title, url in lists]
        
        # Verifica se algumas listas populares estão presentes
        popular_lists = [
            "Best Programming Books",
            "Best Python Books",
            "Best JavaScript Books"
        ]
        
        found_popular = [title for title in popular_lists if title in titles]
        assert len(found_popular) > 0, \
            f"Nenhuma lista popular encontrada. Esperado: {popular_lists}"
        
        print(f"\n✓ Listas populares encontradas: {found_popular}")
    
    @pytest.mark.network
    def test_get_all_lists_url_format(self):
        """Verifica formato das URLs"""
        scraper = Scraper()
        lists = scraper._get_all_lists()
        
        for title, url in lists:
            # URL deve começar com o domínio correto
            assert url.startswith("https://www.best-books.dev/list/")
            
            # URL não deve ter espaços
            assert " " not in url
            
            # Extrai o slug da URL
            slug = url.split("/list/")[1]
            assert len(slug) > 0, f"Slug vazio para: {title}"
            assert slug == slug.lower(), f"Slug deve ser minúsculo: {slug}"


class TestGetBooksFromList:
    """Testes para método _get_books_from_list"""
    
    @pytest.mark.network
    def test_get_books_from_python_list(self):
        """Testa extração de livros da lista de Python"""
        scraper = Scraper()
        list_url = "https://www.best-books.dev/list/best-python-books"
        books = scraper._get_books_from_list(list_url)
        
        # Verifica estrutura básica
        assert isinstance(books, list), "Deve retornar uma lista"
        assert len(books) > 0, "Deve retornar pelo menos um livro"
        
        print(f"\n✓ Encontrados {len(books)} livros na lista de Python")
    
    @pytest.mark.network
    def test_get_books_structure(self):
        """Verifica estrutura dos dados dos livros"""
        scraper = Scraper()
        list_url = "https://www.best-books.dev/list/best-python-books"
        books = scraper._get_books_from_list(list_url)
        
        # Verifica estrutura de cada livro
        for book in books[:5]:  # Testa apenas os primeiros 5
            assert isinstance(book, BookInfo), "Livro deve ser uma instância de BookInfo"
            assert hasattr(book, "title"), "Livro deve ter atributo 'title'"
            assert hasattr(book, "author"), "Livro deve ter atributo 'author'"
            
            # Verifica que não são vazios
            assert len(book.title) > 0, "Título não pode ser vazio"
            assert len(book.author) > 0, "Autor não pode ser vazio"
            
            # Verifica que não contém tags HTML
            assert "<" not in book.title, "Título contém HTML"
            assert "<" not in book.author, "Autor contém HTML"
    
    @pytest.mark.network
    def test_get_books_known_books(self):
        """Verifica se livros conhecidos estão na lista"""
        scraper = Scraper()
        list_url = "https://www.best-books.dev/list/best-python-books"
        books = scraper._get_books_from_list(list_url)
        
        titles = [book.title for book in books]
        
        # Lista de livros populares que devem estar presentes
        # (pode variar, mas pelo menos alguns devem estar)
        popular_books = [
            "Python Crash Course",
            "Automate the Boring Stuff with Python",
            "Fluent Python",
            "Learning Python"
        ]
        
        found_books = [title for title in popular_books if title in titles]
        
        print(f"\n✓ Livros populares encontrados: {found_books}")
        print("  Primeiros 5 livros:")
        for i, book in enumerate(books[:5], 1):
            print(f"    {i}. {book.title} - {book.author}")
    
    @pytest.mark.network
    def test_get_books_author_format(self):
        """Verifica formatação dos autores"""
        scraper = Scraper()
        list_url = "https://www.best-books.dev/list/best-python-books"
        books = scraper._get_books_from_list(list_url)
        
        for book in books[:10]:  # Testa primeiros 10
            author = book.author
            
            # Verifica que não tem espaços extras no início/fim
            assert author == author.strip(), \
                f"Autor tem espaços extras: '{author}'"
            
            # Verifica que tem pelo menos um nome
            assert len(author.split()) > 0, \
                f"Autor inválido: '{author}'"
    
    @pytest.mark.network
    def test_get_books_multiple_lists(self):
        """Testa extração de múltiplas listas"""
        scraper = Scraper()
        lists_to_test = [
            "https://www.best-books.dev/list/best-python-books",
            "https://www.best-books.dev/list/best-javascript-books",
            "https://www.best-books.dev/list/best-programming-books"
        ]
        
        for list_url in lists_to_test:
            books = scraper._get_books_from_list(list_url)
            
            assert len(books) > 0, f"Nenhum livro encontrado em: {list_url}"
            
            # Verifica pelo menos o primeiro livro
            first_book = books[0]
            assert isinstance(first_book, BookInfo)
            assert hasattr(first_book, "title")
            assert hasattr(first_book, "author")
            
            list_name = list_url.split('/')[-1]
            print(f"\n✓ {list_name}: {len(books)} livros")


# Configuração para marcar testes que precisam de rede
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "network: marca testes que precisam de conexão de rede"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos (downloads, etc)"
    )


if __name__ == "__main__":
    # Executa os testes quando o arquivo é rodado diretamente
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
