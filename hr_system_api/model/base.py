#=====================================================================
# Módulo que define a base declarativa para os modelos do SQLAlchemy.
# Este é um componente central do ORM, permitindo que classes Python
# sejam mapeadas para tabelas de um banco de dados relacional.
#=====================================================================

# Importa a função que cria a classe base para a definição de modelos.
from sqlalchemy.ext.declarative import declarative_base

# Cria a instância da classe Base que servirá como a fundação para todos os
# modelos da aplicação (Employee, Note, etc.). Todos os modelos herdarão desta classe.
Base = declarative_base()