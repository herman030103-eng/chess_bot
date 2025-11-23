"""
Unit tests for chess_bot modules
Tests functionality without requiring Stockfish or display.
"""

import numpy as np
import sys


def test_piece_recognition():
    """Test piece recognition module."""
    print("Testing piece_recognition module...")
    import piece_recognition
    
    # Test board_to_fen with start position
    board = [
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
        ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
        ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    ]
    
    fen = piece_recognition.board_to_fen(board, 'w')
    expected_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    
    assert fen == expected_fen, f"Expected {expected_fen}, got {fen}"
    print("  ✓ board_to_fen works correctly")
    
    # Test with e4 position
    board_e4 = [
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
        ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', 'P', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['P', 'P', 'P', 'P', '.', 'P', 'P', 'P'],
        ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
    ]
    
    fen_e4 = piece_recognition.board_to_fen(board_e4, 'b')
    expected_e4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    
    assert fen_e4 == expected_e4, f"Expected {expected_e4}, got {fen_e4}"
    print("  ✓ board_to_fen works with e4 position")
    
    print("✓ piece_recognition tests passed\n")


def test_board_detector():
    """Test board detector module."""
    print("Testing board_detector module...")
    import board_detector
    
    # Test order_points function
    pts = np.array([[100, 200], [300, 100], [400, 400], [50, 350]], dtype=np.float32)
    ordered = board_detector.order_points(pts)
    
    # Check that we have 4 points
    assert ordered.shape == (4, 2), f"Expected shape (4, 2), got {ordered.shape}"
    print("  ✓ order_points returns correct shape")
    
    # Top-left should have smallest sum
    # Bottom-right should have largest sum
    sums = ordered.sum(axis=1)
    assert sums[0] < sums[2], "Top-left should have smaller sum than bottom-right"
    print("  ✓ order_points orders correctly")
    
    # Test segment_board
    test_board = np.zeros((800, 800, 3), dtype=np.uint8)
    cells = board_detector.segment_board(test_board)
    
    assert len(cells) == 8, f"Expected 8 rows, got {len(cells)}"
    assert len(cells[0]) == 8, f"Expected 8 columns, got {len(cells[0])}"
    assert cells[0][0].shape == (100, 100, 3), f"Expected cell shape (100, 100, 3), got {cells[0][0].shape}"
    print("  ✓ segment_board creates 8x8 grid correctly")
    
    print("✓ board_detector tests passed\n")


def test_engine_module():
    """Test engine module (without Stockfish)."""
    print("Testing engine module...")
    import engine
    
    # Test ChessEngine class exists and can be instantiated
    chess_engine = engine.ChessEngine(stockfish_path="/usr/games/stockfish", depth=10)
    assert chess_engine.depth == 10, "Depth not set correctly"
    assert chess_engine.stockfish_path == "/usr/games/stockfish", "Path not set correctly"
    print("  ✓ ChessEngine can be instantiated")
    
    print("✓ engine module tests passed (Stockfish integration not tested)\n")


def test_chess_validation():
    """Test that python-chess works correctly."""
    print("Testing python-chess integration...")
    import chess
    
    # Test creating a board from FEN
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    board = chess.Board(fen)
    
    assert board.is_valid(), "Board should be valid"
    print("  ✓ Can create valid board from FEN")
    
    # Test making a move
    move = chess.Move.from_uci("e2e4")
    board.push(move)
    
    new_fen = board.fen()
    # Check just the position part (ignore en passant details)
    assert "4P3" in new_fen, f"Move e2e4 not reflected in FEN: {new_fen}"
    assert " b " in new_fen, "Turn should be black's"
    print("  ✓ Can make moves and get FEN")
    
    print("✓ python-chess integration tests passed\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Running Chess Bot Tests")
    print("=" * 60)
    print()
    
    try:
        test_piece_recognition()
        test_board_detector()
        test_engine_module()
        test_chess_validation()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
