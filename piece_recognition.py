"""
Piece Recognition Module
Классифицирует шахматные фигуры на клетках.
Использует простой подход на основе анализа цвета и формы.
"""

import cv2
import numpy as np
from typing import Optional


# Словарь для преобразования символов фигур в FEN нотацию
PIECE_SYMBOLS = {
    'white_pawn': 'P',
    'white_knight': 'N',
    'white_bishop': 'B',
    'white_rook': 'R',
    'white_queen': 'Q',
    'white_king': 'K',
    'black_pawn': 'p',
    'black_knight': 'n',
    'black_bishop': 'b',
    'black_rook': 'r',
    'black_queen': 'q',
    'black_king': 'k',
    'empty': '.'
}


def analyze_cell(cell_image: np.ndarray) -> dict:
    """
    Анализирует клетку для определения наличия и типа фигуры.
    
    Args:
        cell_image: Изображение клетки
        
    Returns:
        dict: Словарь с информацией о клетке (has_piece, is_dark_square, etc.)
    """
    # Конвертируем в HSV для лучшего анализа цвета
    hsv = cv2.cvtColor(cell_image, cv2.COLOR_BGR2HSV)
    
    # Определяем средние значения
    mean_v = np.mean(hsv[:, :, 2])  # Value channel
    mean_s = np.mean(hsv[:, :, 1])  # Saturation channel
    
    # Создаем маску для обнаружения фигуры
    # Фигуры обычно имеют высокий контраст с доской
    gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    
    # Анализ цветовых характеристик
    mean_color = np.mean(cell_image, axis=(0, 1))
    
    return {
        'mean_value': mean_v,
        'mean_saturation': mean_s,
        'edge_density': edge_density,
        'mean_color': mean_color,
        'has_piece': edge_density > 0.05  # Порог для наличия фигуры
    }


def classify_piece_simple(cell_image: np.ndarray, is_dark_square: bool) -> str:
    """
    Простая классификация фигуры на основе цветовых характеристик.
    Это базовая реализация. Для лучших результатов можно использовать CNN.
    
    Args:
        cell_image: Изображение клетки
        is_dark_square: True если клетка темная
        
    Returns:
        str: Символ фигуры в FEN нотации или '.' для пустой клетки
    """
    analysis = analyze_cell(cell_image)
    
    # Если нет фигуры, возвращаем пустую клетку
    if not analysis['has_piece']:
        return '.'
    
    # Анализируем цвет фигуры
    gray = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)
    
    # Создаем маску для фигуры (выделяем объект)
    if is_dark_square:
        # На темной клетке ищем светлые и темные фигуры
        _, thresh_light = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        _, thresh_dark = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)
    else:
        # На светлой клетке
        _, thresh_light = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        _, thresh_dark = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY_INV)
    
    light_pixels = np.sum(thresh_light > 0)
    dark_pixels = np.sum(thresh_dark > 0)
    
    # Определяем цвет фигуры
    is_white_piece = light_pixels > dark_pixels
    
    # Базовая эвристика для определения типа фигуры
    # В реальном приложении здесь должна быть CNN или template matching
    edge_density = analysis['edge_density']
    
    # Простая эвристика на основе плотности краев
    if edge_density > 0.15:
        # Сложная фигура (ферзь, конь)
        piece_type = 'queen' if edge_density > 0.20 else 'knight'
    elif edge_density > 0.10:
        # Средняя сложность (слон, ладья, король)
        # Анализируем форму
        contours, _ = cv2.findContours(
            cv2.Canny(gray, 50, 150),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            aspect_ratio = float(w) / h if h > 0 else 1
            
            if aspect_ratio > 1.2:
                piece_type = 'rook'
            elif y < cell_image.shape[0] * 0.3:
                piece_type = 'king'
            else:
                piece_type = 'bishop'
        else:
            piece_type = 'bishop'
    else:
        # Простая фигура (пешка)
        piece_type = 'pawn'
    
    # Формируем ключ и возвращаем символ
    color = 'white' if is_white_piece else 'black'
    piece_key = f"{color}_{piece_type}"
    
    return PIECE_SYMBOLS.get(piece_key, '.')


def recognize_pieces_on_board(cells: list) -> list:
    """
    Распознает все фигуры на доске.
    
    Args:
        cells: Двумерный массив клеток [8][8]
        
    Returns:
        list: Двумерный массив символов фигур [8][8]
    """
    board = []
    
    for row in range(8):
        board_row = []
        for col in range(8):
            # Определяем, темная ли клетка (шахматный паттерн)
            is_dark_square = (row + col) % 2 == 1
            
            # Классифицируем фигуру
            piece = classify_piece_simple(cells[row][col], is_dark_square)
            board_row.append(piece)
        
        board.append(board_row)
    
    return board


def board_to_fen(board: list, active_color: str = 'w') -> str:
    """
    Преобразует двумерный массив фигур в FEN строку.
    
    Args:
        board: Двумерный массив символов фигур [8][8]
        active_color: Цвет, который ходит ('w' или 'b')
        
    Returns:
        str: FEN строка
    """
    fen_rows = []
    
    for row in board:
        fen_row = ""
        empty_count = 0
        
        for cell in row:
            if cell == '.':
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += cell
        
        if empty_count > 0:
            fen_row += str(empty_count)
        
        fen_rows.append(fen_row)
    
    # Собираем FEN строку
    fen_position = '/'.join(fen_rows)
    
    # Добавляем дополнительную информацию FEN
    # Формат: позиция активный_цвет возможность_рокировки взятие_на_проходе полуходы полные_ходы
    fen = f"{fen_position} {active_color} KQkq - 0 1"
    
    return fen


def cells_to_fen(cells: list, active_color: str = 'w') -> str:
    """
    Основная функция: принимает клетки и возвращает FEN строку.
    
    Args:
        cells: Двумерный массив изображений клеток [8][8]
        active_color: Цвет, который ходит ('w' или 'b')
        
    Returns:
        str: FEN строка
    """
    # Распознаем фигуры
    board = recognize_pieces_on_board(cells)
    
    # Преобразуем в FEN
    fen = board_to_fen(board, active_color)
    
    return fen
