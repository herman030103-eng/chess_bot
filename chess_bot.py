"""
Main Chess Bot Application
Фоновое приложение с глобальным хоткеем для анализа шахматных позиций.
"""

import json
import time
import sys
from pynput import keyboard
from typing import Optional
import threading

from board_detector import capture_screenshot, process_screenshot_to_cells
from piece_recognition import cells_to_fen
from engine import ChessEngine


class ChessBot:
    """Основной класс приложения chess bot."""
    
    def __init__(self, config_path: str = "config.json"):
        """
        Инициализирует chess bot.
        
        Args:
            config_path: Путь к файлу конфигурации
        """
        # Загружаем конфигурацию
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        # Инициализируем движок
        self.engine = ChessEngine(
            stockfish_path=self.config.get('stockfish_path', '/usr/games/stockfish'),
            depth=self.config.get('stockfish_depth', 15)
        )
        
        # Параметры
        self.player_color = self.config.get('player_color', 'white')
        self.screenshot_delay = self.config.get('screenshot_delay', 0.5)
        
        # Флаг для остановки
        self.running = True
        
        # Флаг обработки (чтобы не запускать несколько раз одновременно)
        self.processing = False
        
        print("=" * 60)
        print("Chess Bot запущен!")
        print("=" * 60)
        print(f"Цвет игрока: {self.player_color}")
        print(f"Глубина анализа: {self.config.get('stockfish_depth', 15)}")
        print(f"Горячая клавиша: {self.config.get('hotkey', 'ctrl+shift+x')}")
        print("=" * 60)
        print("Нажмите CTRL+SHIFT+X для анализа позиции")
        print("Нажмите CTRL+C для выхода")
        print("=" * 60)
    
    def process_screenshot(self):
        """
        Обрабатывает скриншот: захват -> распознавание -> анализ -> вывод.
        """
        if self.processing:
            print("Обработка уже выполняется, подождите...")
            return
        
        self.processing = True
        
        try:
            print("\n" + "=" * 60)
            print("НАЧАЛО ОБРАБОТКИ")
            print("=" * 60)
            
            # Шаг 1: Захват скриншота
            print("1. Захват скриншота...")
            time.sleep(self.screenshot_delay)  # Небольшая задержка
            screenshot = capture_screenshot()
            print("   ✓ Скриншот захвачен")
            
            # Шаг 2: Обнаружение и сегментация доски
            print("2. Обнаружение шахматной доски...")
            cells = process_screenshot_to_cells(screenshot)
            
            if cells is None:
                print("   ✗ ОШИБКА: Не удалось обнаружить шахматную доску")
                print("   Убедитесь, что доска видна на экране полностью")
                return
            
            print("   ✓ Доска обнаружена и разделена на 64 клетки")
            
            # Шаг 3: Распознавание фигур и генерация FEN
            print("3. Распознавание фигур...")
            active_color = 'w' if self.player_color.lower() == 'white' else 'b'
            fen = cells_to_fen(cells, active_color)
            print(f"   ✓ FEN: {fen}")
            
            # Шаг 4: Анализ позиции
            print("4. Анализ позиции с помощью Stockfish...")
            best_move_uci, evaluation = self.engine.get_best_move(fen)
            
            if best_move_uci:
                # Преобразуем в читаемый формат
                best_move_san = self.engine.move_to_readable(best_move_uci, fen)
                
                print("=" * 60)
                print("РЕЗУЛЬТАТ АНАЛИЗА")
                print("=" * 60)
                print(f"Лучший ход (UCI): {best_move_uci}")
                print(f"Лучший ход (SAN): {best_move_san}")
                print(f"Оценка позиции: {evaluation}")
                print("=" * 60)
            else:
                print("   ✗ ОШИБКА: Не удалось найти лучший ход")
                print("   Возможно, позиция некорректна")
            
        except Exception as e:
            print(f"\n✗ ОШИБКА: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.processing = False
            print()
    
    def on_hotkey(self):
        """Обработчик нажатия горячей клавиши."""
        # Запускаем обработку в отдельном потоке, чтобы не блокировать listener
        thread = threading.Thread(target=self.process_screenshot)
        thread.daemon = True
        thread.start()
    
    def run(self):
        """Запускает основной цикл приложения."""
        try:
            # Запускаем движок
            self.engine.start()
            
            # Настраиваем горячую клавишу
            hotkey_combo = keyboard.HotKey(
                keyboard.HotKey.parse('<ctrl>+<shift>+x'),
                self.on_hotkey
            )
            
            # Обработчик событий клавиатуры
            def for_canonical(f):
                return lambda k: f(listener.canonical(k))
            
            # Создаем listener
            with keyboard.Listener(
                on_press=for_canonical(hotkey_combo.press),
                on_release=for_canonical(hotkey_combo.release)
            ) as listener:
                # Сохраняем listener в переменную для доступа в for_canonical
                globals()['listener'] = listener
                
                # Основной цикл
                while self.running:
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            print("\n\nОстановка приложения...")
        finally:
            self.engine.stop()
            print("Chess Bot остановлен.")


def main():
    """Точка входа в приложение."""
    import os
    
    # Определяем путь к конфигу
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')
    
    # Проверяем наличие конфига
    if not os.path.exists(config_path):
        print(f"ОШИБКА: Файл конфигурации не найден: {config_path}")
        print("Создайте config.json со следующим содержимым:")
        print(json.dumps({
            "player_color": "white",
            "stockfish_path": "/usr/games/stockfish",
            "stockfish_depth": 15,
            "hotkey": "ctrl+shift+x",
            "screenshot_delay": 0.5
        }, indent=2))
        sys.exit(1)
    
    # Создаем и запускаем бота
    bot = ChessBot(config_path)
    bot.run()


if __name__ == "__main__":
    main()
