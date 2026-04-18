import sys
import os
import requests
import gzip
import shutil
import subprocess  # Para abrir programas externos
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QProgressBar, QMessageBox,
    QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
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
            self.status.emit("Baixando imagem...")
            response = requests.get(self.url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            with open(self.dest_path, 'wb') as f:
                downloaded = 0
                for data in response.iter_content(chunk_size=1024*1024):
                    downloaded += len(data)
                    f.write(data)
                    if total_size > 0:
                        self.progress.emit(int(downloaded * 100 / total_size))

            # 2. EXTRAÇÃO (.gz para .img)
            self.status.emit("Extraindo imagem para gravação...")
            img_path = self.dest_path.replace('.gz', '')
            with gzip.open(self.dest_path, 'rb') as f_in:
                with open(img_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(self.dest_path) # Remove o arquivo comprimido
            self.finished.emit(img_path)

        except Exception as e:
            self.error.emit(str(e))

class RocknixManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.releases_data = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Rocknix Manager Pro - {VERSION}")
        self.setFixedSize(650, 550)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ... (Mantemos as partes de busca de hardware e versão anteriores) ...
        # (Apenas para o exemplo, vamos focar no botão de ação final)

        self.action_btn = QPushButton("BAIXAR E PREPARAR GRAVAÇÃO")
        self.action_btn.setFixedHeight(50)
        self.action_btn.setStyleSheet("background-color: #2a5a8a; font-weight: bold;")
        self.action_btn.clicked.connect(self.start_workflow)
        layout.addWidget(self.action_btn)

        self.status_label = QLabel("Aguardando seleção...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def start_workflow(self):
        # Lógica de seleção de asset (igual aos passos anteriores)
        # ...
        self.worker = ProcessThread(asset_url, full_dest_path)
        self.worker.finished.connect(self.open_flasher)
        self.worker.start()

    def open_flasher(self, img_path):
        self.status_label.setText("Imagem pronta!")
        
        # Caminhos comuns para gravadores de SD (Windows)
        flashers = [
            r"C:\Program Files (x86)\Raspberry Pi Imager\rpi-imager.exe",
            r"C:\Users\{}\AppData\Local\Programs\balena-etcher\balenaEtcher.exe".format(os.getlogin()),
            r"C:\Program Files\balena-etcher\balenaEtcher.exe"
        ]

        found = False
        for exe in flashers:
            if os.path.exists(exe):
                self.status_label.setText(f"Abrindo gravador...")
                # Abre o programa passando o caminho da imagem como argumento
                subprocess.Popen([exe, img_path])
                found = True
                break
        
        if not found:
            # Se não achar nenhum, abre a pasta onde o arquivo está e orienta o usuário
            QMessageBox.information(self, "Download Concluído", 
                f"A imagem foi extraída em:\n{img_path}\n\nNão detectamos o Raspberry Pi Imager ou BalenaEtcher. "
                "Vou abrir a pasta para você gravar manualmente.")
            os.startfile(os.path.dirname(img_path))
        else:
            QMessageBox.information(self, "Sucesso", "O gravador foi aberto com a imagem carregada!")
