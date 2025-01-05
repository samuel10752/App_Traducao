from tkinter import Tk, Label, filedialog, StringVar, messagebox, Toplevel, Entry, Text, Scrollbar, VERTICAL, RIGHT, Y
from tkinter.ttk import Progressbar, Button, Radiobutton
from deep_translator import GoogleTranslator
from fpdf import FPDF
import fitz  # PyMuPDF for PDF manipulation
from datetime import datetime
from PyPDF2 import PdfMerger
from ebooklib import epub
import threading
import os
# Global variable to control cancellation
cancel_process = False
# Default admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123"
# Function to log messages
def registrar_log(mensagem, pasta_logs, log_type="process"):
    """
    Logs messages based on type ('process', 'error', 'success').
    Creates separate log files for each type within a structured directory.
    """
    agora = datetime.now()
    log_mensagem = f"{agora.strftime('%d/%m/%Y %H:%M:%S')} - {mensagem}"
    print(log_mensagem)
    # Structured log directory with date subfolders
    date_folder = agora.strftime("%Y/%m/%d")
    log_dir = os.path.join(pasta_logs, date_folder)
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{log_type}_log.txt")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(log_mensagem + "\n")
# Function to browse files
def browse_file():
    global selected_file
    file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
    if file_path:
        selected_file_label.config(text=f"Arquivo Selecionado: {file_path}")
        selected_file = file_path
# Function to start translation
def start_translation():
    if not selected_file:
        messagebox.showerror("Erro", "Selecione um arquivo para traduzir!")
        return
    if messagebox.askyesno("Confirmação", "Tem certeza de que deseja iniciar a tradução?"):
        global cancel_process
        cancel_process = False
        translation_thread = threading.Thread(target=traduzir_pdf_em_paginas, args=(selected_file, output_format.get()))
        translation_thread.start()
# Function to cancel translation
def cancel_translation():
    if messagebox.askyesno("Confirmação", "Tem certeza de que deseja cancelar a tradução?"):
        global cancel_process
        cancel_process = True
# Function to exit the application
def exit_program():
    if messagebox.askyesno("Confirmação", "Tem certeza de que deseja sair?"):
        root.destroy()
# Admin login window
def admin_login():
    def validate_login():
        username = username_entry.get()
        password = password_entry.get()
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            messagebox.showinfo("Sucesso", "Login bem-sucedido!")
            admin_window.destroy()
            admin_dashboard()
        else:
            messagebox.showerror("Erro", "Credenciais inválidas!")
    admin_window = Toplevel(root)
    admin_window.title("Login de Admin")
    admin_window.geometry("350x200")
    admin_window.resizable(False, False)
    Label(admin_window, text="Usuário:", font=("Arial", 12)).pack(pady=5)
    username_entry = Entry(admin_window, font=("Arial", 12))
    username_entry.pack(pady=5)
    Label(admin_window, text="Senha:", font=("Arial", 12)).pack(pady=5)
    password_entry = Entry(admin_window, show="*", font=("Arial", 12))
    password_entry.pack(pady=5)
    Button(admin_window, text="Entrar", command=validate_login).pack(pady=10)
# Admin dashboard with log options
def admin_dashboard():
    dashboard_window = Toplevel(root)
    dashboard_window.title("Admin Dashboard")
    dashboard_window.geometry("400x300")
    Label(dashboard_window, text="Admin Dashboard", font=("Arial", 16, "bold")).pack(pady=10)
    Button(dashboard_window, text="Ver Logs de Erro", command=lambda: view_logs("error")).pack(pady=5)
    Button(dashboard_window, text="Ver Logs de Processo", command=lambda: view_logs("process")).pack(pady=5)
    Button(dashboard_window, text="Ver Logs de Sucesso", command=lambda: view_logs("success")).pack(pady=5)
