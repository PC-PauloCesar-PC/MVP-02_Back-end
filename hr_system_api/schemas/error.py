#==================================================================
# Módulo que define o esquema padrão para mensagens de erro da API.
#==================================================================

from pydantic import BaseModel

# Define a estrutura de uma mensagem de erro JSON.
# Utilizado em:
# - 'app.py': Nos decoradores de resposta de TODAS as rotas que podem retornar um
#   erro padrão (400, 404, 409, 500), incluindo:
#   - @app.post('/employee')
#   - @app.post('/note')
#   - @app.put('/note')
#   - @app.get('/employees')
#   - @app.get('/employee')
#   - @app.delete('/employee')
#   - @app.put('/employee')
#   - @app.post('/employee/print_tag')
#   - @app.get('/employee/print_all_tags')
#   - @app.post('/bus_access/upload')
#   - @app.get('/bus_access/by_employee')
#   - @app.get('/bus_access/by_bus')
#   - @app.get('/bus_access/by_date')
#   - @app.get('/bus_access/all')
class ErrorSchema(BaseModel):
    """ Define como uma mensagem de erro padrão será representada na API. """
    mesage: str