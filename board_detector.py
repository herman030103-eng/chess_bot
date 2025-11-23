"""
Chess Board Detection Module
Handles screenshot capture, board detection, perspective correction,
and segmentation into 64 squares.
"""

import cv2
import numpy as np
import mss
from typing import Tuple, Optional, List


def capture_screenshot() -> np.ndarray:
    """
    Захватывает скриншот всего экрана.
    
    Returns:
        np.ndarray: Изображение в формате BGR
    """
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Основной монитор
        screenshot = sct.grab(monitor)
        # Конвертируем в numpy array и BGR формат
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img


def detect_chessboard(image: np.ndarray) -> Optional[np.ndarray]:
    """
    Обнаруживает шахматную доску на изображении и возвращает координаты углов.
    
    Args:
        image: Входное изображение
        
    Returns:
        np.ndarray: Массив из 4 точек (углы доски) или None
    """
    # Конвертируем в градации серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Применяем адаптивную бинаризацию для улучшения контраста
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Поиск контуров
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Сортируем контуры по площади (от большего к меньшему)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    # Ищем квадратную область (шахматную доску)
    for contour in contours[:10]:  # Проверяем топ-10 контуров
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
        
        # Если контур имеет 4 вершины (прямоугольник)
        if len(approx) == 4:
            area = cv2.contourArea(approx)
            # Проверяем, что это достаточно большая область
            if area > 10000:  # Минимальная площадь доски
                # Проверяем, насколько форма близка к квадрату
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = float(w) / h
                if 0.7 < aspect_ratio < 1.3:  # Примерно квадрат
                    return approx.reshape(4, 2)
    
    # Если автоматическое обнаружение не сработало, 
    # используем всю центральную область изображения
    h, w = image.shape[:2]
    margin = min(h, w) // 8
    return np.array([
        [margin, margin],
        [w - margin, margin],
        [w - margin, h - margin],
        [margin, h - margin]
    ], dtype=np.float32)


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Упорядочивает точки в порядке: верхний левый, верхний правый,
    нижний правый, нижний левый.
    
    Args:
        pts: Массив из 4 точек
        
    Returns:
        np.ndarray: Упорядоченный массив точек
    """
    rect = np.zeros((4, 2), dtype=np.float32)
    
    # Сумма координат: верхний левый имеет наименьшую сумму,
    # нижний правый - наибольшую
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    
    # Разность координат: верхний правый имеет наименьшую разность,
    # нижний левый - наибольшую
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    
    return rect


def correct_perspective(image: np.ndarray, corners: np.ndarray, 
                       size: int = 800) -> np.ndarray:
    """
    Применяет перспективную трансформацию для выравнивания доски.
    
    Args:
        image: Входное изображение
        corners: Координаты 4 углов доски
        size: Размер выходного изображения (квадрат)
        
    Returns:
        np.ndarray: Выровненное изображение доски
    """
    # Упорядочиваем точки
    rect = order_points(corners)
    
    # Определяем целевые точки для трансформации
    dst = np.array([
        [0, 0],
        [size - 1, 0],
        [size - 1, size - 1],
        [0, size - 1]
    ], dtype=np.float32)
    
    # Вычисляем матрицу перспективной трансформации
    M = cv2.getPerspectiveTransform(rect, dst)
    
    # Применяем трансформацию
    warped = cv2.warpPerspective(image, M, (size, size))
    
    return warped


def segment_board(board_image: np.ndarray) -> List[List[np.ndarray]]:
    """
    Разделяет изображение доски на 64 клетки (8x8).
    
    Args:
        board_image: Выровненное изображение доски
        
    Returns:
        List[List[np.ndarray]]: Двумерный массив изображений клеток [ряд][колонка]
    """
    h, w = board_image.shape[:2]
    cell_h = h // 8
    cell_w = w // 8
    
    cells = []
    for row in range(8):
        row_cells = []
        for col in range(8):
            y1 = row * cell_h
            y2 = (row + 1) * cell_h
            x1 = col * cell_w
            x2 = (col + 1) * cell_w
            
            cell = board_image[y1:y2, x1:x2]
            row_cells.append(cell)
        cells.append(row_cells)
    
    return cells


def process_screenshot_to_cells(screenshot: np.ndarray) -> Optional[List[List[np.ndarray]]]:
    """
    Полный пайплайн обработки скриншота: от изображения до 64 клеток.
    
    Args:
        screenshot: Исходный скриншот
        
    Returns:
        List[List[np.ndarray]]: Массив клеток 8x8 или None если доска не найдена
    """
    # Обнаруживаем доску
    corners = detect_chessboard(screenshot)
    if corners is None:
        print("Не удалось обнаружить шахматную доску на изображении")
        return None
    
    # Корректируем перспективу
    board = correct_perspective(screenshot, corners)
    
    # Сегментируем на клетки
    cells = segment_board(board)
    
    return cells
