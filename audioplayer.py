import sys
import random
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QSlider, QLabel, QFileDialog, QListWidget, 
                             QStyle, QLineEdit, QTextEdit)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent, QMediaPlaylist
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import (QPalette, QColor, QFont, QPainter, QPen, QLinearGradient)

class MatrixAudioPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Matrix Audio Player")
        self.setGeometry(100, 100, 800, 600)
        
        # Настройки плейлиста
        self.playlist_file = "matrix_playlist.json"
        
        # Стиль Matrix
        self.init_ui()
        self.load_playlist()
        
        # Стартовое сообщение
        self.log_message("SYSTEM INITIALIZED")
        self.log_message("TYPE 'add' TO LOAD MUSIC")

    def init_ui(self):
        # Цветовая схема
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.WindowText, QColor(0, 255, 0))
        palette.setColor(QPalette.Button, QColor(0, 50, 0))
        palette.setColor(QPalette.ButtonText, QColor(0, 255, 0))
        palette.setColor(QPalette.Base, QColor(0, 20, 0))
        palette.setColor(QPalette.Text, QColor(0, 255, 0))
        palette.setColor(QPalette.Highlight, QColor(0, 100, 0))
        self.setPalette(palette)

        # Шрифт
        font = QFont("Courier New", 12)
        font.setBold(True)
        self.setFont(font)

        # Медиаплеер
        self.player = QMediaPlayer()
        self.playlist = QMediaPlaylist()
        self.player.setPlaylist(self.playlist)
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.currentMediaChanged.connect(self.update_track_label)

        # Основной интерфейс
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Фон с анимацией
        self.matrix_bg = MatrixBackground(self)
        self.matrix_bg.lower()

        # Элементы управления
        self.track_label = QLabel("> SYSTEM READY")
        self.track_label.setStyleSheet("color: #00ff00; font-size: 14px;")
        main_layout.addWidget(self.track_label)

        self.time_label = QLabel("> 0:00 / 0:00")
        self.time_label.setStyleSheet("color: #00aa00; font-size: 12px;")
        main_layout.addWidget(self.time_label)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #002200; height: 8px; }
            QSlider::handle:horizontal { background: #00ff00; width: 12px; height: 12px; }
            QSlider::sub-page:horizontal { background: #00aa00; }
        """)
        self.progress_slider.sliderMoved.connect(self.set_position)
        main_layout.addWidget(self.progress_slider)

        # Кнопки
        btn_style = """
        QPushButton {
            background: #002200;
            border: 1px solid #00aa00;
            color: #00ff00;
            padding: 5px;
            min-width: 60px;
        }
        QPushButton:hover { background: #004400; }
        """
        
        buttons = QHBoxLayout()
        self.prev_btn = QPushButton("[ << ]")
        self.prev_btn.setStyleSheet(btn_style)
        self.prev_btn.clicked.connect(self.play_previous)
        buttons.addWidget(self.prev_btn)

        self.play_pause_btn = QPushButton("[ > ]")
        self.play_pause_btn.setStyleSheet(btn_style)
        self.play_pause_btn.clicked.connect(self.play_pause)
        buttons.addWidget(self.play_pause_btn)

        self.stop_btn = QPushButton("[ ■ ]")
        self.stop_btn.setStyleSheet(btn_style)
        self.stop_btn.clicked.connect(self.stop)
        buttons.addWidget(self.stop_btn)

        self.next_btn = QPushButton("[ >> ]")
        self.next_btn.setStyleSheet(btn_style)
        self.next_btn.clicked.connect(self.play_next)
        buttons.addWidget(self.next_btn)

        main_layout.addLayout(buttons)

        # Плейлист
        self.playlist_view = QListWidget()
        self.playlist_view.setStyleSheet("""
            QListWidget {
                background: #001100;
                color: #00ff00;
                border: 1px solid #00aa00;
                font-family: 'Courier New';
            }
            QListWidget::item:selected {
                background: #004400;
                color: #00ff00;
            }
        """)
        self.playlist_view.itemDoubleClicked.connect(self.play_selected_track)
        main_layout.addWidget(self.playlist_view)

        # Командная строка
        self.cmd_input = QLineEdit()
        self.cmd_input.setStyleSheet("background: #001100; color: #00ff00; border: 1px solid #00aa00;")
        self.cmd_input.setPlaceholderText("> Enter command (play, stop, next, prev, add, clear)")
        self.cmd_input.returnPressed.connect(self.execute_command)
        main_layout.addWidget(self.cmd_input)

        # Лог
        self.console_log = QTextEdit()
        self.console_log.setStyleSheet("background: #000000; color: #00ff00; border: 1px solid #00aa00;")
        self.console_log.setReadOnly(True)
        main_layout.addWidget(self.console_log)

        # Таймер анимации
        self.matrix_timer = QTimer()
        self.matrix_timer.timeout.connect(self.matrix_bg.update_matrix)
        self.matrix_timer.start(100)

    # Основные функции плеера
    def load_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", "", 
                                               "Audio Files (*.mp3 *.wav)")
        if files:
            for file in files:
                self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(file)))
                self.playlist_view.addItem(os.path.basename(file))
            
            if self.playlist.mediaCount() > 0 and self.player.media().isNull():
                self.playlist.setCurrentIndex(0)
                self.player.setPlaylist(self.playlist)
            
            self.save_playlist()
            self.log_message(f"Added {len(files)} file(s)")

    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_pause_btn.setText("[ > ]")
            self.log_message("Playback paused")
        else:
            self.player.play()
            self.play_pause_btn.setText("[ || ]")
            self.log_message("Playback started")

    def stop(self):
        self.player.stop()
        self.play_pause_btn.setText("[ > ]")
        self.progress_slider.setValue(0)
        self.time_label.setText("> 0:00 / 0:00")
        self.log_message("Playback stopped")

    def play_previous(self):
        self.playlist.previous()
        if self.player.state() != QMediaPlayer.PlayingState:
            self.player.play()
            self.play_pause_btn.setText("[ || ]")
        self.log_message("Previous track")

    def play_next(self):
        self.playlist.next()
        if self.player.state() != QMediaPlayer.PlayingState:
            self.player.play()
            self.play_pause_btn.setText("[ || ]")
        self.log_message("Next track")

    def set_position(self, position):
        self.player.setPosition(position)

    def update_position(self, position):
        self.progress_slider.setValue(position)
        self.time_label.setText(f"> {self.format_time(position)} / {self.format_time(self.player.duration())}")

    def update_duration(self, duration):
        self.progress_slider.setMaximum(duration)

    def update_track_label(self, media):
        if media.isNull():
            self.track_label.setText("> SYSTEM READY")
        else:
            self.track_label.setText(f"> NOW PLAYING: {media.canonicalUrl().fileName()}")
            self.log_message(f"Now playing: {media.canonicalUrl().fileName()}")

    def play_selected_track(self, item):
        index = self.playlist_view.row(item)
        self.playlist.setCurrentIndex(index)
        self.player.play()
        self.play_pause_btn.setText("[ || ]")
        self.log_message("Playing selected track")

    def clear_playlist(self):
        self.playlist.clear()
        self.playlist_view.clear()
        self.player.stop()
        self.track_label.setText("> SYSTEM READY")
        self.time_label.setText("> 0:00 / 0:00")
        self.play_pause_btn.setText("[ > ]")
        self.save_playlist()
        self.log_message("Playlist cleared")

    def format_time(self, milliseconds):
        if milliseconds < 0:
            return "0:00"
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"

    # Работа с плейлистом
    def save_playlist(self):
        playlist_paths = []
        for i in range(self.playlist.mediaCount()):
            media = self.playlist.media(i)
            if not media.isNull():
                playlist_paths.append(media.canonicalUrl().toLocalFile())
        
        with open(self.playlist_file, "w") as f:
            json.dump(playlist_paths, f)
        
        self.log_message("Playlist saved")

    def load_playlist(self):
        if os.path.exists(self.playlist_file):
            try:
                with open(self.playlist_file, "r") as f:
                    playlist_paths = json.load(f)
                
                missing_files = []
                
                for path in playlist_paths:
                    if os.path.exists(path):
                        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(path)))
                        self.playlist_view.addItem(os.path.basename(path))
                    else:
                        missing_files.append(os.path.basename(path))
                
                if missing_files:
                    self.log_message(f"Missing files: {', '.join(missing_files)}")
                
                if self.playlist.mediaCount() > 0:
                    self.playlist.setCurrentIndex(0)
                    self.log_message(f"Loaded {self.playlist.mediaCount()} tracks")
            except Exception as e:
                self.log_message(f"Playlist load error: {str(e)}")

    # Дополнительные функции
    def execute_command(self):
        cmd = self.cmd_input.text().strip().lower()
        self.cmd_input.clear()
        
        commands = {
            'play': self.play_pause,
            'stop': self.stop,
            'next': self.play_next,
            'prev': self.play_previous,
            'add': self.load_file,
            'clear': self.clear_playlist
        }
        
        if cmd in commands:
            commands[cmd]()
        else:
            self.log_message("Unknown command. Try: play, stop, next, prev, add, clear")

    def log_message(self, message):
        self.console_log.append(f"> {message}")
        self.console_log.verticalScrollBar().setValue(self.console_log.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.save_playlist()
        event.accept()

class MatrixBackground(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.chars = "01"
        self.columns = 100
        self.positions = [random.randint(-1000, 0) for _ in range(self.columns)]
        self.speeds = [random.randint(10, 30) for _ in range(self.columns)]
        self.opacities = [random.random() * 0.5 + 0.1 for _ in range(self.columns)]

    def update_matrix(self):
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setFont(QFont("Courier New", 12))
        
        for i in range(self.columns):
            x = i * (self.width() // self.columns)
            y = self.positions[i]
            
            for j in range(20):
                if y + j * 20 < self.height():
                    char = random.choice(self.chars)
                    opacity = self.opacities[i] * (1 - j/20)
                    color = QColor(0, 255, 0)
                    color.setAlphaF(opacity)
                    painter.setPen(color)
                    painter.drawText(x, y + j * 20, char)
            
            self.positions[i] += self.speeds[i]
            if self.positions[i] > self.height() + 100:
                self.positions[i] = random.randint(-1000, 0)
                self.speeds[i] = random.randint(10, 30)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = MatrixAudioPlayer()
    player.show()
    sys.exit(app.exec_())