# View logs based on type
def view_logs(log_type):
    log_dir = "log"
    logs_window = Toplevel(root)
    logs_window.title(f"Logs de {log_type.capitalize()}")
    logs_window.geometry("600x400")
    text_area = Text(logs_window, wrap="word", font=("Courier", 10))
    text_area.pack(side="left", fill="both", expand=True)
    scrollbar = Scrollbar(logs_window, orient=VERTICAL, command=text_area.yview)
    scrollbar.pack(side=RIGHT, fill=Y)
    text_area.configure(yscrollcommand=scrollbar.set)
    if not os.path.exists(log_dir):
        messagebox.showerror("Erro", "Diretório de logs não encontrado.")
        return
    for root_dir, _, files in os.walk(log_dir):
        for file_name in files:
            if log_type in file_name:
                log_path = os.path.join(root_dir, file_name)
                with open(log_path, "r", encoding="utf-8") as log_file:
                    text_area.insert("end", f"=== {log_path} ===\n")
                    text_area.insert("end", log_file.read())
                    text_area.insert("end", "\n\n")
# Function to translate the PDF
def traduzir_pdf_em_paginas(arquivo_entrada, output_format, idioma_destino="pt"):
    global cancel_process
    try:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        central_pasta_paginas = "Arquivo_Executavel/Paginas_tradutor"
        central_pasta_logs = "Arquivo_Executavel/Logs"
        pasta_paginas = os.path.join(central_pasta_paginas, f"traduzidas_{timestamp}")
        pasta_logs = os.path.join(central_pasta_logs, f"log_{timestamp}")
        pasta_arquivos_finais = os.path.join("Arquivo_Executavel/Arquivos_prontos", f"traduzido_{timestamp}")
        os.makedirs(pasta_paginas, exist_ok=True)
        os.makedirs(pasta_logs, exist_ok=True)
        os.makedirs(pasta_arquivos_finais, exist_ok=True)
        registrar_log(f"Tradução iniciada em: {timestamp}", pasta_logs, "process")
        translator = GoogleTranslator(source='en', target=idioma_destino)
        documento = fitz.open(arquivo_entrada)
        num_pages = len(documento)
        translated_pages = []
        content_for_epub = []
        unicode_font = "Arquivo_Executavel/fonte/DejaVuSans.ttf"
        if not os.path.exists(unicode_font):
            full_path = os.path.abspath(unicode_font)
            messagebox.showerror("Erro", f"A fonte Unicode {full_path} não foi encontrada. "
                                          f"Baixe a fonte e coloque-a no diretório do script ou atualize o caminho.")
            return

        largura_a4 = 210
        altura_a4 = 297
        for numero_pagina in range(num_pages):
            if cancel_process:
                registrar_log("Processo cancelado pelo usuário.", pasta_logs, "error")
                messagebox.showinfo("Cancelado", "O processo foi cancelado pelo usuário.")
                return
            pagina = documento[numero_pagina]
            registrar_log(f"Processando página {numero_pagina + 1} de {num_pages}", pasta_logs, "process")
            texto_original = pagina.get_text()
            traducao = translator.translate(texto_original) if texto_original.strip() else ""
            content_for_epub.append(traducao)
            imagens = pagina.get_images(full=True)
            pdf = FPDF(unit='mm', format='A4')
            pdf.add_page()
            pdf.add_font("DejaVuSans", '', unicode_font, uni=True)
            pdf.set_font("DejaVuSans", size=10)
            y_offset = 10
            if imagens:
                for img_index, img in enumerate(imagens, start=1):
                    xref = img[0]
                    try:
                        base_imagem = documento.extract_image(xref)
                        imagem_bytes = base_imagem["image"]
                        ext = base_imagem["ext"]
                        caminho_imagem_temp = f"temp_imagem_{numero_pagina + 1}_{img_index}.{ext}"
                        with open(caminho_imagem_temp, "wb") as f:
                            f.write(imagem_bytes)
                        largura_imagem = base_imagem["width"] * 0.264583
                        altura_imagem = base_imagem["height"] * 0.264583
                        if largura_imagem > 200 or altura_imagem > 230:
                            proporcao = max(largura_a4 / largura_imagem, altura_a4 / altura_imagem)
                            largura_final = largura_imagem * proporcao
                            altura_final = altura_imagem * proporcao
                            pos_x = (largura_a4 - largura_final) / 2
                            pos_y = (altura_a4 - altura_final) / 2
                        elif largura_imagem < 150 and altura_imagem < 150:
                            largura_final = 100 * 0.264583
                            altura_final = 100 * 0.264583
                            pos_x = (210 - largura_final) / 2
                            pos_y = 20
                            y_offset = pos_y + altura_final + 20
                        else:
                            proporcao = min(largura_a4 / largura_imagem, altura_a4 / altura_imagem)
                            largura_final = largura_imagem * proporcao
                            altura_final = altura_imagem * proporcao
                            pos_x = (largura_a4 - largura_final) / 2
                            pos_y = (altura_a4 - altura_final) / 2
                        pdf.image(caminho_imagem_temp, x=pos_x, y=pos_y, w=largura_final, h=altura_final)
                        os.remove(caminho_imagem_temp)
                    except Exception as e:
                        registrar_log(f"Erro ao processar imagem {img_index} na página {numero_pagina + 1}: {e}", pasta_logs, "error")
            pdf.set_y(y_offset)
            pdf.multi_cell(0, 6, traducao)
            nome_pagina = os.path.join(pasta_paginas, f"pagina_{numero_pagina + 1}.pdf")
            pdf.output(nome_pagina)
            translated_pages.append(nome_pagina)
            progress_var.set((numero_pagina + 1) / num_pages * 100)
            root.update_idletasks()
        documento.close()
        if output_format == "PDF":
            merged_file = filedialog.asksaveasfilename(defaultextension=".pdf",
                                                       filetypes=[("PDF files", "*.pdf")],
                                                       title="Salvar arquivo PDF traduzido")
            if merged_file:
                merger = PdfMerger()
                for pagina in translated_pages:
                    merger.append(pagina)
                merger.write(merged_file)
                merger.close()
                registrar_log(f"PDF traduzido salvo em: {merged_file}", pasta_logs, "success")
                messagebox.showinfo("Sucesso", f"PDF traduzido salvo em: {merged_file}")
        elif output_format == "EPUB":
            epub_file = filedialog.asksaveasfilename(defaultextension=".epub",
                                                     filetypes=[("EPUB files", "*.epub")],
                                                     title="Salvar arquivo EPUB traduzido")
            if epub_file:
                book = epub.EpubBook()
                book.set_title(os.path.basename(arquivo_entrada))
                book.set_language('pt')
                book.add_author("Autor Traduzido")
                for i, content in enumerate(content_for_epub, start=1):
                    chapter = epub.EpubHtml(title=f"Página {i}", file_name=f"pagina_{i}.xhtml", lang='pt')
                    chapter.content = f"<h1>Página {i}</h1><p>{content}</p>"
                    book.add_item(chapter)
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())
                epub.write_epub(epub_file, book, {})
                registrar_log(f"EPUB traduzido salvo em: {epub_file}", pasta_logs, "success")
                messagebox.showinfo("Sucesso", f"EPUB traduzido salvo em: {epub_file}")
    except Exception as e:
        registrar_log(f"Erro ao processar o arquivo: {e}", pasta_logs, "error")
        messagebox.showerror("Erro", f"Erro ao processar o arquivo: {e}")
