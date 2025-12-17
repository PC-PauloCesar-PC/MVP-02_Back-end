#============================================================================
# Módulo que define todos os esquemas Pydantic relacionados aos funcionários.
#============================================================================

from pydantic import BaseModel, Field, computed_field, validator, field_validator
from typing import Optional, List, Union
from datetime import date

# Importação relativa para evitar problemas com importações circulares
from model.employee import Employee
from.note import NoteViewSchema

# Função auxiliar reutilizável para remover espaços em branco de strings.
# Utilizada em:
# - 'schemas/employee.py': Aplicada através dos validadores '_strip_fields' nas classes
#   'EmployeeSchema' e 'EmployeeUpdateSchema'.
def strip_string(cls, v):
    """Remove espaços em branco do início e do fim de um campo string."""
    if isinstance(v, str):
        return v.strip()
    return v

# Define o esquema para a criação de um novo funcionário.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'form' na função 'add_employee', validando
#   os dados recebidos no corpo da requisição POST.
class EmployeeSchema(BaseModel):
    """
    Define a estrutura e as regras de validação para os dados de um novo
    funcionário ao ser cadastrado na API.
    """

    nome: str = Field(..., max_length=100, example="Nome Sobrenome")
    cpf: int = Field(..., example=12345678911)
    identidade: int = Field(..., example=123456789)
    data_nascimento: date = Field(..., example="AAAA-MM-DD")
    genero: str = Field(..., max_length=1, example="M ou F ou X")
    endereco: str = Field(..., max_length=500,
                          example="Rua ABC, número 01, CEP: 123, bairro: DEF, cidade: GHI, estado: GH")
    tel_principal: str = Field(..., max_length=20,
                               example="+55 (99) 9 9999 9999")
    tel_secundario: Optional[str] = Field(
        None, max_length=20, example="+55 (99) 9 9999 9999")
    email: Optional[str] = Field(None,max_length=200, example="exemplo@exemplo.com")
    cargo: str = Field(..., max_length=100, example="Engenheiro de Software")
    salario: float = Field(..., example=999999.99)
    centro_custo: str = Field(..., max_length=20, example="ACB123456789")
    setor: str = Field(..., max_length=50, example="Engenharia")
    matricula_superior: int = Field(..., example=654321)
    nome_superior: str = Field(..., max_length=100, example="Nome Sobrenome")
    data_admissao: date = Field(..., example="AAAA-MM-DD")
    data_demissao: Optional[date] = Field(None, example="AAAA-MM-DD")
    status: str = Field(..., max_length=1, example="A -> Ativo, L -> Licença, D -> Desligado")
    first_note_text: Optional[str] = Field(None, example="Texto da primeira anotação a ser criada junto com o funcionário (opcional).")

    # Validador que converte campos numéricos (enviados como texto por formulários) para string.
    # Utilizado em:
    # - 'schemas/employee.py': Aplicado implicitamente pelo Pydantic nos campos definidos
    #   dentro da classe 'EmployeeSchema'.
    @field_validator('cpf', 'identidade', 'tel_principal', 'tel_secundario', 'centro_custo', 'setor', mode='before')
    @classmethod
    def format_fields_to_str(cls, v):
        """
        Garante que campos que podem ser numéricos mas são tratados como string
        sejam convertidos antes da validação principal.
        """
        if v is not None:
            return str(v)
        return v

    # Validador que limpa strings vazias ou "null" antes da validação.
    # Utilizado em:
    # - 'schemas/employee.py': Aplicado a todos os campos de 'EmployeeSchema' e 'EmployeeUpdateSchema'.
    @validator("*", pre=True)
    def parse_empty_str_as_none(cls, v):
        """
        Converte strings vazias ou "null" em None para garantir que campos
        opcionais sejam corretamente invalidados se não preenchidos.
        """
        if isinstance(v, str) and (v.lower() == "null" or v.strip() == ""):
            return None
        return v

    # Aplica a função 'strip_string' para remover espaços em branco de múltiplos campos.
    # Utilizado em: Implicitamente pelo Pydantic nos campos 'endereco', 'tel_principal',
    # 'tel_secundario', 'cargo', 'setor' e 'centro_custo' desta classe ('EmployeeSchema').
    _strip_fields = validator(
    'endereco', 'tel_principal', 'tel_secundario', 
    'cargo', 'setor', 'centro_custo', pre=True, allow_reuse=True
    )(strip_string)

    # Validador para normalizar nomes (remove espaços e aplica capitalização).
    # Utilizado em: Implicitamente pelo Pydantic nos campos 'nome' e 'nome_superior' desta classe.
    @validator('nome', 'nome_superior', pre=True)
    def normalize_names(cls, v):
        """Padroniza nomes: remove espaços e aplica capitalização de título."""
        if isinstance(v, str):
            # Ex: "  nome SOBRENOME  " -> "Nome Sobrenome"
            return v.strip().title()
        return v

    # Validador para normalizar e-mails (remove espaços e converte para minúsculas).
    # Utilizado em: Implicitamente pelo Pydantic no campo 'email' desta classe.
    @validator('email', pre=True)
    def normalize_email(cls, v):
        """Padroniza email: remove espaços e converte para minúsculas."""
        if isinstance(v, str):
            return v.strip().lower()
        return v

    # Validador para normalizar o campo de gênero (remove espaços e converte para maiúscula).
    # Utilizado em: Implicitamente pelo Pydantic no campo 'genero' desta classe.
    @validator('genero', pre=True)
    def normalize_genero(cls, v):
        """Padroniza gênero: remove espaços e converte para maiúscula."""
        if isinstance(v, str):
            # Ex: " m " -> "M"
            return v.strip().upper()
        return v

