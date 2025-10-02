import logging
from pathlib import Path
from datetime import datetime


def setup_logger(log_dir: Path = Path("logs")) -> logging.Logger:
    """
    Configura o logger para salvar logs detalhados em arquivo

    Args:
        log_dir: Diretório onde salvar os logs

    Returns:
        Logger configurado
    """
    # Cria diretório de logs
    log_dir.mkdir(exist_ok=True)

    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"download_{timestamp}.log"

    # Configura o logger
    logger = logging.getLogger("best-books")
    logger.setLevel(logging.DEBUG)

    # Remove handlers existentes
    logger.handlers.clear()

    # Handler para arquivo (detalhado)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.info("=" * 80)
    logger.info("Iniciando Best Books Downloader")
    logger.info(f"Log salvo em: {log_file.absolute()}")
    logger.info("=" * 80)

    return logger
