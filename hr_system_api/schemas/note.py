#=========================================================================================
# Módulo que define todos os esquemas Pydantic relacionados às anotações dos funcionários.
#=========================================================================================

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

# Define o esquema para adicionar uma nova anotação.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'form' na função 'add_note'.
class NoteSchema(BaseModel):
    """ Define a estrutura de dados para criar uma nova anotação. """
    employee_matricula: int
    text: str
    category: Optional[str] = None

# Define o esquema para exibir uma anotação na resposta da API.
# Utilizado em:
# - 'app.py': Nos decoradores de resposta das rotas '@app.post('/note')' e '@app.put('/note')'.
# - 'schemas/employee.py': Como tipo da lista 'notes' dentro de 'EmployeeViewSchema'.
class NoteViewSchema(BaseModel):
    """ Define como os dados de uma anotação serão exibidos. """
    id: int
    text: str
    category: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Converte um objeto 'Note' (SQLAlchemy) em um dicionário serializável.
# Utilizado em:
# - 'app.py': Nas funções 'add_note' e 'update_note' para formatar a resposta JSON de sucesso.
def show_note(note):
    """ Converte um objeto Note do SQLAlchemy para um dicionário JSON serializável. """
    return {
        "id": note.id,
        "text": note.text,
        "category": note.category,
        "created_at": note.created_at
    }

# Define o esquema para os parâmetros de busca de uma anotação específica.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'query' na função 'update_note'.
class NoteSearchSchema(BaseModel):
    """
    Define a estrutura para buscar uma anotação específica, exigindo o ID
    da anotação e a matrícula do funcionário.
    """
    id: int = Field(..., description="ID da anotação a ser alterada.")
    employee_matricula: int = Field(..., description="Matrícula do funcionário ao qual a anotação pertence.")

# Define o esquema para atualizar uma anotação existente.
# Utilizado em:
# - 'app.py': Como tipo do parâmetro 'form' na função 'update_note'.
class NoteUpdateSchema(BaseModel):
    """
    Define a estrutura dos dados a serem alterados em uma anotação.
    Ambos os campos são opcionais.
    """
    text: Optional[str] = Field(None, description="O novo texto corrigido para a anotação.")
    category: Optional[str] = Field(None, description="A nova categoria para a anotação.")

    # Validador que limpa strings vazias ou "null" antes da validação.
    # Utilizado em: Implicitamente pelo Pydantic em todos os campos desta classe ('NoteUpdateSchema').    
    @validator("*", pre=True)
    def parse_empty_str_as_none(cls, v):
        """
        Converte strings "null" ou vazias em None antes da validação principal.
        Isso limpa os dados vindos de formulários que enviam campos vazios como strings.
        """
        if isinstance(v, str) and (v.lower() == "null" or v.strip() == ""):
            return None
        return v
    


#=============================================================================================
# SCHEMA PARA TESTES
#=============================================================================================

from werkzeug.datastructures import FileStorage

# Defina este novo Schema antes da rota que o utiliza (pode ser junto ao outro Schema de upload)
class NoteUploadFormSchema(BaseModel):
    """ Define o esquema para o upload de um arquivo CSV de anotações. """
    file: bytes = Field(..., format="binary", description="Arquivo .csv com os dados das anotações.")

    @validator("file", pre=True)
    def read_file_storage_to_bytes(cls, v):
        if isinstance(v, FileStorage):
            return v.read()
        return v