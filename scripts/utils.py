from dataclasses import dataclass
from libgen_api_enhanced.book import Book


@dataclass
class BookInfo:
    """Informações de um livro extraído do site"""

    title: str
    author: str

    def __str__(self) -> str:
        return f"{self.title} - {self.author}"


def slugify(text: str) -> str:
    """Converte texto para formato slug (com hífens)"""
    return text.lower().replace(" ", "-").replace("'", "")


def get_author(author: str) -> str:
    """Formata nome de autor: capitaliza e converte & para vírgula"""
    return author.replace(" &", ",").strip().title()


def get_title(title: str) -> str:
    """Formata título: remove espaços extras e capitaliza"""
    return title.strip().title()


def filter_results(results: list[Book], author: str) -> list[Book]:
    """
    Filtra resultados de livros pelo autor de forma flexível.

    Estratégia:
    1. Extrai sobrenomes dos autores (últimas palavras)
    2. Verifica se os sobrenomes aparecem no campo autor do livro
    3. Case-insensitive e tolerante a variações

    Args:
        results: Lista de livros do Libgen
        author: String com nome(s) do(s) autor(es) do site

    Returns:
        Lista filtrada de livros que provavelmente correspondem ao autor
    """
    if not author or not results:
        return results

    # Extrai os sobrenomes dos autores (últimas palavras de cada nome)
    # Ex: "Eric Evans" -> ["Evans"], "Martin Fowler, Kent Beck" -> ["Fowler", "Beck"]
    author_names = author.replace(" &", ",").replace(" And ", ",").split(",")
    surnames = []
    for name in author_names:
        name = name.strip()
        if name:
            # Pega a última palavra (geralmente o sobrenome)
            words = name.split()
            if words:
                surnames.append(words[-1].lower())

    if not surnames:
        return results

    # Filtra livros onde pelo menos um sobrenome aparece no campo autor
    filtered = []
    for result in results:
        if not result.author:
            continue

        result_author_lower = result.author.lower()

        # Verifica se algum sobrenome está presente no autor do resultado
        for surname in surnames:
            if surname in result_author_lower:
                filtered.append(result)
                break  # Encontrou match, não precisa verificar outros sobrenomes

    # Se não encontrou nenhum resultado com filtro, retorna os primeiros resultados
    # (o título já foi buscado, então provavelmente são relevantes)
    if not filtered and results:
        return results[:3]  # Retorna até 3 primeiros resultados sem filtro

    return filtered
