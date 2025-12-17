#======================================================================
# Módulo que define o modelo de dados para uma Anotação de funcionário.
#======================================================================

from sqlalchemy import Column, Integer, DateTime, Text, String, ForeignKey
from datetime import datetime
from .base import Base

# Define a classe 'Note' que mapeia para a tabela 'notes' no banco de dados.
# Utilizada em:
# - 'model/__init__.py': Para ser exposta como parte do pacote 'model'.
# - 'app.py': Nas funções 'add_employee' (para a primeira anotação), 'add_note',
#   e 'update_note' para queries e criação de novos registros.
class Note(Base):
    """
    Representa uma anotação sobre um funcionário na tabela 'notes'.
    Cada anotação está vinculada a um funcionário específico.
    """
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

    # Chave estrangeira que liga a anotação à matrícula de um funcionário.
    employee_matricula = Column(Integer, ForeignKey("employee.pk_employee"), nullable=False)