# Define o esquema para a resposta da API de um único funcionário (visualização).
# Utilizado em:
# - 'app.py': Nos decoradores de resposta das rotas '@app.post('/employee')' e '@app.put('/employee')'.
class EmployeeViewSchema(BaseModel):
    """
    Define a estrutura completa de um funcionário para ser exibida nas
    respostas da API.
    """
    nome: str
    matricula: int
    cpf: int
    identidade: int
    data_nascimento: date
    genero: str
    endereco: str
    tel_principal: str
    tel_secundario: str
    email: str
    cargo: str
    salario: float
    centro_custo: str
    setor: str
    matricula_superior: int
    nome_superior: str
    data_admissao: date
    data_demissao: date
    status: str
    notes: List[NoteViewSchema] = []

# Converte uma instância do modelo SQLAlchemy 'Employee' em um dicionário serializável (JSON).
# Utilizado em:
# - 'app.py': Nas funções 'add_employee' e 'update_employee' para formatar a resposta JSON de sucesso.
def show_employee(employee: Employee):
    """
    Formata um objeto de funcionário do banco de dados para a representação
    JSON que será enviada como resposta pela API.
    """
    return {
        "nome": employee.nome,
        "matricula": employee.matricula,
        "cpf": employee.cpf,
        "identidade": employee.identidade,
        "data_nascimento": employee.data_nascimento,
        "genero": employee.genero,
        "endereco": employee.endereco,
        "tel_principal": employee.tel_principal,
        "tel_secundario": employee.tel_secundario,
        "email": employee.email,
        "cargo": employee.cargo,
        "salario": employee.salario,
        "centro_custo": employee.centro_custo,
        "setor": employee.setor,
        "matricula_superior": employee.matricula_superior,
        "nome_superior": employee.nome_superior,
        "data_admissao": employee.data_admissao,
        "data_demissao": employee.data_demissao,
        "status": employee.status,
        "notes": [
            {
                "id": note.id,
                "text": note.text,
                "category": note.category,
                "created_at": note.created_at
            }
            for note in employee.notes
        ]
    }

# Define o esquema para os parâmetros de busca de um ou mais funcionários.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'query' na função 'get_employee'.
class EmployeeFindSchema(BaseModel):
    """
    Define os parâmetros de query opcionais para buscar um funcionário por nome,
    matrícula ou CPF.
    """
    nome: Optional[str] = Field(None, max_length=100, example="Nome Sobrenome")
    matricula: Optional[int] = Field(None, example=123456)
    cpf: Optional[int] = Field(None, example=12345678911)

