"""
Chess Engine Module
Взаимодействие с шахматным движком Stockfish для анализа позиций и поиска лучших ходов.
"""

import chess
import chess.engine
from typing import Tuple, Optional
import os


class ChessEngine:
    """Класс для работы с шахматным движком."""
    
    def __init__(self, stockfish_path: str = "/usr/games/stockfish", depth: int = 15):
        """
        Инициализирует шахматный движок.
        
        Args:
            stockfish_path: Путь к исполняемому файлу Stockfish
            depth: Глубина анализа
        """
        self.stockfish_path = stockfish_path
        self.depth = depth
        self.engine = None
        
    def _ensure_engine_exists(self) -> bool:
        """
        Проверяет наличие движка Stockfish.
        
        Returns:
            bool: True если движок найден
        """
        # Проверяем стандартные пути
        possible_paths = [
            self.stockfish_path,
            "/usr/games/stockfish",
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "stockfish"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or os.system(f"which {path} > /dev/null 2>&1") == 0:
                self.stockfish_path = path
                return True
        
        return False
    
    def start(self):
        """Запускает движок."""
        if not self._ensure_engine_exists():
            raise FileNotFoundError(
                f"Stockfish не найден. Установите его командой: sudo apt-get install stockfish"
            )
        
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
            print(f"Stockfish запущен: {self.stockfish_path}")
        except Exception as e:
            raise RuntimeError(f"Ошибка запуска Stockfish: {e}")
    
    def stop(self):
        """Останавливает движок."""
        if self.engine:
            self.engine.quit()
            self.engine = None
    
    def analyze_position(self, fen: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Анализирует позицию и возвращает лучший ход.
        
        Args:
            fen: FEN строка позиции
            
        Returns:
            Tuple[str, float]: (Лучший ход в нотации UCI, оценка позиции)
                              Оценка в пешках (положительная для белых)
        """
        if not self.engine:
            self.start()
        
        try:
            # Создаем доску из FEN
            board = chess.Board(fen)
            
            # Анализируем позицию
            info = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
            
            # Получаем лучший ход
            best_move = info.get("pv")[0] if "pv" in info else None
            
            # Получаем оценку
            score = info.get("score")
            if score:
                # Конвертируем оценку в пешки
                score_cp = score.relative.score(mate_score=10000)
                if score_cp is not None:
                    evaluation = score_cp / 100.0  # Конвертируем сантипешки в пешки
                else:
                    # Если мат
                    mate_in = score.relative.mate()
                    evaluation = f"Мат в {mate_in}" if mate_in else "0.0"
            else:
                evaluation = None
            
            return (str(best_move) if best_move else None, evaluation)
            
        except Exception as e:
            print(f"Ошибка анализа позиции: {e}")
            return None, None
    
    def get_best_move(self, fen: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Получает лучший ход для позиции.
        
        Args:
            fen: FEN строка позиции
            
        Returns:
            Tuple[str, float]: (Лучший ход, оценка позиции)
        """
        return self.analyze_position(fen)
    
    def move_to_readable(self, move_uci: str, fen: str) -> str:
        """
        Преобразует ход из UCI нотации в читаемую форму.
        
        Args:
            move_uci: Ход в UCI формате (например, 'e2e4')
            fen: FEN позиции
            
        Returns:
            str: Ход в стандартной нотации (например, 'e4' или 'Nf3')
        """
        try:
            board = chess.Board(fen)
            move = chess.Move.from_uci(move_uci)
            san_move = board.san(move)
            return san_move
        except Exception as e:
            print(f"Ошибка преобразования хода: {e}")
            return move_uci


def analyze_fen(fen: str, stockfish_path: str, depth: int = 15) -> dict:
    """
    Удобная функция для анализа FEN позиции.
    
    Args:
        fen: FEN строка
        stockfish_path: Путь к Stockfish
        depth: Глубина анализа
        
    Returns:
        dict: Словарь с результатами анализа
    """
    engine = ChessEngine(stockfish_path, depth)
    
    try:
        engine.start()
        best_move, evaluation = engine.get_best_move(fen)
        
        if best_move:
            readable_move = engine.move_to_readable(best_move, fen)
            return {
                'success': True,
                'best_move_uci': best_move,
                'best_move_san': readable_move,
                'evaluation': evaluation,
                'fen': fen
            }
        else:
            return {
                'success': False,
                'error': 'Не удалось найти лучший ход'
            }
    finally:
        engine.stop()
