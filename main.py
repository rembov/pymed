import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QSlider
from PyQt5.QtCore import QTimer, Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import requests

# Установка русского шрифта для matplotlib
plt.rcParams['font.family'] = 'Arial'

class SpectrogramWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Анализатор частот')
        self.setGeometry(100, 100, 1000, 600)

        # Параметры FFT
        self.RATE = 2000  # Частота дискретизации ESP (1kHz)
        self.MAX_FREQUENCY = 700  # Максимальная частота
        self.TIME_WINDOW = 1  # Временное окно
        self.SAMPLES = self.TIME_WINDOW * self.RATE  # Количество точек

        # Основные параметры
        self.esp_ip = "192.168.43.49"
        self.data_buffer = np.zeros(self.SAMPLES)  # Заполняем массив нулями
        self.time_buffer = np.linspace(1, self.TIME_WINDOW, self.SAMPLES)  # Время

        # Создаем главный виджет и layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Создаем график
        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Кнопки управления
        self.start_button = QPushButton('Старт')
        self.start_button.clicked.connect(self.start_recording)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Стоп')
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        # Ползунок для перемещения по времени
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self.SAMPLES)
        self.slider.valueChanged.connect(self.update_plot)
        layout.addWidget(self.slider)

        # Таймер для обновления данных
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.setInterval(50)  # 50ms интервал обновления

        # Инициализация графика
        self.line_freq, = self.ax.plot(self.time_buffer, self.data_buffer)

        # Настройка графика
        self.ax.set_xlim(0, self.TIME_WINDOW)  # Ось X минут
        self.ax.set_ylim(0, self.MAX_FREQUENCY)  # Ось Y до 700 Гц
        self.ax.set_title('Частотный анализ', fontsize=12)
        self.ax.set_xlabel('Время ', fontsize=10)
        self.ax.set_ylabel('Частота (Гц)', fontsize=10)
        self.ax.grid(True)

        self.figure.tight_layout()

    def start_recording(self):
        print("Запуск записи данных...")
        self.timer.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_recording(self):
        print("Остановка записи данных.")
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_plot(self):
        try:
            # Получаем данные с ESP
            response = requests.get(f"http://{self.esp_ip}/data")
            value = int(response.text)
            print(f"Получено значение: {value}")

            # Конвертация значения в частоту
            frequency = (value / 1024) * self.MAX_FREQUENCY  # Масштабируем до 700 Гц

            # Сдвигаем данные влево
            self.data_buffer[:-1] = self.data_buffer[1:]
            self.data_buffer[-1] = frequency

            # Обновляем временную шкалу (сдвигаем влево)
            self.time_buffer[:-1] = self.time_buffer[1:]
            self.time_buffer[-1] = self.time_buffer[-2] + (1 / self.RATE)

            # Обновляем график
            self.line_freq.set_data(self.time_buffer, self.data_buffer)

            # Обновляем пределы оси X в зависимости от реального времени
            self.ax.set_xlim(self.time_buffer[0], self.time_buffer[-1])

            # Обновляем график
            self.canvas.draw()

        except Exception as e:
            print(f"Ошибка получения данных: {e}")
            self.stop_recording()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SpectrogramWindow()
    window.show()
    sys.exit(app.exec_())
