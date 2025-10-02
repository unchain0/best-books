from loguru import logger
from pathlib import Path
from datetime import datetime
import sys


def setup_logger(log_dir: Path = Path("logs")) -> None:
    """
    Configura o Loguru para salvar logs detalhados em arquivo
    
    Args:
        log_dir: Diretório onde salvar os logs
    """
    # Cria diretório de logs
    log_dir.mkdir(exist_ok=True)

    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"download_{timestamp}.log"

    # Remove handler padrão do stderr (evita duplicação com Rich)
    logger.remove()
    
    # Adiciona handler para arquivo com formato detalhado
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        level="DEBUG",
        encoding="utf-8",
        backtrace=True,
        diagnose=True,
    )
    
    # Adiciona handler para console apenas para erros críticos
    logger.add(
        sys.stderr,
        format="<red>{level}</red>: {message}",
        level="ERROR",
        colorize=True,
    )

    logger.info("=" * 80)
    logger.info("Iniciando Best Books Downloader")
    logger.info(f"Log salvo em: {log_file.absolute()}")
    logger.info("=" * 80)
