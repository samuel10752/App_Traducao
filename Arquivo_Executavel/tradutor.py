from tkinter import Tk, Label, filedialog, StringVar, messagebox, Toplevel, Entry, Text, Scrollbar, VERTICAL, RIGHT, Y
from tkinter.ttk import Progressbar, Button, Radiobutton
from ebooklib import epub
import fitz  # PyMuPDF for PDF manipulation
import threading
import os
from datetime import datetime

# Global variable to control cancellation
cancel_process = False

# Function to log messages
def registrar_log(mensagem, pasta_logs, log_type="process"):
    agora = datetime.now()
    log_mensagem = f"{agora.strftime('%d/%m/%Y %H:%M:%S')} - {mensagem}"
    print(log_mensagem)
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

# Function to start EPUB conversion
def start_conversion():
    if not selected_file:
        messagebox.showerror("Erro", "Selecione um arquivo para converter!")
        return
    if messagebox.askyesno("Confirmação", "Tem certeza de que deseja iniciar a conversão?"):
        global cancel_process
        cancel_process = False
        conversion_thread = threading.Thread(target=convert_pdf_to_epub, args=(selected_file,))
        conversion_thread.start()

# Function to cancel conversion
def cancel_conversion():
    if messagebox.askyesno("Confirmação", "Tem certeza de que deseja cancelar a conversão?"):
        global cancel_process
        cancel_process = True

# Convert PDF to EPUB
def convert_pdf_to_epub(pdf_path):
    global cancel_process
    try:
        output_dir = filedialog.askdirectory(title="Selecione o diretório de saída")
        if not output_dir:
            return

        registrar_log(f"Iniciando conversão para EPUB: {pdf_path}", "Logs", "process")

        # Abrir o PDF
        pdf_document = fitz.open(pdf_path)
        book = epub.EpubBook()

        # Configurar metadados
        book.set_identifier("id123456")
        book.set_title(os.path.basename(pdf_path).replace(".pdf", ""))
        book.set_language("pt")
        book.add_author("Desconhecido")

        chapters = []

        for page_num in range(len(pdf_document)):
            if cancel_process:
                registrar_log("Processo cancelado pelo usuário.", "Logs", "error")
                messagebox.showinfo("Cancelado", "O processo foi cancelado pelo usuário.")
                return

            page = pdf_document[page_num]
            text = page.get_text("text")  # Obter texto bruto
            images = page.get_images(full=True)

            # Criar capítulo
            chapter = epub.EpubHtml(title=f"Página {page_num + 1}", file_name=f"page_{page_num + 1}.xhtml", lang="pt")
            content = f"<h1>Página {page_num + 1}</h1><p>{text}</p>"

            # Adicionar imagens ao capítulo
            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = pdf_document.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_name = f"page_{page_num + 1}_img_{img_index + 1}.{image_ext}"

                # Salvar imagem no EPUB
                epub_image = epub.EpubItem(
                    uid=image_name,
                    file_name=f"images/{image_name}",
                    media_type=f"image/{image_ext}",
                    content=image_bytes
                )
                book.add_item(epub_image)
                content += f'<img src="images/{image_name}" alt="Imagem {img_index + 1}">'

            chapter.content = content
            book.add_item(chapter)
            chapters.append(chapter)

            # Atualizar progresso
            progress_var.set((page_num + 1) / len(pdf_document) * 100)
            root.update_idletasks()

        # Adicionar navegação
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Definir a estrutura do EPUB
        book.spine = ["nav"] + chapters

        # Adicionar estilo CSS com tamanho de fonte fixo
        style = """
        body {
            font-family: Arial, sans-serif;
            font-size: 10px;
            line-height: 1.5;
            margin: 0;
            padding: 10px;
        }
        h1 {
            font-size: 14px;
            text-align: center;
        }
        p {
            margin: 10px 0;
            text-align: justify;
        }
        img {
            display: block;
            margin: 20px auto;
            max-width: 100%;
            height: auto;
        }
        """
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)

        # Salvar o EPUB
        output_file = os.path.join(output_dir, f"{os.path.basename(pdf_path).replace('.pdf', '')}.epub")
        epub.write_epub(output_file, book)
        registrar_log(f"EPUB salvo em: {output_file}", "Logs", "success")
        messagebox.showinfo("Sucesso", f"EPUB gerado com sucesso: {output_file}")
    except Exception as e:
        registrar_log(f"Erro ao converter o arquivo: {e}", "Logs", "error")
        messagebox.showerror("Erro", f"Erro ao converter o arquivo: {e}")

# Main UI
selected_file = None
root = Tk()
root.title("Conversor de PDF para EPUB")
root.geometry("500x400")
root.resizable(False, False)

Label(root, text="Conversor de PDF para EPUB", font=("Arial", 16, "bold")).pack(pady=10)
Label(root, text="Selecione o arquivo PDF para converter:", font=("Arial", 12)).pack(pady=5)
Button(root, text="Selecionar Arquivo", command=browse_file).pack(pady=5)

selected_file_label = Label(root, text="Nenhum arquivo selecionado", font=("Arial", 10), fg="gray")
selected_file_label.pack(pady=5)

Label(root, text="Progresso:", font=("Arial", 12)).pack(pady=5)
progress_var = StringVar(value=0)
progress_bar = Progressbar(root, orient="horizontal", length=400, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

Button(root, text="Iniciar Conversão", command=start_conversion).pack(pady=10)
Button(root, text="Cancelar Conversão", command=cancel_conversion).pack(pady=10)
Button(root, text="Sair", command=root.quit).pack(pady=10)

root.mainloop()
