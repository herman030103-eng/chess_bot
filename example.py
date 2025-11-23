"""
Пример использования модулей chess_bot
Демонстрирует основные функции без необходимости запуска фонового процесса.
"""

from board_detector import capture_screenshot, process_screenshot_to_cells
from piece_recognition import cells_to_fen
from engine import analyze_fen


def screenshot_to_fen(player_color='white'):
    """
    Принимает скриншот и возвращает FEN-строку.
    
    Args:
        player_color: Цвет игрока ('white' или 'black')
        
    Returns:
        str: FEN-строка или None при ошибке
    """
    print("Захват скриншота...")
    screenshot = capture_screenshot()
    
    print("Обработка изображения...")
    cells = process_screenshot_to_cells(screenshot)
    
    if cells is None:
        print("Ошибка: не удалось обнаружить доску")
        return None
    
    print("Генерация FEN...")
    active_color = 'w' if player_color.lower() == 'white' else 'b'
    fen = cells_to_fen(cells, active_color)
    
    return fen


def main():
    """Главная функция примера."""
    print("=" * 60)
    print("Пример использования Chess Bot")
    print("=" * 60)
    print()
    
    # Пример 1: Анализ стартовой позиции
    print("Пример 1: Анализ стартовой позиции")
    print("-" * 60)
    
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print(f"FEN: {start_fen}")
    
    result = analyze_fen(
        fen=start_fen,
        stockfish_path="/usr/games/stockfish",
        depth=10
    )
    
    if result['success']:
        print(f"Лучший ход: {result['best_move_san']} ({result['best_move_uci']})")
        print(f"Оценка: {result['evaluation']}")
    else:
        print(f"Ошибка: {result.get('error', 'Неизвестная ошибка')}")
    
    print()
    
    # Пример 2: Получение FEN со скриншота (закомментировано)
    print("Пример 2: Получение FEN со скриншота")
    print("-" * 60)
    print("Для использования этой функции:")
    print("1. Откройте шахматную доску на экране")
    print("2. Раскомментируйте код ниже")
    print("3. Запустите скрипт заново")
    print()
    
    # Раскомментируйте для захвата и анализа скриншота:
    # fen = screenshot_to_fen('white')
    # if fen:
    #     print(f"Полученный FEN: {fen}")
    #     result = analyze_fen(fen, "/usr/games/stockfish", depth=15)
    #     if result['success']:
    #         print(f"Лучший ход: {result['best_move_san']}")
    #         print(f"Оценка: {result['evaluation']}")
    
    print()
    print("=" * 60)
    print("Для полноценной работы запустите: python3 chess_bot.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
