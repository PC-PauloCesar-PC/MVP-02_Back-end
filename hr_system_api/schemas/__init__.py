#==============================================================================
# Módulo de inicialização do pacote 'schemas'.
# Este arquivo transforma o diretório 'schemas' em um pacote Python, permitindo
# importações organizadas.
# Utilizado em:
# - 'app.py': A importação 'from schemas import *' torna todos os esquemas
# disponíveis para os endpoints da API.
#==============================================================================

# Expõe todos os esquemas e funções do submódulo 'employee'.
from.employee import EmployeeSchema, EmployeeFindSchema, EmployeeFindToDelSchema, EmployeeViewSchema,\
      EmployeeListingSchema, EmployeeDelSchema, show_employees, show_employee, show_all_employees, \
      EmployeeUpdateSchema, EmployeeSearchSchema, EmployeeQRCodeSchema, EmployeeMatriculaQuery, EmployeeListingAllSchema, EmployeeUploadFormSchema, ContractDataSchema

# Expõe todos os esquemas e funções do submódulo 'bus_access'.
from.bus_access import BusAccessUploadResponseSchema, AccessDetailSchema, \
      EmployeeAccessHistorySchema, BusAccessTimestampSchema, EmployeeAccessByBusSchema, \
      BusAccessReportSchema, DailyEmployeeAccessSchema, DailyBusReportSchema,\
      DailyReportSchema, EmployeeInBusAccessSchema, BusAccessViewSchema, ListBusAccessSchema, \
      show_all_bus_accesses, BusAccessUploadFormSchema, BusNumberQuery, DateQuery

# Expõe o esquema padrão para representação de erros.
from.error import ErrorSchema

# Expõe todos os esquemas e funções do submódulo 'note'.
from.note import NoteSchema, NoteViewSchema, show_note, NoteSearchSchema, NoteUpdateSchema, NoteUploadFormSchema