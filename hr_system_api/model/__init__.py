#===============================================================================================
# Módulo de inicialização do pacote 'model'.
# Este arquivo é executado quando o pacote 'model' é importado. Ele é responsável
# por configurar a conexão com o banco de dados, garantir que o diretório e o
# arquivo do banco existam, e criar as tabelas com base nos modelos definidos.
# Também expõe a fábrica de sessões 'Session' e as classes de modelo para o resto da aplicação.
#===============================================================================================

# Importações de bibliotecas externas necessárias para a configuração do banco de dados
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

#---------------------------------------------------------------------------------------------------------------------------
# Importações relativas para evitar problemas com importações circulares, onde
# a construção do pacote fica em loop pois a uma "parte A" começa a ser contruída mas é pausada
# para construir a "parte B" que por sua vez depende da "parte A" que ainda não foi construída.
# Em python, recomenda-se sempre usar importações relativas em pacotes para evitar esses problemas.
# Exemplo de importação relativa:
# from.arquivo import Classe

from.base import Base
from.employee import Employee
from.bus_access import BusAccess
from.note import Note

#---------------------------------------------------------------------------------------------------------------------------

db_path = "database/"

if not os.path.exists(db_path): 
    os.makedirs(db_path)

db_url = 'sqlite:///%s/db.sqlite3' % db_path 

engine = create_engine(db_url, echo=False) 

Session = sessionmaker(bind=engine) 

if not database_exists(engine.url):
    create_database(engine.url)

Base.metadata.create_all(engine)