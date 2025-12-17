#=========================================================================
# Módulo de configuração do sistema de logs da aplicação.
# Utiliza o dictConfig para definir de forma estruturada os formatadores,
# manipuladores (handlers) e níveis de log.
#=========================================================================

from logging.config import dictConfig
import logging
import os

log_path = "log/"
if not os.path.exists(log_path):
    os.makedirs(log_path)

# Configura o sistema de logging da aplicação a partir de um dicionário.
# Esta configuração é carregada uma vez quando a aplicação inicia.
dictConfig({
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)-4s %(funcName)s() L%(lineno)-4d %(message)s",
        },
        "detailed": {
            "format": "[%(asctime)s] %(levelname)-4s %(funcName)s() L%(lineno)-4d %(message)s - call_trace=%(pathname)s L%(lineno)-4d",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "error_file": {
            "class": "concurrent_log_handler.ConcurrentRotatingFileHandler",
            "formatter": "detailed",
            "filename": "log/gunicorn.error.log",
            "maxBytes": 10000,
            "backupCount": 10,
            "delay": True,
        },
        "detailed_file": {
            "class": "concurrent_log_handler.ConcurrentRotatingFileHandler",
            "formatter": "detailed",
            "filename": "log/gunicorn.detailed.log",
            "maxBytes": 10000,
            "backupCount": 10,
            "delay": True,
        }
    },
    "loggers": {
        "gunicorn.error": {
            "handlers": ["console", "error_file"],
            "level": "INFO",
            "propagate": False,
        }
    },
    "root": {
        "handlers": ["console", "detailed_file"],
        "level": "INFO",
    }
})

# Cria a instância do logger que será importada e usada em outras partes da aplicação.
# Utilizado em:
# - 'app.py': Importado como 'logger' e usado nas funções de endpoint para registrar
#   informações de debug, avisos e erros (ex: 'add_employee', 'get_employee').
logger = logging.getLogger(__name__)