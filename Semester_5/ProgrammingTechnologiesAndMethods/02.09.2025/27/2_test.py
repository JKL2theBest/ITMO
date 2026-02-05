import pytest
import numpy as np
from main import load_points, solve_clusters, main


def test_basic_scenario(tmp_path):
    """Базовый сценарий с двумя кластерами и шумом."""
    p = tmp_path / "test_data.txt"
    cluster1 = "\n".join(
        [f"{1+i*0.01:.2f} {1+i*0.01:.2f}".replace(".", ",") for i in range(11)]
    )
    cluster2 = "\n".join(
        [f"{10+i*0.01:.2f} {10+i*0.01:.2f}".replace(".", ",") for i in range(11)]
    )
    p.write_text(f"{cluster1}\n{cluster2}\n50,0 50,0")

    points = load_points(str(p))
    d_min, d_max = solve_clusters(points, str(p), expected_clusters=2)

    c1 = np.array([[1 + i * 0.01, 1 + i * 0.01] for i in range(11)])
    c2 = np.array([[10 + i * 0.01, 10 + i * 0.01] for i in range(11)])

    assert d_min == pytest.approx(np.linalg.norm(c1[-1] - c2[0]))
    assert d_max == pytest.approx(np.linalg.norm(c1[0] - c2[-1]))


def test_file_and_data_errors(tmp_path):
    """Ошибки формата и содержимого файла."""
    with pytest.raises(FileNotFoundError):
        load_points("non_existent_file.txt")
    p_empty = tmp_path / "empty.txt"
    p_empty.touch()
    with pytest.raises(ValueError, match="Файл пуст"):
        load_points(str(p_empty))
    p_bad_data = tmp_path / "bad_data.txt"
    p_bad_data.write_text("1,0 a\n2,0 3,0")
    with pytest.raises(ValueError, match="некорректный формат"):
        load_points(str(p_bad_data))
    p_wrong_dims = tmp_path / "wrong_dims.txt"
    p_wrong_dims.write_text("1,0 2,0 3,0")
    with pytest.raises(ValueError, match="некорректный формат в '1,0 2,0 3,0'"):
        load_points(str(p_wrong_dims))


def test_file_with_blank_line(tmp_path):
    """Пропуск пустых строк внутри файла."""
    p = tmp_path / "blank_line.txt"
    p.write_text("1,0 1,0\n\n2,0 2,0")
    assert load_points(str(p)).shape == (2, 2)


def test_logic_errors(tmp_path):
    """Логические ошибки (неверное число кластеров)."""
    p = tmp_path / "one_cluster.txt"
    cluster_text = "\n".join([f"{1+i*0.01:.2f} {1+i*0.01:.2f}" for i in range(11)])
    p.write_text(cluster_text)
    points = load_points(str(p))
    with pytest.raises(RuntimeError, match="найдено 1 кластеров, ожидалось 2"):
        solve_clusters(points, str(p), expected_clusters=2)


def test_main_success(tmp_path, monkeypatch, capsys):
    p = tmp_path / "a.txt"
    cluster_text = "\n".join([f"{1+i*0.01:.2f} {1+i*0.01:.2f}" for i in range(11)])
    p.write_text(cluster_text)
    monkeypatch.setattr("sys.argv", ["main.py", str(p), "1"])
    main()
    captured = capsys.readouterr()
    assert captured.out.strip() == "0\n0"


def test_main_arg_errors(monkeypatch, capsys):
    """Ошибки аргументов командной строки."""
    scenarios = [
        ["main.py"],
        ["main.py", "file.txt"],
        ["main.py", "file.txt", "two"],
        ["main.py", "file.txt", "0"],
    ]
    for args in scenarios:
        monkeypatch.setattr("sys.argv", args)
        with pytest.raises(SystemExit):
            main()
    captured = capsys.readouterr()
    assert "Число кластеров должно быть целым > 0" in captured.err
