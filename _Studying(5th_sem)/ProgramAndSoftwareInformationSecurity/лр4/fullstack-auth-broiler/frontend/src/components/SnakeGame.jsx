import { useState, useEffect, useCallback } from 'react';

// --- Константы игры ---
const GRID_SIZE = 20;
const INITIAL_SNAKE = [{ x: 10, y: 10 }];
const INITIAL_DIRECTION = { x: 0, y: -1 }; // Начальное движение вверх
const GAME_SPEED = 150; // в миллисекундах

function SnakeGame({ onExit }) {
  // --- Состояние (State) ---
  const [snake, setSnake] = useState(INITIAL_SNAKE);
  const [direction, setDirection] = useState(INITIAL_DIRECTION);
  const [apple, setApple] = useState({ x: 15, y: 15 });
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // --- Игровая логика ---

  // Генерация нового яблока в случайном месте, не на змейке
  const generateApple = useCallback((currentSnake) => {
    let newApple;
    do {
      newApple = {
        x: Math.floor(Math.random() * GRID_SIZE),
        y: Math.floor(Math.random() * GRID_SIZE),
      };
    } while (
      currentSnake.some(
        (segment) => segment.x === newApple.x && segment.y === newApple.y
      )
    );
    return newApple;
  }, []);

  // Проверка столкновений
  const checkCollision = useCallback((head, body) => {
    // Столкновение со стенами
    if (head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE) {
      return true;
    }
    // Столкновение с собственным хвостом
    return body.some(
      (segment) => segment.x === head.x && segment.y === head.y
    );
  }, []);

  // Основной игровой цикл
  const gameLoop = useCallback(() => {
    if (!isPlaying || gameOver) return;

    setSnake((currentSnake) => {
      const newSnake = [...currentSnake];
      const head = { ...newSnake[0] };

      head.x += direction.x;
      head.y += direction.y;

      // Проверяем столкновение головы с хвостом (все, кроме головы)
      const snakeBody = newSnake.slice(1);
      if (checkCollision(head, snakeBody)) {
        setGameOver(true);
        setIsPlaying(false);
        return currentSnake;
      }

      newSnake.unshift(head); // Добавляем новую голову

      // Проверка на съедение яблока
      if (head.x === apple.x && head.y === apple.y) {
        setScore((prev) => prev + 10);
        setApple(generateApple(newSnake)); // Генерируем новое яблоко
      } else {
        newSnake.pop(); // Удаляем хвост, если яблоко не съедено
      }

      return newSnake;
    });
  }, [isPlaying, gameOver, direction, apple, checkCollision, generateApple]);

  // Обработка нажатий клавиш
  const handleKeyPress = useCallback(
    (e) => {
      if (!isPlaying) return;

      switch (e.key) {
        case 'ArrowUp':
          if (direction.y === 0) setDirection({ x: 0, y: -1 });
          break;
        case 'ArrowDown':
          if (direction.y === 0) setDirection({ x: 0, y: 1 });
          break;
        case 'ArrowLeft':
          if (direction.x === 0) setDirection({ x: -1, y: 0 });
          break;
        case 'ArrowRight':
          if (direction.x === 0) setDirection({ x: 1, y: 0 });
          break;
        default:
          break;
      }
    },
    [isPlaying, direction]
  );

  // --- Управление игрой ---

  const startGame = () => {
    setSnake(INITIAL_SNAKE);
    setDirection(INITIAL_DIRECTION);
    setApple({ x: 15, y: 15 });
    setGameOver(false);
    setScore(0);
    setIsPlaying(true);
  };

  const stopGame = () => {
    setIsPlaying(false);
  };

  // --- Эффекты (Side Effects) ---

  // Подписка и отписка от событий клавиатуры
  useEffect(() => {
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [handleKeyPress]);

  // Запуск и остановка интервала игрового цикла
  useEffect(() => {
    const interval = setInterval(gameLoop, GAME_SPEED);
    return () => clearInterval(interval);
  }, [gameLoop]);

  // --- Рендеринг (UI) ---

  const renderGrid = () => {
    const grid = [];
    for (let row = 0; row < GRID_SIZE; row++) {
      for (let col = 0; col < GRID_SIZE; col++) {
        let cellType = 'empty';
        const isSnakeHead =
          snake[0] && snake[0].x === col && snake[0].y === row;
        const isSnakeBody = snake
          .slice(1)
          .some((segment) => segment.x === col && segment.y === row);

        if (isSnakeHead) {
          cellType = 'snake-head';
        } else if (isSnakeBody) {
          cellType = 'snake-body';
        } else if (apple.x === col && apple.y === row) {
          cellType = 'apple';
        }
        grid.push(
          <div key={`${row}-${col}`} className={`game-cell ${cellType}`} />
        );
      }
    }
    return grid;
  };

  return (
    <div className="snake-game-container">
      <div className="game-header">
        <h2>🎮 Змейка - Приз за тестировку!</h2>
        <div className="game-stats">
          <span className="game-stats-status">
            {isPlaying ? 'Играем!' : gameOver ? 'Игра окончена' : 'Остановлена'}
          </span>
        </div>
      </div>
      <div className="game-controls">
        <button
          className="windows7-button"
          onClick={startGame}
          disabled={isPlaying}
        >
          {gameOver ? 'Играть снова' : 'Начать игру'}
        </button>
        <button
          className="windows7-button"
          onClick={stopGame}
          disabled={!isPlaying || gameOver}
        >
          Остановить
        </button>
        <button
          className="windows7-button"
          onClick={onExit}
        >
          ← На главную
        </button>
      </div>
      {!isPlaying && !gameOver && (
        <div className="game-instructions">
          <p>🎯 Цель игры: собирайте яблоки и растите змейку!</p>
          <p>⌨️ Управление: стрелочки на клавиатуре</p>
          <p>💀 Смерть: столкновение с границами или собственным хвостом</p>
          <p>🍎 Яблоки появляются случайно на игровом поле</p>
        </div>
      )}
      {gameOver && (
        <div className="game-over">
          <h3>💀 Игра окончена!</h3>
          <p>Финальный счет: {score}</p>
          <p>Попробуйте еще раз!</p>
        </div>
      )}
      <div className="game-board">{renderGrid()}</div>
      <div className="game-legend">
        <div className="legend-item">
          <div className="legend-color snake-head"></div>
          <span>Голова змейки</span>
        </div>
        <div className="legend-item">
          <div className="legend-color snake-body"></div>
          <span>Тело змейки</span>
        </div>
        <div className="legend-item">
          <div className="legend-color apple"></div>
          <span>Яблоко (+10 очков)</span>
        </div>
      </div>
    </div>
  );
}

export default SnakeGame;
