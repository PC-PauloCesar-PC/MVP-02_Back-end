#===========================================================================
# Módulo que define o modelo de dados para um registro de acesso ao ônibus.
#===========================================================================

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

# Define a classe 'BusAccess' que mapeia para a tabela 'bus_access' no banco de dados.
# Utilizada em:
# - 'model/__init__.py': Para ser exposta como parte do pacote 'model'.
# - 'app.py': Nas funções 'upload_bus_access_file', 'get_accesses_by_employee',
#   'get_employees_by_bus', 'get_accesses_by_date', e 'get_all_bus_accesses' para queries.
# - 'schemas/bus_access.py': Como anotação de tipo na função 'show_all_bus_accesses'.
class BusAccess(Base):
    """
    Representa um único registro de acesso de um funcionário a um ônibus na
    tabela 'bus_access'.
    """
    __tablename__ = 'bus_access'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    bus_number = Column(Integer, nullable=False)

    # Chave estrangeira que liga o registro de acesso à matrícula de um funcionário.
    # Aponta para a coluna 'pk_employee' da tabela 'employee'.
    employee_matricula = Column(Integer, ForeignKey("employee.pk_employee"), nullable=False)

    # Define o relacionamento com o modelo 'Employee'.
    employee = relationship("Employee", back_populates="bus_accesses")

    # Método construtor para criar uma nova instância de BusAccess.
    def __init__(self, timestamp: datetime, bus_number: int, employee_matricula: int):
        """
        Inicializa um novo registro de acesso ao ônibus.

        Args:
            timestamp (datetime): A data e hora do acesso.
            bus_number (int): O número de identificação do ônibus.
            employee_matricula (int): A matrícula do funcionário que realizou o acesso.
        """
        self.timestamp = timestamp
        self.bus_number = bus_number
        self.employee_matricula = employee_matricula