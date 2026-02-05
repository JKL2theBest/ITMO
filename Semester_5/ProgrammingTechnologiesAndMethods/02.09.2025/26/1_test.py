import pytest
from main import find_best_pair, main


def create_file_content(M, K, seats):
    lines = [f"{len(seats)} {M} {K}\n"]
    for r, s in seats:
        lines.append(f"{r} {s}\n")
    return lines


def test_example_case():
    M, K = 7, 8
    seats = [(1, 1), (6, 6), (5, 5), (6, 7), (4, 4), (2, 2), (3, 3)]
    lines = create_file_content(M, K, seats)
    assert find_best_pair(lines) == (5, 8)


def test_tiebreaker_case():
    """Самая правая пара при нескольких вариантах в одном ряду."""
    M, K = 10, 10
    seats = [(10, 1), (10, 5)]
    lines = create_file_content(M, K, seats)
    assert find_best_pair(lines) == (10, 10)


def test_boundary_case():
    """Граничные условия (правый край зала)."""
    M, K = 100, 50
    seats = [(91, 49)] + [(10, s) for s in range(1, 49)]
    lines = create_file_content(M, K, seats)
    assert find_best_pair(lines) == (90, 50)


def test_low_row_trap_case():
    """Проверяет, что алгоритм не зависит от большого M и находит решение в низком ряду."""
    M, K = 200000, 100
    seats = [(11, 50)]
    for p in range(1, K):
        if p not in [50, 51]:
            seats.append((5, p))
    lines = create_file_content(M, K, seats)
    assert find_best_pair(lines) == (10, 51)


def test_all_value_errors():
    """Некорректные данные."""
    with pytest.raises(ValueError, match="ожидалось 3 числа, найдено 2"):
        find_best_pair(["10 100\n"])
    with pytest.raises(ValueError, match="нечисловые данные в 'a b c'"):
        find_best_pair(["a b c\n"])
    with pytest.raises(ValueError, match="неверные параметры N=1, M=-5, K=5"):
        find_best_pair(["1 -5 5\n"])
    with pytest.raises(ValueError, match="ожидалось 2 числа, найдено 1"):
        find_best_pair(["1 5 5\n", "10\n"])
    with pytest.raises(ValueError, match="нечисловые координаты в 'a b'"):
        find_best_pair(["1 5 5\n", "a b\n"])
    with pytest.raises(ValueError, match="координата .* вне зала"):
        find_best_pair(["1 5 5\n", "10 10\n"])


def test_empty_file():
    with pytest.raises(ValueError, match="Файл пустой."):
        find_best_pair([])


def test_main_success(monkeypatch, capsys, tmp_path):
    p = tmp_path / "testfile.txt"
    p.write_text("7 7 8\n1 1\n6 6\n5 5\n6 7\n4 4\n2 2\n3 3\n")
    monkeypatch.setattr("sys.argv", ["main.py", str(p)])
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "5 8"


def test_main_no_args(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["main.py"])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "Требуется ровно один аргумент" in captured.err


def test_main_file_not_found(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["main.py", "non_existent_file.txt"])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "No such file or directory" in captured.err


def test_main_bad_data(monkeypatch, capsys, tmp_path):
    """Файл с некорректными данными."""
    p = tmp_path / "badfile.txt"
    p.write_text("1 5 5\n10 10\n")
    monkeypatch.setattr("sys.argv", ["main.py", str(p)])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "координата (10, 10) вне зала 5x5" in captured.err
