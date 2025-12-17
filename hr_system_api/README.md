# Sistema de Gerenciamento de Funcionários - RH - Backend (API)

Trata-se da API RESTful para a aplicação de gerenciamento de funcionários. Construída com Flask, ela gerencia toda a lógica de negócio e a comunicação com o banco de dados.

## ✨ Funcionalidades

* **Gerenciamento de Funcionários:** CRUD completo (Criar, Ler, Atualizar, Deletar) para registros de funcionários.
* **Gerenciamento de Anotações:** Adição e atualização de anotações vinculadas a cada funcionário.
* **Controle de Acesso ao Ônibus:**
    * Upload em massa dos registros de acesso aos ônibus via arquivo `.csv` (SOMENTE PARA TESTES).
    * Consultas gerais e detalhadas por funcionário, por número de ônibus ou por data.
* **Geração de Contrato:** Consumo de API Externa (APITemplate.io) para emissão de contrato de trabalho em PDF.
* **Geração de QR Codes:** Criação de PDFs com QR Codes das matrículas para a identificação dos funcionários.
* **Documentação Automática:** Interface Swagger UI para testar e entender os endpoints da API.

## 🚀 Tecnologias Utilizadas

* **Linguagem:** Python 3
* **Framework:** Flask com Flask-OpenAPI3
* **Banco de Dados:** SQLAlchemy ORM com SQLite
* **Segurança:** Auth0 (PyJWT)
* **Orquestração:** Docker Compose/Engine
* **Geração de PDF:** ReportLab e APITemplate.io
* **Validação de Dados:** Pydantic

## ⚙️ Configuração e Instalação

Siga os passos abaixo para configurar e executar o backend.

⚠️ Importante (arquivo .env): Para executar o projeto, é necessário um arquivo .env na raiz (/hr_system_api) com as variáveis de ambiente disponibilizadas separadamente.

### Pré-requisitos

* Python 3.8 ou superior
* `pip` (gerenciador de pacotes do Python)

### Passos

1.  **Clone o repositório**:
    ```bash
    git clone <url-do-repositorio>
    ```

#### ▶️ Como Executar a Aplicação Utilizando Ambiente Virtual

1.  **Navegue até a pasta raiz da aplicação, onde encontram-se o back-end e o front-end:**
    ```bash
    cd "diretório-raiz-da-aplicação"
    ```
2.  **Crie e ative um ambiente virtual:**
    * No Windows:
        ```bash
        python -m venv venv
        .\venv\Scripts\activate
        ```
    * No macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
3.  **Navegue até a pasta do back-end:**.
    ```bash
    cd "hr_system_api"
    ```
4.  **Instale as dependências:**.
    ```bash
    pip install -r requirements.txt
    ```
5.  **Executando a API:**.
    Com o ambiente virtual ativado e as dependências instaladas, execute o seguinte comando no terminal:
    ```bash
    flask run --host 0.0.0.0 --port 5000
    ```

#### 🐳 Como Executar a Aplicação Utilizando Orquestração Docker (Opção Mais Simples)

Se você tem o Docker instalado, pode subir os dois componentes (Front-end na porta 3000 e Back-end na porta 5000) com um único comando.
Se ainda não possui o Docker, instale a versão compatível com seu sistema operacional, disponível em: "https://www.docker.com/". Leia a documentação oficial para mais esclarecimentos.

1.  **Crie o arquivo `.env`** (na pasta `hr_system_api/`) e cole as chaves e credenciais dentro dele.
2.  **Navegue até a pasta do Front-end** (onde está o `docker-compose.yml`).
    ```bash
    cd ../hr_system_front
    ```
3.  **Execute a Aplicação:**
    Primeira vez, e quando fizer alterações:
    ```bash
    docker-compose up --build
    ```
    Demais vezes:
    ```bash
    docker-compose up
    ```
    (Este comando dispensa a criação manual do ambiente virtual e a execução separada do `flask run`).
    Após o início, a documentação Swagger estará disponível em: 👉 http://127.0.0.1:5000/openapi/swagger
    A interface do usuário poderá ser acessada em: * 👉 **[http://127.0.0.1:3000/](http://127.0.0.1:3000/)**

    Caso queira executar somente o Back-end, através de seu Dockerfile, execute os seguintes comandos no terminal dentro da pasta `hr_system_api`:

    Primeira vez, e quando fizer alterações:
    ```bash
    docker build -t hr_system_api .
    docker run -p 5000:5000 hr_system_api
    ```
    Demais vezes:
    ```bash
    docker run -p 5000:5000 hr_system_api
    ```


## 🔑 Testando Rotas Protegidas no Swagger (Avaliação Simplificada)

Para evitar a complexidade de configurar o fluxo OAuth2/ROPG (que exige Client Secret), foi implementado um **Token de Demonstração** exclusivo para testes no Swagger.

**Para Testar as Rotas (POST, PUT, DELETE, GET Protegidas):**

1.  **Obter o Token:** Vá para a rota `/test/get-demo-token` na documentação do Swagger. Clique em **"Try it out"** e **"Execute"**.
2.  **Copiar:** Copie o valor do campo `access_token` (em `Response body`), sem incluir as aspas duplas.
3.  **Autorizar:** Clique no botão verde **"Authorize"** (Cadeado) no topo do Swagger.
4.  **Colar:** Cole o token no campo de valor (Value) e clique em **Authorize**, e depois em Close.

Após a autorização, todas as rotas protegidas com o cadeado estarão abertas para testes.