# Define o esquema para os parâmetros de exclusão de um funcionário.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'query' na função 'del_employee'.
class EmployeeFindToDelSchema(BaseModel):
    """
    Define os parâmetros de query obrigatórios para deletar um funcionário,
    exigindo nome, matrícula e CPF para confirmação.
    """
    nome: str = Field(..., max_length=100, example="Nome Sobrenome")
    matricula: int = Field(..., example=123456)
    cpf: int = Field(..., example=12345678911)

# Define o esquema para identificar um funcionário pela matrícula em parâmetros de busca.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'query' na função 'update_employee'.
class EmployeeSearchSchema(BaseModel):
    """
    Define o parâmetro de query obrigatório 'matricula' para buscar um
    funcionário específico para atualização.
    """
    matricula: int = Field(..., example="123456")

# Define o esquema para a resposta da API contendo uma lista de funcionários.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.get('/employee')'.
class EmployeeListingSchema(BaseModel):
    """
    Define a estrutura da resposta JSON que contém uma lista de funcionários,
    usada em buscas que podem retornar múltiplos resultados.
    """
    employees: List[EmployeeViewSchema]

# Converte uma lista de objetos 'Employee' (SQLAlchemy) em um dicionário serializável.
# Utilizado em:
# - 'app.py': Dentro da função 'get_employee' para formatar a resposta JSON.
def show_employees(employees: List[Employee]):
    """
    Formata uma lista de objetos de funcionário do banco de dados para a
    representação JSON que será enviada como resposta pela API.
    """
    result = []

    for employee in employees:
        result.append({
            "nome": employee.nome,
            "matricula": employee.matricula,
            "cpf": employee.cpf,
            "identidade": employee.identidade,
            "data_nascimento": employee.data_nascimento,
            "genero": employee.genero,
            "endereco": employee.endereco,
            "tel_principal": employee.tel_principal,
            "tel_secundario": employee.tel_secundario,
            "email": employee.email,
            "cargo": employee.cargo,
            "salario": employee.salario,
            "centro_custo": employee.centro_custo,
            "setor": employee.setor,
            "matricula_superior": employee.matricula_superior,
            "nome_superior": employee.nome_superior,
            "data_admissao": employee.data_admissao,
            "data_demissao": employee.data_demissao,
            "status": employee.status,
            "notes": [
                {
                    "id": note.id,
                    "text": note.text,
                    "category": note.category,
                    "created_at": note.created_at
                }
                for note in employee.notes
            ]
        })

    # Retorna um dicionário com a lista de funcionários, caso existam nomes e sobrenomes iguais, e
    # se não existirem, retorna uma lista com somente 1 funcionário
    return {"employees": result}

# Define o esquema para a resposta da API contendo a lista de todos os funcionários.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.get('/employees')'.
class EmployeeListingAllSchema(BaseModel):
    """
    Define a estrutura da resposta JSON para a listagem de todos os
    funcionários cadastrados.
    """
    employees: List[EmployeeViewSchema]

# Converte uma lista de objetos 'Employee' e adiciona a contagem total.
# Utilizado em:
# - 'app.py': Dentro da função 'get_all_employees' para formatar a resposta JSON.
def show_all_employees(all_employees: List[Employee]):
    """
    Formata uma lista de todos os funcionários do banco, incluindo no corpo da
    resposta a contagem total de registros.
    """
    result_all = []
    
    for employee in all_employees:
        result_all.append({
            "nome": employee.nome,
            "matricula": employee.matricula,
            "cpf": employee.cpf,
            "identidade": employee.identidade,
            "data_nascimento": employee.data_nascimento,
            "genero": employee.genero,
            "endereco": employee.endereco,
            "tel_principal": employee.tel_principal,
            "tel_secundario": employee.tel_secundario,
            "email": employee.email,
            "cargo": employee.cargo,
            "salario": employee.salario,
            "centro_custo": employee.centro_custo,
            "setor": employee.setor,
            "matricula_superior": employee.matricula_superior,
            "nome_superior": employee.nome_superior,
            "data_admissao": employee.data_admissao,
            "data_demissao": employee.data_demissao,
            "status": employee.status,
            "notes": [
                {
                    "id": note.id,
                    "text": note.text,
                    "category": note.category,
                    "created_at": note.created_at
                }
                for note in employee.notes
            ],
            "total_employees": len(all_employees)
        })

    # Retorna um dicionário com a lista de todos os funcionários e a quantidade total de funcionários
    return {"all_employees": result_all}

