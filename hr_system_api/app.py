#=============================================================================
# Módulo principal da API Flask.
# Este arquivo contém a configuração da aplicação Flask, a definição de todas
# as rotas (endpoints), e a lógica de negócio para cada operação (CRUD)
# relacionada a funcionários, anotações e acessos ao ônibus.
#=============================================================================

from flask_openapi3 import OpenAPI, Info, Tag
from flask import redirect, request, make_response, jsonify
from urllib.parse import unquote
from sqlalchemy.exc import IntegrityError
from model import Session, Employee, BusAccess, Note
from logger import logger
from schemas import *
from flask_cors import CORS
from datetime import datetime, date
from flask import send_file
from utils.pdf_generator import generate_multiple_labels_pdf
from werkzeug.datastructures import FileStorage
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from itertools import groupby
# Para que a função de consulta/busca de funcionário faça a buscar pelo nome, matricula ou CPF.
from sqlalchemy import or_

from auth import requires_auth, AuthError, AUTH0_DOMAIN, DEMO_TOKEN

import re
import csv
import io
import os
import requests

from dotenv import load_dotenv
load_dotenv()

jwt_scheme = {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
security_schemes = {"bearerAuth": jwt_scheme}

info = Info(title="Minha API", version="1.0.0")
app = OpenAPI(__name__, info=info, security_schemes=security_schemes)
CORS(app, 
     resources={r"/*": {"origins": "*"}}, 
     supports_credentials=True, 
     allow_headers=["Content-Type", "Authorization"], 
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Bloco de Definição de Tags para Documentação
home_tag = Tag(name="Documentação",
               description="Seleção de documentação: Swagger, Redoc ou RapiDoc.")
employee_tag = Tag(name="Funcionário",
                   description="Adição, atualização, visualização e remoção de funcionários à base.")
bus_access_tag = Tag(name="Acesso ao Ônibus", description="Upload e consulta de registros de acesso.")
note_tag = Tag(name="Anotação (Note)", description="Adição de anotações aos funcionários.")
test_tag = Tag(name="Rotas de Teste", description="Endpoints para auxiliar no desenvolvimento e testes, como popular o banco de dados.")
test_token_tag = Tag(name="Token de Teste", description="Endpoint para obter um token de teste para uso no Swagger.")

# Endpoint raiz da API, que redireciona para a interface de documentação.
# Utilizado em: Chamado por um navegador ou cliente HTTP via requisição GET para a URL '/'.
@app.get('/', tags=[home_tag])
def home():
    """Redireciona para /openapi, tela que permite a escolha do estilo de documentação."""
    return redirect('/openapi')

# Tratamento de erro de Auth
@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Rota para obter o Token de Teste para o Swagger. Implementada para facilitar o uso do Swagger na hora da correção.
@app.get('/test/get-demo-token', tags=[test_token_tag],
         responses={"200": {"description": "Token de teste para o Swagger"}})
def get_demo_token():
    """Retorna um token simples para ser colado no campo 'Bearer Auth' do Swagger."""
    return {"access_token": DEMO_TOKEN}, 200

# Função auxiliar para gerar um número de matrícula único e sequencial.
# Utilizada em:
# - 'app.py': Chamada internamente pela função 'add_employee'.
def generate_unique_registration ():
    """Gera uma matrícula sequencial única a partir de 1000, baseada na última
    matrícula cadastrada no banco de dados.
    """
    session = Session()
    last_employee = session.query(Employee).order_by(Employee.matricula.desc()).first()
    if last_employee and last_employee.matricula is not None:
        registration  = last_employee.matricula + 1
    else:
        registration  = 1000
    session.close()
    return registration

# Endpoint para adicionar um novo funcionário.
# Utilizado em: Chamado pelo frontend via requisição POST para a URL '/employee'.
@app.post('/employee', tags=[employee_tag], 
          responses={"200": EmployeeViewSchema, "409": ErrorSchema, "400": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def add_employee(form: EmployeeSchema):
    """
    Adiciona um novo Funcionário à base de dados a partir dos dados
    validados pelo EmployeeSchema. Retorna os dados do funcionário criado.
    """
    matricula = generate_unique_registration()

    employee = Employee(
        nome=form.nome,
        matricula=matricula, 
        cpf=form.cpf,
        identidade=form.identidade,
        data_nascimento=form.data_nascimento,
        genero=form.genero,
        endereco=form.endereco,
        tel_principal=form.tel_principal,
        tel_secundario=form.tel_secundario,
        email=form.email,
        cargo=form.cargo,
        salario=form.salario,
        centro_custo=form.centro_custo,
        setor=form.setor,
        matricula_superior=form.matricula_superior,
        nome_superior=form.nome_superior,
        data_admissao=form.data_admissao,
        data_demissao=form.data_demissao,
        status=form.status,
        last_modification_date=datetime.now()  # Define a data de inserção como a data e hora atual
    )

    logger.debug(
        f"Adicionando o funcionário '{employee.nome}' à base de dados...")
    try:
        session = Session()
        session.add(employee)
        session.commit()
        session.refresh(employee)

        # Se uma primeira anotação foi fornecida, será criada aqui
        if form.first_note_text:
            primeira_anotacao = Note(
                text=form.first_note_text,
                employee_matricula=employee.matricula,
                category="Cadastro Inicial" # Categoria automática
            )
            session.add(primeira_anotacao)
            session.commit()
            session.refresh(employee) # Atualiza novamente para carregar a anotação na relação

        logger.debug(
            f"Funcionário '{employee.nome}' adicionado à base de dados com sucesso.")
        # Chama a função "show_employee" do "schemas.py" que converte o objeto SQLAlchemy "employee" em um formato
        # serializável (dicionário/JSON) para a resposta, e retorna o status HTTP 200 (OK), indicando sucesso.
        return show_employee(employee), 200

    except IntegrityError as e:
        # => Para fazer (pendência): garantir que a duplicidade do cpf seja razão do IntegrityError
        error_msg = "Funcionário já cadastrado na base."
        logger.warning(
            f"Erro ao adicionar o funcionário '{employee.nome}', {error_msg}")
        return {"mesage": error_msg}, 409

    except Exception as e:
        # Caso um erro fora do previsto
        error_msg = "Não foi possível cadastrar novo funcionário"
        logger.warning(
            f"Erro ao adicionar o funcionário '{employee.nome}', {error_msg}")
        return {"mesage": error_msg}, 400

# Endpoint para adicionar uma nova anotação a um funcionário.
# Utilizado em: Chamado pelo frontend via requisição POST para a URL '/note'.
@app.post('/note', tags=[note_tag],
          responses={"201": NoteViewSchema, "404": ErrorSchema, "400": ErrorSchema, "500": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def add_note(form: NoteSchema):
    """Adiciona uma nova anotação a um funcionário existente na base de dados."""
    session = Session()
    try:
        employee = session.query(Employee).filter(Employee.matricula == form.employee_matricula).first()
        if not employee:
            session.close()
            return {"mesage": f"Funcionário com matrícula {form.employee_matricula} não encontrado."}, 404
            
        note = Note(
            text=form.text,
            category=form.category,
            employee_matricula=form.employee_matricula
        )

        session.add(note)
        session.commit()
        session.refresh(note)
        logger.info(f"Nova anotação adicionada para o funcionário '{employee.nome}'.")
        return show_note(note), 201

    except IntegrityError as e:
        session.rollback()
        error_msg = "Ocorreu um erro de integridade ao salvar a anotação."
        logger.warning(f"{error_msg} - {e}")
        return {"mesage": error_msg}, 409

    except Exception as e:
        session.rollback()
        error_msg = "Não foi possível adicionar a anotação."
        logger.error(f"Erro ao adicionar anotação para matrícula #{form.employee_matricula}: {e}", exc_info=True)
        return {"mesage": error_msg}, 500
        
    finally:
        session.close()

# Endpoint para atualizar uma anotação existente.
# Utilizado em: Chamado pelo frontend via requisição PUT para a URL '/note'.
@app.put('/note', tags=[note_tag],
         responses={"200": NoteViewSchema, "404": ErrorSchema, "400": ErrorSchema, "500": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def update_note(query: NoteSearchSchema, form: NoteUpdateSchema):
    """
    Atualiza o texto e/ou a categoria de uma anotação existente,
    identificada pelo seu ID e pela matrícula do funcionário.
    """
    note_id = query.id
    employee_matricula = query.employee_matricula
    logger.debug(f"Iniciando atualização da anotação #{note_id} para o funcionário #{employee_matricula}...")
    session = Session()

    try:
        note = session.query(Note).filter(
            Note.id == note_id,
            Note.employee_matricula == employee_matricula
        ).first()

        if not note:
            session.close()
            error_msg = f"Anotação com ID {note_id} não encontrada ou não pertence ao funcionário de matrícula {employee_matricula}."
            logger.warning(error_msg)
            return {"mesage": error_msg}, 404
        
        # Cria um dicionário contendo apenas os campos que o usuário realmente enviou.
        update_data = form.model_dump(exclude_unset=True, exclude_none=True)

        if not update_data:
            return {"mesage": "Nenhum dado fornecido para atualização."}, 400
        
        # Itera sobre os dados enviados e atualiza dinamicamente o objeto 'note'
        for key, value in update_data.items():
            setattr(note, key, value)
            
        session.commit()
        logger.info(f"Anotação de ID #{note_id} atualizada com sucesso.")
        return show_note(note), 200

    except Exception as e:
        session.rollback()
        error_msg = "Não foi possível atualizar a anotação."
        logger.error(f"Erro ao atualizar anotação #{note_id}: {e}", exc_info=True)
        return {"mesage": error_msg}, 500
    finally:
        session.close()


# Endpoint para listar todos os funcionários cadastrados.
# Utilizado em: Chamado pelo frontend via requisição GET para a URL '/employees'.
@app.get('/employees', tags=[employee_tag],
         responses={"200": EmployeeListingAllSchema, "404": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def get_all_employees():
    """
    Busca e retorna uma lista com os dados de todos os funcionários
    cadastrados no banco de dados.
    """
    logger.debug(f"Coletando dados...")
    session = Session()
    employees = session.query(Employee).all()

    if not employees:
        # Se não há funcionários cadastrados
        return {"employees": []}, 200
    else:
        logger.debug(f"%d funcionários econtrados" % len(employees))
        # Retorna a representação de funcionário
        print(employees)
        # Chama uma função (do schemas.py) que formata a lista de objetos "employees" para um formato JSON adequado,
        # e etorna os dados com status 200.
        return show_all_employees(employees), 200

# Endpoint para buscar um ou mais funcionários por critérios específicos.
# Utilizado em: Chamado pelo frontend via requisição GET para a URL '/employee'.
@app.get('/employee', tags=[employee_tag],
         responses={"200": EmployeeListingSchema, "404": ErrorSchema, "400": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def get_employee(query: EmployeeFindSchema):
    """
    Busca funcionário(s) por matrícula, nome ou CPF. A busca é feita com o
    operador 'OU', retornando todos que correspondem a qualquer um dos critérios.
    Pelo menos um dos três campos (matrícula, nome ou cpf) deve ser fornecido.
    ATENÇÃO: Se todos os 3 campos contiverem dados válidos de funcionários distintos existentes no banco, a função retornará
    3 representações, uma de cada funcionário. Se 2 dessas 3 informações forem de um mesmo funcionário, a função retornará
    2 representações. Se as 3 informações forem do mesmo funcionário, a função retornará somente 1 representação.
    """
    matricula = query.matricula
    nome = query.nome
    cpf = query.cpf

    if not any([matricula, nome, cpf]):
        error_msg = "É necessário fornecer ao menos um critério de busca: matrícula, nome ou CPF."
        logger.warning(f"Requisição de busca inválida: {error_msg}")
        return {"mesage": error_msg}, 400

    search_criteria = []
    if matricula: search_criteria.append(f"matrícula='{matricula}'")
    if nome: search_criteria.append(f"nome='{nome}'")
    if cpf: search_criteria.append(f"cpf='{cpf}'")
    logger.debug(f"Coletando dados sobre funcionário com critérios: {', '.join(search_criteria)}...")

    print("Critérios de busca:", search_criteria)

    session = Session()
    filters = []
    
    if matricula:
        filters.append(Employee.matricula == matricula)

    if nome:
        filters.append(Employee.nome.ilike(f"%{nome.strip()}%"))

    if cpf:
        filters.append(Employee.cpf == cpf)
    
    print("filtros:", filters)

    # Faz a busca com o operador or_
    # O or_(*filters) aplica um "OU" entre todas as condições da lista
    employee = session.query(Employee).filter(or_(*filters)).all()

    if not employee:
        error_msg = "Funcionário não encontrado na base"
        logger.warning(f"Erro ao buscar o funcionário com os critérios fornecidos. {error_msg}")
        return {"mesage": error_msg}, 404
    else:
        logger.debug(f"{len(employee)} funcionário(s) encontrado(s).")
        return show_employees(employee), 200


# Endpoint para deletar um funcionário.
# Utilizado em: Chamado pelo frontend via requisição DELETE para a URL '/employee'.
@app.delete('/employee', tags=[employee_tag],
            responses={"200": EmployeeDelSchema, "404": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def del_employee(query: EmployeeFindToDelSchema):
    """
    Deleta um funcionário do banco de dados. Exige nome, matrícula e CPF
    como confirmação para a exclusão.
    """
    employee_nome = query.nome.strip()
    employee_matricula = query.matricula
    employee_cpf = query.cpf

    print(employee_nome)
    logger.debug(f"Deletando dados sobre o funcionário '{employee_nome}'...")
    session = Session()

    try:
        employee_to_delete = session.query(Employee).filter(
            Employee.nome.ilike(employee_nome),
            Employee.matricula == employee_matricula,
            Employee.cpf == employee_cpf
        ).first()

        if not employee_to_delete:
            error_msg = "Funcionário não encontrado ou dados não correspondem."
            logger.warning(f"Falha na exclusão: {error_msg} Matrícula: {employee_matricula}, Nome: {employee_nome}")
            return {"mesage": error_msg}, 404
        
        deleted_employee_name = employee_to_delete.nome
        session.delete(employee_to_delete)
        session.commit()

        logger.debug(f"Funcionário '{deleted_employee_name}' (matrícula #{employee_matricula}) deletado com sucesso.")
        return {"mesage": "Funcionário removido com sucesso", "Nome": deleted_employee_name}, 200

    except Exception as e:
        session.rollback()
        error_msg = "Ocorreu um erro ao tentar deletar o funcionário."
        logger.error(f"Erro na exclusão da matrícula {employee_matricula}: {e}", exc_info=True)
        return {"mesage": error_msg}, 400
    finally:
        session.close()

# Endpoint para atualizar os dados de um funcionário.
# Utilizado em: Chamado pelo frontend via requisição PUT para a URL '/employee'.
@app.put('/employee', tags=[employee_tag],
         responses={"200": EmployeeViewSchema, "404": ErrorSchema, "400": ErrorSchema, "409": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def update_employee(query: EmployeeSearchSchema, form: EmployeeUpdateSchema):
    """
    Atualiza parcialmente os dados de um funcionário existente, identificado
    pela matrícula. Apenas os campos enviados no corpo da requisição são alterados.
    """
    employee_matricula = query.matricula
    logger.debug(f"Iniciando atualização do funcionário de matrícula #{employee_matricula}...")

    session = Session()
    employee = session.query(Employee).filter(Employee.matricula == employee_matricula).first()

    if not employee:
        error_msg = "Funcionário não encontrado na base."
        logger.warning(f"Erro ao atualizar: funcionário de matrícula #{employee_matricula} não encontrado.")
        return {"mesage": error_msg}, 404

    # - exclude_unset=True: Garante que só campos enviados entrem.
    # - exclude_none=True: Remove os campos que foram enviados como 'null'.
    update_data = form.model_dump(exclude_unset=True, exclude_none=True)

    if not update_data:
        error_msg = "Nenhum dado fornecido para atualização."
        logger.warning(f"Tentativa de atualização da matrícula #{employee_matricula} sem dados.")
        return {"mesage": error_msg}, 400

    for key, value in update_data.items():
        setattr(employee, key, value)
    
    employee.last_modification_date = datetime.now()

    try:
        session.commit()
        logger.debug(f"Funcionário de matrícula #{employee_matricula} atualizado com sucesso.")
        return show_employee(employee), 200

    except IntegrityError as e:
        session.rollback()
        error_msg = "Erro de integridade ao atualizar. Verifique se dados únicos (como CPF) não estão duplicados."
        logger.warning(f"Erro de integridade ao atualizar funcionário #{employee_matricula}: {e}")
        return {"mesage": error_msg}, 409

    except Exception as e:
        session.rollback()
        error_msg = "Não foi possível atualizar o funcionário devido a um erro inesperado."
        logger.error(f"Erro inesperado ao atualizar funcionário #{employee_matricula}: {e}", exc_info=True)
        return {"mesage": error_msg}, 400

# Endpoint para gerar e retornar um PDF com etiquetas de QR Code para funcionários específicos.
# Utilizado em: Chamado pelo frontend via requisição POST para a URL '/employee/print_tag'.
# O método POST foi utilizado pois com ele é possível enviar uma grande quantidade de matrículas
# para a geração dos QR Codes, já que são enviadas no corpo da retuisição.
@app.post('/employee/print_tag', tags=[employee_tag],
          responses={"200": {"description": "Arquivo PDF com as etiquetas dos funcionários"}, 
                     "404": ErrorSchema, 
                     "400": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def print_employee_tag(form: EmployeeQRCodeSchema):
    """
    Gera um arquivo PDF contendo etiquetas com nome e QR Code para uma ou
    mais matrículas de funcionários fornecidas.
    A entrada deve conter apenas números separados por vírgula (,) ou ponto e vírgula (;).
    Qualquer outro formato será rejeitado.
    """
    matriculas_input = str(form.matriculas).strip()

    # Garantir que a string contém APENAS caracteres permitidos.
    if re.search(r'[^\d,;\s]', matriculas_input):
        error_msg = "Formato inválido. Caracteres especiais ou letras não são permitidos."
        logger.warning(f"Entrada de matrícula rejeitada por caractere inválido: '{matriculas_input}'")
        return {"mesage": error_msg}, 400

    # Garantir que a ESTRUTURA está correta.
    valid_structure_pattern = re.compile(r'^\d+(\s*[,;]\s*\d+)*$')
    if not valid_structure_pattern.fullmatch(matriculas_input):
        error_msg = "Formato de matrículas inválido. Use apenas vírgula (,) ou ponto e vírgula (;) como separadores entre os números."
        logger.warning(f"Entrada de matrícula rejeitada por estrutura inválida: '{matriculas_input}'")
        return {"mesage": error_msg}, 400

    try:
        requested_matriculas = set([int(m) for m in re.split(r'[,;]\s*', matriculas_input)])
    except (ValueError, TypeError):
        return {"mesage": "Ocorreu um erro ao processar os números das matrículas."}, 400

    logger.debug(f"Matrículas solicitadas: {sorted(list(requested_matriculas))}...")

    session = Session()
    try:
        employees = session.query(Employee).filter(Employee.matricula.in_(requested_matriculas)).all()

        if not employees:
            error_msg = f"Nenhuma das matrículas fornecidas foi encontrada: {sorted(list(requested_matriculas))}"
            logger.warning(error_msg)
            return {"mesage": error_msg}, 404
        
        found_matriculas = {emp.matricula for emp in employees}
        not_found_matriculas = requested_matriculas - found_matriculas
        employee_data = [{'matricula': emp.matricula, 'nome': emp.nome} for emp in employees]
        pdf_buffer = generate_multiple_labels_pdf(employee_data)
        logger.debug(f"Etiquetas para {len(employee_data)} funcionário(s) geradas com sucesso.")
        response = make_response(pdf_buffer)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=etiquetas_qrcodes.pdf'

        if not_found_matriculas:
            not_found_str = ', '.join(map(str, sorted(list(not_found_matriculas))))
            response.headers['X-Not-Found-Matriculas'] = not_found_str
            # Expõe o cabeçalho para o JavaScript poder ler (MUITO IMPORTANTE!)
            response.headers['Access-Control-Expose-Headers'] = 'X-Not-Found-Matriculas'

        return response
    
    except Exception as e:
        error_msg = "Ocorreu um erro ao gerar o arquivo PDF."
        logger.error(f"Erro na geração do PDF para as matrículas solicitadas: {e}", exc_info=True)
        return {"mesage": error_msg}, 500
    finally:
        session.close()

# Endpoint para gerar e retornar um PDF com etiquetas de QR Code para TODOS os funcionários.
# Utilizado em: Chamado pelo frontend via requisição GET para a URL '/employee/print_all_tags'.
# IMPORTANTE: Estudar um método melhor para gerar QR Code para todas as matrículas,
# visando a eficiência e redução do uso de recursos computacionais: memória RAM, por exemplo.
@app.get('/employee/print_all_tags', tags=[employee_tag],
         responses={"200": {"description": "Arquivo PDF com as etiquetas de todos os funcionários"},
                    "404": ErrorSchema,
                    "500": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def print_all_employee_tags():
    """
    Gera um arquivo PDF contendo etiquetas com nome e QR Code para todos os
    funcionários cadastrados na base.
    A função não requer parâmetros. Basta executar para iniciar o download do arquivo.
    """
    logger.debug("Iniciando geração de etiquetas para TODOS os funcionários...")
    session = Session()

    try:
        employees = session.query(Employee).order_by(Employee.nome).all()

        if not employees:
            error_msg = "Nenhum funcionário encontrado na base de dados."
            logger.warning(error_msg)
            return {"mesage": error_msg}, 404

        employee_data = [{'matricula': emp.matricula, 'nome': emp.nome} for emp in employees]
        pdf_buffer = generate_multiple_labels_pdf(employee_data)
        logger.debug(f"Etiquetas para todos os {len(employee_data)} funcionários geradas com sucesso.")

        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='etiquetas_todos_funcionarios.pdf'
        )
    
    except Exception as e:
        error_msg = "Ocorreu um erro ao gerar o arquivo PDF de todos os funcionários."
        logger.error(f"Erro na geração do PDF em massa: {e}", exc_info=True)
        return {"mesage": error_msg}, 500
    
    finally:
        session.close()


# Endpoint para gerar o contrato de trabalho
@app.post('/employee/generate_contract', tags=[employee_tag],
          responses={"200": {"description": "URL do PDF gerado"},
                     "400": ErrorSchema,
                     "500": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def generate_contract(form: ContractDataSchema):
    """
    Gera um PDF de contrato de trabalho usando um TEMPLATE SALVO
    na APITemplate.io V2 (endpoint /v2/create-pdf).
    """
    # --- Obter Chaves da API a partir das variáveis de ambiente ---
    api_key = os.getenv("APITEMPLATE_API_KEY")
    template_id = os.getenv("CONTRACT_TEMPLATE_ID") 

    if not api_key or not template_id:
        logger.error("APITEMPLATE_API_KEY ou CONTRACT_TEMPLATE_ID não definidas no .env")
        return {"mesage": "Serviço de geração de PDF não configurado no servidor."}, 500
        
    logger.debug(f"Iniciando geração de contrato (via APITemplate.io V2) para: {form.contractNomeCompleto}")

    # --- Construir Endereços Compostos ---
    endereco_filial = (
        f"{form.contractRua}, {form.contractNumero}, {form.contractBairro} - "
        f"{form.contractCidade}/{form.contractUF}, CEP: {form.contractCEP}"
    )

    complemento_str = f", {form.contractFuncionarioComplemento}" if form.contractFuncionarioComplemento else ""
    endereco_colaborador = (
        f"{form.contractFuncionarioRua}, {form.contractFuncionarioNumero}{complemento_str}, "
        f"{form.contractFuncionarioBairro} - {form.contractFuncionarioCidade}/{form.contractFuncionarioUF}, "
        f"CEP: {form.contractFuncionarioCEP}"
    )

    # --- Formatar Data de Admissão (AAAA-MM-DD -> DD/MM/AAAA) ---
    try:
        data_obj = datetime.strptime(form.contractDataAdmissao, '%Y-%m-%d')
        data_admissao_formatada = data_obj.strftime('%d/%m/%Y')
        logger.debug(f"Data de admissão formatada de '{form.contractDataAdmissao}' para '{data_admissao_formatada}'")
    except (ValueError, TypeError):
        logger.warning(f"Não foi possível formatar a data '{form.contractDataAdmissao}'. Usando o valor original.")
        data_admissao_formatada = form.contractDataAdmissao

    # --- Formatar Salário (Padrão BR)
    try:
        # Divide a string em parte inteira e decimal
        parts = form.contractSalarioBruto.split('.')
        part_inteira_str = parts[0]
        part_decimal_str = ""
        if len(parts) > 1:
            part_decimal_str = parts[1]

        # Converte a parte inteira para 'int'
        # e formata com separadores (que serão ',')
        part_inteira_int = int(part_inteira_str)
        part_inteira_formatada = f"{part_inteira_int:,}" # Ex: "10,000,000"
        
        # Troca os separadores da parte inteira para o padrão BR (',' -> '.')
        part_inteira_formatada_br = part_inteira_formatada.replace(',', '.') # Ex: "10.000.000"

        # Garante que a parte decimal tenha 2 dígitos (ex: "5" -> "50", "" -> "00")
        # E trunca se tiver mais de 2 dígitos (ex: "955" -> "95")
        part_decimal_formatada_br = part_decimal_str.ljust(2, '0')[:2] # Ex: "95" ou "50" ou "00"

        # Junta tudo com a vírgula do padrão BR
        salario_br_formatado = f"{part_inteira_formatada_br},{part_decimal_formatada_br}" # Ex: "10.000.000,95"

        logger.debug(f"Salário (string) formatado de '{form.contractSalarioBruto}' para '{salario_br_formatado}'")

    except (ValueError, TypeError, IndexError) as e:
        # Se falhar (ex: string vazia ou formato "abc"), usa o valor original
        logger.warning(f"Não foi possível formatar o salário '{form.contractSalarioBruto}'. Usando valor original. Erro: {e}")
        salario_br_formatado = form.contractSalarioBruto

    # --- Mapear dados do Schema para o Payload do Template ---
    payload_data = {
        # Contratante (Empresa)
        "Razao_Social": form.contractRazaoSocial,
        "endereco_filial": endereco_filial,
        "CNPJ": form.contractCNPJ,
        "representante_RH": form.contractRepresentante,
        "CPF": form.contractRepCPF,  # <-- {{CPF}} (Maiúsculo) do representante

        # Contratado (Funcionário)
        "nome_completo": form.contractNomeCompleto,
        "nacionalidade": form.contractNacionalidade,
        "estado_civil": form.contractEstadoCivil,
        "cpf": form.contractCPF,  # <-- {{cpf}} (Minúsculo) do funcionário
        "identidade": form.contractIdentidade,
        "endereco_colaborador": endereco_colaborador,
        
        # Detalhes do Contrato
        "cargo": form.contractCargo,
        "setor": form.contractSetor,
        "salario_bruto": salario_br_formatado,
        "valor_extenso": form.contractValorExtenso,
        "data_admissao": data_admissao_formatada,
        
        # Local/Data Assinatura (Conforme Cláusula Oitava e rodapé)
        "Cidade": form.contractCidade,  # <-- Cidade da Empresa para o Foro
        "UF": form.contractUF,          # <-- UF da Empresa para o Foro
        "cidade_admissao": form.contractCidadeAdmissao
    }

    # --- Chamar a API externa ---
    
    # A URL usa a V2 e passa o template_id como parâmetro de query
    api_url = f"https://rest.apitemplate.io/v2/create-pdf?template_id={template_id}"

    # O Header de autenticação usa X-API-KEY
    headers = {
        "X-API-KEY": api_key
    }
    
    # O JSON enviado é o payload_data diretamente
    json_data = payload_data

    try:
        response = requests.post(api_url, json=json_data, headers=headers)
        
        # Lança um erro para respostas 4xx ou 5xx
        response.raise_for_status() 
        
        api_result = response.json()
        download_url = api_result.get("download_url")

        if not download_url:
            logger.error("APITemplate.io SUCESSO, mas não retornou 'download_url'.")
            return {"mesage": "API de PDF não retornou um link para download."}, 500

        # Retorna a URL para o frontend
        logger.info(f"Contrato gerado com sucesso para {form.contractNomeCompleto}. URL: {download_url}")
        return {"download_url": download_url}, 200

    except requests.exceptions.HTTPError as http_err:
        # Tenta extrair a mensagem de erro específica da V2
        error_details = response.text
        try:
            error_json = response.json()
            error_details = error_json.get("message", response.text)
        except requests.exceptions.JSONDecodeError:
            pass # Mantém o 'error_details' como texto puro
            
        logger.error(f"Erro HTTP ao chamar APITemplate.io: {http_err} - Resposta: {error_details}")
        return {"mesage": f"Erro ao comunicar com a API de Tamplate: {response.status_code} {error_details}"}, 502

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Erro de Conexão ao chamar APITemplate.io: {req_err}")
        return {"mesage": "Erro de conexão com a API de Template."}, 504
    except Exception as e:
        logger.error(f"Erro inesperado na geração do contrato: {e}", exc_info=True)
        return {"mesage": "Erro interno do servidor ao gerar contrato."}, 500



# Endpoint para listar todos os acessos de um funcionário específico.
# Utilizado em: Chamado pelo frontend via requisição GET para a URL '/bus_access/by_employee'.
@app.get('/bus_access/by_employee', tags=[bus_access_tag],
         responses={"200": EmployeeAccessHistorySchema, "404": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def get_accesses_by_employee(query: EmployeeMatriculaQuery):
    """
    Retorna o histórico completo de acessos ao ônibus para um funcionário
    específico, identificado por sua matrícula.
    """
    matricula = query.matricula
    logger.debug(f"Buscando acessos para a matrícula #{matricula}...")
    session = Session()
    accesses = session.query(BusAccess).options(
        joinedload(BusAccess.employee)
    ).filter(BusAccess.employee_matricula == matricula).order_by(BusAccess.timestamp.asc()).all()
    
    if not accesses:
        session.close()
        return {"mesage": f"Nenhum registro de acesso encontrado para a matrícula {matricula}."}, 404
    
    employee = accesses[0].employee
    accesses_list = [
        {"timestamp": access.timestamp, "bus_number": access.bus_number} 
        for access in accesses
    ]
    
    session.close()
    return {
        "matricula": employee.matricula,
        "nome": employee.nome,
        "accesses": accesses_list,
        "total_accesses": len(accesses)
    }

# Endpoint para listar todos os funcionários que acessaram um ônibus específico.
# Utilizado em: Chamado pelo frontend via requisição GET para a URL '/bus_access/by_bus'.
@app.get('/bus_access/by_bus', tags=[bus_access_tag],
         responses={"200": BusAccessReportSchema, "404": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def get_employees_by_bus(query: BusNumberQuery):
    """
    Retorna uma lista de todos os funcionários que utilizaram um determinado
    ônibus, identificado pelo seu número.
    """
    bus_number = query.bus_number
    logger.debug(f"Buscando acessos no ônibus #{bus_number}...")
    session = Session()
    accesses = session.query(BusAccess).options(joinedload(BusAccess.employee)).filter(BusAccess.bus_number == bus_number).order_by(BusAccess.employee_matricula, BusAccess.timestamp).all()
    total_count = len(accesses)

    if not accesses:
        return {"mesage": f"Nenhum registro encontrado para o ônibus #{bus_number}."}, 404
    
    employees_data = []

    for matricula, group in groupby(accesses, key=lambda x: x.employee_matricula):
        access_list = list(group)
        employee = access_list[0].employee
        employees_data.append({
            "matricula": employee.matricula,
            "nome": employee.nome,
            "accesses": [{"timestamp": access.timestamp} for access in access_list]
        })

    session.close()
    return {"bus_number": bus_number, "employees": employees_data, "total_accesses": total_count}

# Endpoint para listar todos os acessos em uma data específica.
# Utilizado em: Chamado pelo frontend via requisição GET para a URL '/bus_access/by_date'.
@app.get('/bus_access/by_date', tags=[bus_access_tag],
         responses={"200": DailyReportSchema, "404": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def get_accesses_by_date(query: DateQuery):
    """
    Retorna um relatório de todos os acessos ocorridos em uma data específica,
    agrupados por ônibus e por funcionário.
    """
    target_date = query.target_date
    logger.debug(f"Buscando acessos para a data {target_date.strftime('%Y-%m-%d')}...")
    session = Session()
    accesses = session.query(BusAccess).options(joinedload(BusAccess.employee)).filter(func.date(BusAccess.timestamp) == target_date).order_by(BusAccess.bus_number, BusAccess.employee_matricula, BusAccess.timestamp).all()
    total_count = len(accesses)

    if not accesses:
        return {"mesage": f"Nenhum registro encontrado para a data {target_date.strftime('%d/%m/%Y')}."}, 404
        
    daily_report = []

    for bus, bus_group in groupby(accesses, key=lambda x: x.bus_number):
        bus_data = {"bus_number": bus, "accesses_by_employee": []}

        for matricula, employee_group in groupby(bus_group, key=lambda x: x.employee_matricula):
            access_list = list(employee_group)
            employee = access_list[0].employee
            bus_data["accesses_by_employee"].append({
                "matricula": employee.matricula,
                "nome": employee.nome,
                "times": [access.timestamp.time().strftime('%H:%M:%S') for access in access_list]
            })
        daily_report.append(bus_data)
        
    session.close()
    return {"date": target_date.strftime('%Y-%m-%d'), "daily_report": daily_report, "total_accesses": total_count}

# Endpoint para listar TODOS os registros de acesso do banco de dados.
# Utilizado em: Chamado pelo frontend via requisição GET para a URL '/bus_access/all'.
@app.get('/bus_access/all', tags=[bus_access_tag],
         responses={"200": ListBusAccessSchema, "404": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def get_all_bus_accesses():
    """
    Busca e retorna todos os registros de acesso ao ônibus existentes
    no banco de dados.
    """
    logger.debug("Buscando todos os registros de acesso...")
    session = Session()
    accesses = session.query(BusAccess).options(joinedload(BusAccess.employee)).order_by(BusAccess.timestamp.asc()).all()
    session.close()

    if not accesses:
        return {"mesage": "Nenhum registro de acesso encontrado."}, 404

    response_data = show_all_bus_accesses(accesses)
    response_data["total_accesses"] = len(accesses)
    return response_data

#=================================================
# ROTAS PARA TESTES. NÃO FAZEM PARTE DO FRONTEND.
#=================================================

# Endpoint para fazer o upload de um arquivo .csv com registros de acesso.
# Utilizado em: Chamado, exclusivamente na interface de documentação, via requisição POST para
# a URL '/test/populate_bus_access'.
# Essa rota não está sendo utilizada pela página Web pois o upload dos registros de acesso
# aos ônibus, para o banco de dados, deverá ser feito automaticamente pelo
# App Mobile (que decodificará os QR Codes e armazenará os dados localmente) assim que se conectar à
# internet (via dados móveis ou Wifi). Essa rota foi construída para teste de inserção de
# dados (no banco) oriundos de arquivo CSV.
@app.post('/test/populate_bus_access', tags=[test_tag],
          responses={"200": BusAccessUploadResponseSchema,"201": BusAccessUploadResponseSchema,
                     "400": ErrorSchema, "409": ErrorSchema, "500": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def upload_bus_access_file(form: BusAccessUploadFormSchema):
    """
    Processa um arquivo .csv enviado, validando (a estrutura do arquivo, incluindo o cabeçalho)
    e inserindo os registros de acesso ao ônibus no banco de dados.
    """
    uploaded_file = request.files.get('file')

    if uploaded_file is None or uploaded_file.filename == '' or not uploaded_file.filename.endswith('.csv'):
        return {"mesage": "Arquivo inválido. Por favor, envie um arquivo .csv."}, 400

    file_content_bytes = form.file
    
    if not file_content_bytes:
        return {"mesage": "O arquivo CSV enviado está completamente vazio."}, 400

    added_count = 0
    skipped_count = 0
    errors = []
    session = Session()
    try:
        stream = io.StringIO(file_content_bytes.decode("UTF-8"), newline=None)
        csv_reader = csv.DictReader(stream)
        expected_headers = {'date', 'time', 'matricula', 'bus_number'}

        # csv_reader.fieldnames contém os nomes das colunas lidas da primeira linha
        if not csv_reader.fieldnames or not expected_headers.issubset(set(csv_reader.fieldnames)):
            return {
                "mesage": "O cabeçalho do arquivo CSV é inválido ou está faltando.",
                "expected_columns": list(expected_headers)
            }, 400
            
        new_access_records = []
        processed_data_rows = 0

        for i, row in enumerate(csv_reader):
            processed_data_rows += 1
            line_num = i + 2

            try:
                matricula = int(row['matricula'])
                bus_number = int(row['bus_number'])
                timestamp = datetime.strptime(f"{row['date']} {row['time']}", "%Y-%m-%d %H:%M:%S")
                employee_exists = session.query(Employee).filter(Employee.matricula == matricula).first()

                if not employee_exists:
                    errors.append(f"Linha {line_num}: Funcionário com matrícula {matricula} não encontrado.")
                    continue

                record_exists = session.query(BusAccess).filter_by(
                    employee_matricula=matricula,
                    timestamp=timestamp
                ).first()

                if record_exists:
                    skipped_count += 1
                    continue
                
                new_access = BusAccess(
                    employee_matricula=matricula,
                    bus_number=bus_number,
                    timestamp=timestamp
                )
                new_access_records.append(new_access)

            except (ValueError, KeyError, TypeError) as e:
                errors.append(f"Linha {line_num}: Formato de dados inválido - {e}")

        if processed_data_rows == 0:
            return {"mesage": "O arquivo CSV contém apenas o cabeçalho, sem linhas de dados."}, 400
            
        if new_access_records:
            session.bulk_save_objects(new_access_records)
            session.commit()
            added_count = len(new_access_records)
        
        logger.info(f"Arquivo '{uploaded_file.filename}' processado: {added_count} adicionados, {skipped_count} pulados, {len(errors)} erros.")
        response_body = {
            "registrations_added": added_count,
            "duplicates_skipped": skipped_count,
            "errors": errors
        }

        if added_count > 0:
            return response_body, 201
        elif skipped_count > 0:
            response_body["mesage"] = "Operação concluída, mas nenhum novo registro foi adicionado pois todos já existiam."
            return response_body, 409
        else:
            return response_body, 200

    except Exception as e:
        session.rollback()
        logger.error(f"Erro crítico ao processar o arquivo '{uploaded_file.filename}': {e}", exc_info=True)
        return {"mesage": f"Ocorreu um erro inesperado no servidor: {e}"}, 500
    
    finally:
        session.close()


# Rota de teste para popular o banco de dados com funcionários a partir de um CSV
@app.post('/test/populate_employees', tags=[test_tag],
          responses={"201": {"description": "Funcionários cadastrados com sucesso"}, 
                     "400": ErrorSchema, "409": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def populate_employees_from_csv(form: EmployeeUploadFormSchema):
    """
    Popula o banco de dados com funcionários a partir de um arquivo CSV.

    Esta é uma rota de desenvolvimento para facilitar a criação de dados de teste.
    Retorna um relatório detalhado de sucessos, duplicatas e erros de formatação no arquivo.
    """
    file_content_bytes = form.file
    if not file_content_bytes:
        return {"mesage": "Arquivo CSV vazio ou inválido."}, 400

    new_employees = []
    errors = []
    added_count = 0
    skipped_count = 0
    session = Session()

    try:
        last_employee = session.query(Employee).order_by(Employee.matricula.desc()).first()
        if last_employee and last_employee.matricula is not None:
            next_registration_num = last_employee.matricula + 1
        else:
            next_registration_num = 1000

        stream = io.StringIO(file_content_bytes.decode("utf-8-sig"), newline=None)
        csv_reader = csv.DictReader(stream)

        for i, row in enumerate(csv_reader):
            line_num = i + 2
            try:
                if not row.get('cpf') or not row.get('nome'):
                    errors.append(f"Linha {line_num}: Faltando 'cpf' ou 'nome'.")
                    continue
                
                cpf_int = int(row['cpf'])
                existing_employee = session.query(Employee).filter(Employee.cpf == cpf_int).first()
                if existing_employee:
                    skipped_count += 1
                    continue

                new_employee = Employee(
                    nome=row['nome'],
                    # 2. Usa o número da variável e o incrementa. Não chama mais a função.
                    matricula=next_registration_num,
                    cpf=cpf_int,
                    identidade=int(row['identidade']),
                    data_nascimento=datetime.strptime(row['data_nascimento'], '%Y-%m-%d').date(),
                    genero=row['genero'],
                    endereco=row['endereco'],
                    tel_principal=row['tel_principal'],
                    tel_secundario=row.get('tel_secundario'),
                    email=row.get('email'),
                    cargo=row['cargo'],
                    salario=float(row['salario']),
                    centro_custo=row['centro_custo'],
                    setor=row['setor'],
                    matricula_superior=int(row['matricula_superior']),
                    nome_superior=row['nome_superior'],
                    data_admissao=datetime.strptime(row['data_admissao'], '%Y-%m-%d').date(),
                    data_demissao=datetime.strptime(row['data_demissao'], '%Y-%m-%d').date() if row.get('data_demissao') else None,
                    status=row['status'],
                    last_modification_date=datetime.now()
                )
                new_employees.append(new_employee)
                next_registration_num += 1
            
            except (ValueError, TypeError) as e:
                errors.append(f"Linha {line_num}: Erro de formato de dado (ex: data ou número inválido). Detalhe: {e}")
            except KeyError as e:
                errors.append(f"Linha {line_num}: Nome de coluna não encontrado no CSV: {e}")

        if new_employees:
            session.add_all(new_employees)
            session.commit()
            added_count = len(new_employees)
            logger.info(f"{added_count} novos funcionários adicionados via CSV.")
        
        message = f"{added_count} funcionários cadastrados."
        if skipped_count > 0:
            message += f" {skipped_count} ignorados por já existirem (CPF duplicado)."
        
        if errors:
            error_details = {"mesage": message, "errors_found": errors}
            return error_details, 400

        return {"mesage": message}, 201

    except Exception as e:
        session.rollback()
        logger.error(f"Erro crítico ao processar CSV: {e}", exc_info=True)
        return {"mesage": f"Ocorreu um erro crítico ao processar o arquivo: {e}"}, 500
    finally:
        session.close()

@app.post('/test/populate_notes', tags=[test_tag],
          responses={"201": {"description": "Anotações cadastradas com sucesso"}, 
                     "400": ErrorSchema}, security=[{"bearerAuth": []}])
@requires_auth
def populate_notes_from_csv(form: NoteUploadFormSchema):
    """
    Popula o banco de dados com anotações a partir de um arquivo CSV.

    Esta é uma rota de desenvolvimento. O CSV deve conter as colunas:
    'employee_matricula', 'category', 'text'.
    Anotações para matrículas de funcionários não existentes serão ignoradas.
    """
    file_content_bytes = form.file
    if not file_content_bytes:
        return {"mesage": "Arquivo CSV vazio ou inválido."}, 400

    new_notes = []
    errors = []
    added_count = 0
    skipped_count = 0
    session = Session()

    try:
        stream = io.StringIO(file_content_bytes.decode("utf-8-sig"), newline=None)
        csv_reader = csv.DictReader(stream)

        for i, row in enumerate(csv_reader):
            line_num = i + 2
            try:
                matricula = int(row['employee_matricula'])
                employee_exists = session.query(Employee).filter(Employee.matricula == matricula).first()
                
                if employee_exists:
                    new_note = Note(
                        employee_matricula=matricula,
                        category=row.get('category'),
                        text=row['text']
                    )
                    new_notes.append(new_note)
                else:
                    skipped_count += 1
                    errors.append(f"Linha {line_num}: Matrícula '{matricula}' não encontrada. Anotação ignorada.")

            except (ValueError, TypeError) as e:
                errors.append(f"Linha {line_num}: Erro de formato de dado (matrícula deve ser um número). Detalhe: {e}")
            except KeyError as e:
                errors.append(f"Linha {line_num}: Nome de coluna não encontrado no CSV: {e}")
        
        if new_notes:
            session.add_all(new_notes)
            session.commit()
            added_count = len(new_notes)
            logger.info(f"{added_count} novas anotações adicionadas via CSV.")
        
        message = f"{added_count} anotações cadastradas com sucesso."
        if skipped_count > 0:
            message += f" {skipped_count} anotações ignoradas por matrícula de funcionário não existente."
        
        if errors:
            error_details = {"mesage": message, "errors_found": errors}
            return error_details, 400

        return {"mesage": message}, 201

    except Exception as e:
        session.rollback()
        logger.error(f"Erro crítico ao processar CSV de anotações: {e}", exc_info=True)
        return {"mesage": f"Ocorreu um erro crítico ao processar o arquivo: {e}"}, 500
    finally:
        session.close()