# Main UI
selected_file = None
root = Tk()
root.title("Tradutor de PDF")
root.geometry("500x550")
root.resizable(False, False)
Label(root, text="Tradutor de PDF", font=("Arial", 16, "bold")).pack(pady=10)
Label(root, text="Selecione o arquivo PDF para traduzir:", font=("Arial", 12)).pack(pady=5)
Button(root, text="Selecionar Arquivo", command=browse_file).pack(pady=5)
selected_file_label = Label(root, text="Nenhum arquivo selecionado", font=("Arial", 10), fg="gray")
selected_file_label.pack(pady=5)
Label(root, text="Selecione o formato de saída:", font=("Arial", 12)).pack(pady=5)
output_format = StringVar(value="PDF")
Radiobutton(root, text="PDF", variable=output_format, value="PDF").pack()
Radiobutton(root, text="EPUB", variable=output_format, value="EPUB").pack()
Label(root, text="Progresso:", font=("Arial", 12)).pack(pady=5)
progress_var = StringVar(value=0)
progress_bar = Progressbar(root, orient="horizontal", length=400, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)
Button(root, text="Iniciar Tradução", command=start_translation).pack(pady=10)
Button(root, text="Cancelar Tradução", command=cancel_translation).pack(pady=10)
Button(root, text="Acessar Admin", command=admin_login).pack(pady=10)
Button(root, text="Sair", command=exit_program).pack(pady=10)
root.mainloop()