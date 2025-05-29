% Параметры зарядов
charges = [1, -1, 1, -1]; % Заряды (Кл)
charges_x = [-1, 1, 1, -1]; % Координаты зарядов по x (м)
charges_y = [-1, -1, 1, 1]; % Координаты зарядов по y (м)

% Сетка расчета (уменьшена для ускорения)
x = linspace(-5, 5, 100);
y = linspace(-5, 5, 100);
[X, Y] = meshgrid(x, y);

% Константы
k = 9e9; % Электростатическая постоянная (Н·м²/Кл²)
num_frames = 200; % Количество кадров анимации
dt = 0.05; % Шаг времени для движения зарядов
speed = 20; % Скорость движения зарядов (м/с) — увеличена для более быстрого движения

figure;

for frame = 1:num_frames
    % Обновление координат зарядов (хаотичное движение)
    charges_x = charges_x + (rand(1, length(charges)) - 0.5) * speed * dt;
    charges_y = charges_y + (rand(1, length(charges)) - 0.5) * speed * dt;
    charges_x = max(min(charges_x, max(x)), min(x));
    charges_y = max(min(charges_y, max(y)), min(y));

    % Расчёт потенциала
    phi = zeros(size(X)); % Матрица для потенциала
    for i = 1:length(charges)
        r = sqrt((X - charges_x(i)).^2 + (Y - charges_y(i)).^2);
        phi = phi + k * charges(i) ./ r;
    end
    phi(isinf(phi)) = NaN;

    % Масштабирование потенциала для визуализации
    phi_scaled = log(abs(phi));

    % Расчёт напряжённости электрического поля (градиент потенциала)
    [Ex, Ey] = gradient(-phi, x(2) - x(1), y(2) - y(1));

    % Построение эквипотенциальных поверхностей
    subplot(1, 2, 1);
    contour(X, Y, phi_scaled, 50, 'LineWidth', 1.5);
    hold on;
    scatter(charges_x(charges > 0), charges_y(charges > 0), 100, 'filled', 'r');
    scatter(charges_x(charges < 0), charges_y(charges < 0), 100, 'filled', 'b');
    hold off;
    axis equal;
    title('Эквипотенциальные поверхности');
    xlabel('x, м');
    ylabel('y, м');
    colormap('parula');
    colorbar;

    % Построение силовых линий
    subplot(1, 2, 2);
    quiver(X, Y, Ex, Ey, 'k');
    hold on;
    streamslice(X, Y, Ex, Ey)
    scatter(charges_x(charges > 0), charges_y(charges > 0), 100, 'filled', 'r');
    scatter(charges_x(charges < 0), charges_y(charges < 0), 100, 'filled', 'b');
    hold off;
    axis equal;
    title('Силовые линии');
    xlabel('x, м');
    ylabel('y, м');

    pause(1 / 60);
    drawnow;
end

disp('Анимация завершена.');
