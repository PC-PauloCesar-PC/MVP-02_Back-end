#=========================================================
# Módulo que define o modelo de dados para um Funcionário.
#=========================================================

# Importações necessárias do SQLAlchemy para definir o modelo Employee e suas colunas.
from sqlalchemy import Column, String, Integer, DateTime, Date, Float # Importa os tipos de dados das colunas
from sqlalchemy.orm import relationship # Importa a função relationship para definir relacionamentos entre tabelas

# Importações padrão do Python para manipulação de datas e tipos
from datetime import datetime
from datetime import date 
from typing import Union # Importa Union para permitir múltiplos tipos em anotações de tipo, como por exemplo Union[DateTime, None] que permite DateTime ou None

#---------------------------------------------------------------------------------------------------
# Importação relativa para evitar problemas com importações circulares, onde
# a construção do pacote fica em loop pois a uma "parte A" começa a ser contruída mas é pausada
# para construir a "parte B" que por sua vez depende da "parte A" que ainda não foi construída.
# Em python, recomenda-se sempre usar importações relativas em pacotes para evitar esses problemas.
# Exemplo de importação relativa:
# "from.base import Base" em vez de "from model import Base"
from.base import Base
#---------------------------------------------------------------------------------------------------

# Define a classe 'Employee' que mapeia para a tabela 'employee' no banco de dados.
# Utilizada em:
# - 'model/__init__.py': Para ser exposta como parte do pacote 'model'.
# - 'app.py': Nas funções 'generate_unique_registration', 'add_employee', 'add_note',
#   'get_all_employees', 'get_employee', 'del_employee', 'update_employee',
#   'print_employee_tag', 'print_all_employee_tags', e 'upload_bus_access_file' para queries.
# - 'schemas/employee.py': Como anotação de tipo nas funções 'show_employee',
#   'show_employees', e 'show_all_employees'.
class Employee(Base):
    """
    Representa um funcionário na tabela 'employee' do banco de dados.
    Esta classe define todas as colunas e os relacionamentos da tabela.
    """
    __tablename__ = 'employee'
    # ATENÇÃO: Os atributos estão em português para manter um padrão, pois alguns de seus equivalentes em inglês não me agradaram semanticamente
    # falando, como é o caso do equivalente em inglês do CPF.
    nome = Column(String(100))
    matricula = Column("pk_employee", Integer, unique=True, primary_key=True)
    cpf = Column(Integer)
    identidade = Column(Integer)
    data_nascimento = Column(Date)
    genero = Column(String(1))
    endereco = Column(String(500))
    tel_principal = Column(String(20))
    tel_secundario = Column(String(20))
    email = Column(String(200))
    cargo = Column(String(200))
    salario = Column(Float)
    centro_custo = Column(String(20))
    setor = Column(String(50))
    matricula_superior = Column(Integer)
    nome_superior = Column(String(100))
    data_admissao = Column(Date)
    data_demissao = Column(Date)
    status = Column(String(1), default='A')
    last_modification_date = Column(DateTime, default=datetime.now())

    # Relacionamento um-para-muitos com os registros de acesso ao ônibus.
    # cascade="all, delete-orphan" garante que os acessos sejam deletados se o funcionário for deletado.
    bus_accesses = relationship("BusAccess", back_populates="employee", cascade="all, delete-orphan")

    # Relacionamento um-para-muitos com as anotações.
    # cascade="all, delete-orphan" garante que os acessos sejam deletados se o funcionário for deletado.
    notes = relationship("Note", cascade="all, delete-orphan")

    # Método construtor para criar uma nova instância de Employee.
    def __init__(self, nome: str,
                matricula: int,
                cpf: int,
                identidade: int,
                data_nascimento: date,
                genero: str,
                endereco: str,
                tel_principal: str,
                tel_secundario: str,
                email: str,
                cargo: str,
                salario: float,
                centro_custo: str,
                setor: str,
                matricula_superior: int,
                nome_superior: str,
                data_admissao: Date,
                data_demissao: Union[Date, None] = None,
                status: str = 'A',
                last_modification_date: Union[DateTime, None] = None): # Manter a possibilidade de também ser None com 'Union[DateTime, None]' para futuras funcionalidades
        """
        Inicializa uma nova instância (um novo funcionário) com os dados fornecidos.

        Args:
            (vários): Parâmetros que correspondem às colunas da tabela para
                      criar um novo registro de funcionário.
        """

        # Inicializa os atributos do funcionário
        self.nome = nome
        self.matricula = matricula
        self.cpf = cpf
        self.identidade = identidade
        self.data_nascimento = data_nascimento
        self.last_modification_date = last_modification_date
        self.genero = genero
        self.endereco = endereco
        self.tel_principal = tel_principal
        self.tel_secundario = tel_secundario
        self.email = email
        self.cargo = cargo
        self.salario = salario
        self.centro_custo = centro_custo
        self.setor = setor
        self.matricula_superior = matricula_superior
        self.nome_superior = nome_superior
        self.data_admissao = data_admissao
        self.data_demissao = data_demissao
        self.status = status