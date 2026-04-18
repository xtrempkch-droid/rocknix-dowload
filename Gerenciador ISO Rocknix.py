import sys
import os
import requests
import gzip
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QProgressBar, QMessageBox,
    QComboBox, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QDesktopServices
from PyQt6.QtCore import QUrl
import qdarktheme

class ProcessThread(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            # 1. DOWNLOAD
            self.status.emit("Baixando imagem oficial...")
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(self.dest_path, 'wb') as f:
                downloaded = 0
                for data in response.iter_content(chunk_size=1024*1024):
                    downloaded += len(data)
                    f.write(data)
                    if total_size > 0:
                        self.progress.emit(int(downloaded * 100 / total_size))

            # 2. EXTRAÇÃO
            self.status.emit("Extraindo arquivo .img (aguarde)...")
            img_path = self.dest_path.replace('.gz', '')
            with gzip.open(self.dest_path, 'rb') as f_in:
                with open(img_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            if os.path.exists(self.dest_path):
                os.remove(self.dest_path)
            
            self.finished.emit(img_path)
        except Exception as e:
            self.error.emit(str(e))

class RocknixManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.releases_data = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Rocknix Manager - Assistente de Instalação")
        self.setFixedSize(600, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Cabeçalho Estilizado
        title = QLabel("ROCKNIX")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #3daee9;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Painel de Seleção
        form_frame = QFrame()
        form_layout = QVBoxLayout(form_frame)
        
        self.hw_combo = QComboBox()
        form_layout.addWidget(QLabel("1. Selecione seu Dispositivo:"))
        form_layout.addWidget(self.hw_combo)

        self.version_list = QListWidget()
        form_layout.addWidget(QLabel("2. Selecione a Versão:"))
        form_layout.addWidget(self.version_list)
        
        layout.addWidget(form_frame)

        # Progresso
        self.status_label = QLabel("Pronto para começar")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Botões de Ação
        btn_layout = QHBoxLayout()
        
        self.help_btn = QPushButton("?")
        self.help_btn.setFixedSize(40, 40)
        self.help_btn.setToolTip("Ajuda e Instruções")
        self.help_btn.clicked.connect(self.show_help)
        
        self.action_btn = QPushButton("BAIXAR E PREPARAR SD")
        self.action_btn.setFixedHeight(40)
        self.action_btn.setStyleSheet("font-weight: bold; background-color: #3daee9;")
        self.action_btn.clicked.connect(self.start_workflow)
        
        btn_layout.addWidget(self.help_btn)
        btn_layout.addWidget(self.action_btn)
        layout.addLayout(btn_layout)

        # Inicialização
        self.fetch_data()

    def fetch_data(self):
        # ... (Mesma lógica dinâmica de parse do GitHub que criamos antes) ...
        pass # Implementar lógica de fetch aqui

    def start_workflow(self):
        # ... (Lógica de download e extração) ...
        pass

    def open_flasher(self, img_path):
        # Lista de possíveis caminhos para gravadores conhecidos
        potential_apps = [
            r"C:\Program Files\Raspberry Pi Imager\rpi-imager.exe",
            r"C:\Program Files\balena-etcher\balenaEtcher.exe",
            os.path.expandvars(r"%LocalAppData%\Programs\balena-etcher\balenaEtcher.exe")
        ]
        
        launched = False
        for app in potential_apps:
            if os.path.exists(app):
                subprocess.Popen([app, img_path])
                launched = True
                break
        
        if not launched:
            QMessageBox.warning(self, "Gravador não encontrado", 
                "Download concluído! Não encontramos o Raspberry Pi Imager ou BalenaEtcher.\n"
                "A pasta com a imagem será aberta agora.")
            os.startfile(os.path.dirname(img_path))

    def show_help(self):
        msg = (
            "Como usar o Rocknix Manager:\n\n"
            "1. Escolha seu hardware corretamente (ex: rk3566 para RG353P/V).\n"
            "2. Escolha a versão mais recente.\n"
            "3. O app vai baixar, descompactar e abrir seu gravador de SD.\n\n"
            "Dica: Para o primeiro boot, use um cartão de boa qualidade!"
        )
        QMessageBox.information(self, "Guia de Uso", msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("auto")
    window = RocknixManager()
    window.show()
    sys.exit(app.exec())
