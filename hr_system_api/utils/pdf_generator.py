#=======================================================================================
# Módulo utilitário para a geração de arquivos PDF.
# Contém funções que abstraem a criação de PDFs complexos usando a biblioteca ReportLab.
#=======================================================================================

import io
import qrcode
from typing import List, Dict
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import cm

# Gera um arquivo PDF contendo etiquetas com nome e QR Code para uma lista de funcionários.
# Utilizado em:
# - `app.py`: Nas funções `print_employee_tag` e `print_all_employee_tags`.
def generate_multiple_labels_pdf(employees: List[Dict]) -> io.BytesIO:
    """
    Gera um PDF com múltiplas etiquetas (nome e QR Code) para uma lista de funcionários,
    organizando até 10 etiquetas por página em uma grade de 2x5.

    Args:
        employees (List[Dict]): Uma lista de dicionários, onde cada um contém
                                'matricula' e 'nome' de um funcionário.

    Returns:
        io.BytesIO: Um buffer de bytes em memória contendo o PDF gerado.
    """
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter

    # --- Configurações da Grade e Layout ---
    qr_size = 4 * cm
    items_per_page = 10
    cols = 2
    rows = 5
    
    # Calcular espaçamento horizontal (margens esquerda, central, direita iguais)
    h_margin = (width - (cols * qr_size)) / (cols + 1)
    # Calcular espaçamento vertical (margens superior e inferior)
    # Altura total de um item = QR Code + espaço para o nome + espaço entre linhas
    item_total_height = qr_size + 1 * cm 
    v_margin = (height - (rows * item_total_height)) / 2
    
    # Posições X para as duas colunas
    x_positions = [h_margin, h_margin * 2 + qr_size]
    
    # Posição Y inicial (a partir do topo da página)
    y_start = height - v_margin - item_total_height

    # --- Loop para gerar e posicionar as etiquetas ---
    for i, employee in enumerate(employees):
        # Controle de página: a cada 10 itens, cria uma nova página
        if i > 0 and i % items_per_page == 0:
            c.showPage()

        # Posição na grade da página atual (0 a 9)
        item_index_on_page = i % items_per_page
        
        # Determina a linha e coluna atual
        row = item_index_on_page // cols
        col = item_index_on_page % cols
        
        # Calcula as coordenadas X e Y para a etiqueta atual
        x = x_positions[col]
        y = y_start - (row * item_total_height)
        
        matricula = employee['matricula']
        nome = employee['nome']

        # 1. Gerar imagem do QR Code em memória
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=2)
        qr.add_data(str(matricula))
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
        
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        # 2. Adicionar o nome do funcionário
        c.setFont("Helvetica", 8) # Tamanho da fonte 8
        # Centraliza o nome acima do QR Code
        nome_x_pos = x + (qr_size / 2)
        nome_y_pos = y + qr_size + 0.2 * cm # Posição um pouco acima do QR Code
        c.drawCentredString(nome_x_pos, nome_y_pos, nome)

        # 3. Adicionar a imagem do QR Code
        qr_image_reader = ImageReader(qr_buffer)
        c.drawImage(qr_image_reader, x, y, width=qr_size, height=qr_size)

    # Finalizar e salvar o PDF
    c.showPage()
    c.save()
    pdf_buffer.seek(0)
    
    return pdf_buffer