# Define o esquema para a resposta de sucesso da exclusão de um funcionário.
# Utilizado em:
# - 'app.py': No decorador de resposta da rota '@app.delete('/employee')'.
class EmployeeDelSchema(BaseModel):
    """
    Define a estrutura da mensagem de sucesso ao deletar um funcionário.
    """
    mesage: str
    nome: str

# Define o esquema para a atualização de um funcionário.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'form' na função 'update_employee', validando
#   os dados recebidos no corpo da requisição PUT.
class EmployeeUpdateSchema(BaseModel):
    """
    Define a estrutura e as regras de validação para os dados de atualização
    de um funcionário. Todos os campos são opcionais.
    """
    nome: Optional[str] = Field(None, max_length=100, example="Nome Sobrenome")
    cpf: Optional[int] = Field(None, example=12345678911)
    identidade: Optional[int] = Field(None, example=123456789)
    data_nascimento: Optional[date] = Field(None, example="AAAA-MM-DD")
    genero: Optional[str] = Field(None, max_length=1, example="M ou F ou X")
    endereco: Optional[str] = Field(None, max_length=500,
                          example="Rua ABC, número 01, CEP: 123, bairro: DEF, cidade: GHI, estado: GH")
    tel_principal: Optional[str] = Field(None, max_length=20,
                               example="+55 (99) 9 9999 9999")
    tel_secundario: Optional[str] = Field(None, max_length=20,
                                          example="+55 (99) 9 9999 9999")
    email: Optional[str] = Field(None, max_length=200, example="exemplo@exemplo.com")
    cargo: Optional[str] = Field(None, max_length=100, example="Engenheiro de Software")
    salario: Optional[float] = Field(None, example=999999.99)
    centro_custo: Optional[str] = Field(None, max_length=20, example="ACB123456789")
    setor: Optional[str] = Field(None, max_length=50, example="Engenharia")
    matricula_superior: Optional[int] = Field(None, example=654321)
    nome_superior: Optional[str] = Field(None, max_length=100, example="Nome Sobrenome")
    data_admissao: Optional[date] = Field(None, example="AAAA-MM-DD")
    data_demissao: Optional[date] = Field(None, example="AAAA-MM-DD")
    status: Optional[str] = Field(None, max_length=1, example="A -> Ativo, L -> Licença, D -> Desligado")

    # Reutiliza o validador 'strip_string' para os campos especificados.
    # Utilizado em: Implicitamente pelo Pydantic nos campos 'endereco', 'tel_principal', etc.,
    # desta classe ('EmployeeUpdateSchema').
    _strip_fields = validator(
        'endereco', 'tel_principal', 'tel_secundario', 
        'cargo', 'setor', 'centro_custo', pre=True, allow_reuse=True
    )(strip_string)
    # Reutiliza a lógica da função 'normalize_names' da 'EmployeeSchema'.
    # Utilizado em: Implicitamente pelo Pydantic nos campos 'nome' e 'nome_superior' desta classe.
    _normalize_names = validator('nome', 'nome_superior', pre=True, allow_reuse=True)(EmployeeSchema.normalize_names.__func__)
    # Reutiliza a lógica da função 'normalize_email' da 'EmployeeSchema'.
    # Utilizado em: Implicitamente pelo Pydantic no campo 'email' desta classe.
    _normalize_email = validator('email', pre=True, allow_reuse=True)(EmployeeSchema.normalize_email.__func__)
    # Reutiliza a lógica da função 'normalize_genero' da 'EmployeeSchema'.
    # Utilizado em: Implicitamente pelo Pydantic no campo 'genero' desta classe.
    _normalize_genero = validator('genero', pre=True, allow_reuse=True)(EmployeeSchema.normalize_genero.__func__)

    # Reutiliza o validador que limpa strings vazias ou "null".
    # Utilizado em: Implicitamente pelo Pydantic em TODOS os campos desta classe ('EmployeeUpdateSchema').
    @validator("*", pre=True)
    def parse_empty_str_as_none(cls, v):
        """
        Converte strings "null" ou vazias em None antes da validação principal.
        Isso limpa os dados vindos de formulários que enviam campos vazios como strings.
        """
        if isinstance(v, str) and (v.lower() == "null" or v.strip() == ""):
            return None
        return v

