#=============================================================================================
# Módulo que define todos os esquemas Pydantic relacionados aos registros de acesso ao ônibus.
#=============================================================================================

from pydantic import BaseModel, Field, validator
from typing import List
from datetime import datetime, time, date
from werkzeug.datastructures import FileStorage

# Define o esquema para um único detalhe de acesso (data, hora e ônibus).
# Utilizado em:
# - 'schemas/bus_access.py': Como tipo da lista 'accesses' dentro de 'EmployeeAccessHistorySchema'.
class AccessDetailSchema(BaseModel):
    """
    Representa o detalhe de um único acesso, contendo o momento exato
    e o número do ônibus.
    """
    timestamp: datetime
    bus_number: int

# Define o esquema da resposta JSON ao buscar o histórico de acessos de um funcionário.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.get('/bus_access/by_employee')'.
class EmployeeAccessHistorySchema(BaseModel):
    """
    Estrutura da resposta da API ao consultar todos os acessos de um
    funcionário específico.
    """
    matricula: int
    nome: str
    accesses: List[AccessDetailSchema]

# Define o esquema de um timestamp de acesso para a busca por ônibus.
# Utilizado em:
# - 'schemas/bus_access.py': Como tipo da lista 'accesses' dentro de 'EmployeeAccessByBusSchema'.
class BusAccessTimestampSchema(BaseModel):
    """Representa um único carimbo de data/hora de um acesso."""
    timestamp: datetime

# Define o esquema de um funcionário e seus respectivos acessos em um determinado ônibus.
# Utilizado em:
# - 'schemas/bus_access.py': Como tipo da lista 'employees' dentro de 'BusAccessReportSchema'.
class EmployeeAccessByBusSchema(BaseModel):
    """
    Agrupa os dados de um funcionário com a lista de seus acessos
    ao consultar por um ônibus (número) específico.
    """
    matricula: int
    nome: str
    accesses: List[BusAccessTimestampSchema]

# Define o esquema da resposta JSON completa ao buscar por número de ônibus.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.get('/bus_access/by_bus')'.
class BusAccessReportSchema(BaseModel):
    """
    Estrutura da resposta da API ao consultar todos os funcionários que
    acessaram um ônibus específico.
    """
    bus_number: int
    employees: List[EmployeeAccessByBusSchema]

# Define o esquema de um funcionário e seus horários de acesso em um dia.
# Utilizado em:
# - 'schemas/bus_access.py': Como tipo da lista 'accesses_by_employee' dentro de 'DailyBusReportSchema'.
class DailyEmployeeAccessSchema(BaseModel):
    """
    Agrupa os dados de um funcionário com a lista de horários de acesso
    em uma data específica.
    """
    matricula: int
    nome: str
    times: List[str]

# Define o esquema de um relatório diário para um único ônibus.
# Utilizado em:
# - 'schemas/bus_access.py': Como tipo da lista 'daily_report' dentro de 'DailyReportSchema'.
class DailyBusReportSchema(BaseModel):
    """
    Agrupa, para um ônibus, a lista de funcionários que o acessaram
    em uma data específica e seus respectivos horários.
    """
    bus_number: int
    accesses_by_employee: List[DailyEmployeeAccessSchema]

# Define o esquema da resposta JSON completa ao buscar por data.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.get('/bus_access/by_date')'.
class DailyReportSchema(BaseModel):
    """
    Estrutura da resposta da API ao consultar todos os acessos em
    uma data específica, agrupados por ônibus.
    """
    date: str
    daily_report: List[DailyBusReportSchema]

# Define um esquema simplificado de funcionário para ser aninhado em outras respostas.
# Utilizado em:
# - 'schemas/bus_access.py': Como tipo do campo 'employee' dentro de 'BusAccessViewSchema'.
class EmployeeInBusAccessSchema(BaseModel):
    """
    Representação mínima de um funcionário (matrícula e nome) para ser
    usada dentro de outras listagens.
    """
    matricula: int
    nome: str

# Define o esquema para a visualização de um único registro de acesso com dados do funcionário.
# Utilizado em:
# - 'schemas/bus_access.py': Como tipo da lista 'bus_accesses' dentro de 'ListBusAccessSchema'.
class BusAccessViewSchema(BaseModel):
    """
    Representa um registro de acesso completo, incluindo os dados
    básicos do funcionário associado.
    """
    id: int
    timestamp: datetime
    bus_number: int
    employee: EmployeeInBusAccessSchema

# Define o esquema para a listagem de todos os registros de acesso.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.get('/bus_access/all')'.
class ListBusAccessSchema(BaseModel):
    """
    Estrutura da resposta da API que contém uma lista de todos os
    registros de acesso.
    """
    bus_accesses: List[BusAccessViewSchema]

# Converte uma lista de objetos 'BusAccess' (SQLAlchemy) em um dicionário serializável.
# Utilizada em:
# - 'app.py': Dentro da função 'get_all_bus_accesses' para formatar a resposta.
def show_all_bus_accesses(accesses: List):
    """
    Formata uma lista de objetos de acesso do banco de dados para a
    representação JSON definida em ListBusAccessSchema.

    Args:
        accesses (List[BusAccess]): A lista de objetos BusAccess vinda do banco.

    Returns:
        dict: Um dicionário pronto para ser convertido em JSON pela API.
    """
    result = []
    for access in accesses:
        result.append({
            "id": access.id,
            "timestamp": access.timestamp,
            "bus_number": access.bus_number,
            "employee": {
                "matricula": access.employee.matricula,
                "nome": access.employee.nome
            }
        })
    return {"bus_accesses": result}

# Define o esquema para o parâmetro de busca por número do ônibus.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'query' na função 'get_employees_by_bus'.
class BusNumberQuery(BaseModel):
    """
    Define a estrutura esperada para o parâmetro de query 'bus_number'
    nas requisições GET.
    """
    bus_number: int = Field(..., description="Número do ônibus a ser consultado.")

# Define o esquema para o parâmetro de busca por data.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'query' na função 'get_accesses_by_date'.
class DateQuery(BaseModel):
    """
    Define a estrutura esperada para o parâmetro de query 'target_date'
    nas requisições GET.
    """
    target_date: date = Field(..., description="Data a ser consultada (formato AAAA-MM-DD).")

#=============================================================================================
# SCHEMA PARA TESTES
#=============================================================================================

# Define o esquema da resposta JSON após o processamento do upload do arquivo .csv.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.post('/test/populate_bus_access)'.
class BusAccessUploadResponseSchema(BaseModel):
    """
    Estrutura da resposta da API após o upload e processamento de um
    arquivo de registros de acesso.
    """
    registrations_added: int
    duplicates_skipped: int
    errors: List[str]

# Define o esquema para o formulário de upload de arquivo .csv.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'form' na função 'upload_bus_access_file'.
class BusAccessUploadFormSchema(BaseModel):
    """
    Valida o corpo de uma requisição de upload de arquivo, esperando um
    campo 'file' contendo os bytes de um arquivo .csv.
    """

    # Campo para receber o conteúdo binário do arquivo enviado.
    file: bytes = Field(..., format="binary", description="Arquivo .csv com os registros de acesso.")

    # Validador Pydantic que é executado antes da validação principal do campo 'file'.
    @validator("file", pre=True)
    def read_file_storage_to_bytes(cls, v):
        """
        Converte um objeto FileStorage do Werkzeug (usado pelo Flask) em bytes.
        Isso permite que o Pydantic valide o conteúdo do arquivo diretamente.
        """
        if isinstance(v, FileStorage):
            return v.read()
        return v