# Define o esquema para a geração de QR Code.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'form' na função 'print_employee_tag'.
class EmployeeQRCodeSchema(BaseModel):
    """
    Define o campo 'matriculas' para a requisição de geração de
    etiquetas com QR Code.
    """
    matriculas: Union[str, int] = Field(..., 
                           description="Matrículas dos funcionários, separadas por vírgula (,) ou ponto e vírgula (;).",
                           example="1001, 1002; 1003")

# Define o esquema para buscar um funcionário pela matrícula (parâmetro de query).
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'query' na função 'get_accesses_by_employee'.
class EmployeeMatriculaQuery(BaseModel):
    matricula: int = Field(..., description="Matrícula do funcionário a ser consultado.")
    """
    Define a estrutura para um parâmetro de query que espera uma única
    matrícula de funcionário.
    """

#=============================================================================================
# SCHEMA PARA TESTES
#=============================================================================================

from werkzeug.datastructures import FileStorage

class EmployeeUploadFormSchema(BaseModel):
    """ Define o esquema para o upload de um arquivo CSV de funcionários. """
    file: bytes = Field(..., format="binary", description="Arquivo .csv com os dados dos funcionários.")

    @validator("file", pre=True)
    def read_file_storage_to_bytes(cls, v):
        if isinstance(v, FileStorage):
            return v.read()
        return v

#=============================================================================================

#============================================================================================
# SCHEMA PARA CONTRATO DE TRABALHO
#============================================================================================

class ContractDataSchema(BaseModel):
    """ 
    Define a estrutura para os dados do formulário de contrato.
    Todos os campos são recebidos como 'str' (texto)
    diretamente do FormData do front-end.
    """
    # Dados da Contratante (Empresa)
    contractRazaoSocial: str
    contractCNPJ: str
    contractCEP: str
    contractRua: str
    contractNumero: str
    contractBairro: str
    contractCidade: str
    contractUF: str
    contractRepresentante: str
    contractRepCPF: str

    # Dados do Contratado (Funcionário)
    contractMatricula: str
    contractNomeCompleto: str
    contractCPF: str
    contractIdentidade: str
    contractCargo: str
    contractSetor: str
    contractDataAdmissao: str
    contractFuncionarioCEP: str
    contractFuncionarioRua: str
    contractFuncionarioNumero: str
    contractFuncionarioBairro: str
    contractFuncionarioCidade: str
    contractFuncionarioUF: str
    contractFuncionarioComplemento: Optional[str] = None
    contractNacionalidade: str
    contractEstadoCivil: str
    contractSalarioBruto: str
    contractValorExtenso: str
    contractCidadeAdmissao: str

    @validator("contractFuncionarioComplemento", pre=True)
    def parse_empty_str_as_none(cls, v):
        if isinstance(v, str) and (v.lower() == "null" or v.strip() == ""):
            return None
        return v

    @validator(
        'contractCNPJ', 'contractCEP', 'contractNumero', 'contractRepCPF',
        'contractMatricula', 'contractCPF', 'contractIdentidade',
        'contractFuncionarioCEP', 'contractFuncionarioNumero', 'contractSalarioBruto',
        pre=True
    )
    def convert_numeric_to_string(cls, v):
        if isinstance(v, (int, float)):
            return str(v)
        return v