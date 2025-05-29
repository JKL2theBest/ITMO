%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Программа для получения двумерной картины случайных блужданий частиц, %
% вышедших из одной точки и построение графика функции распределения R = sqrt(x^2+y^2) %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Инициализация параметров
n = 500; 
steps = 1000; % Число шагов
dh = 0.02; 
x = zeros(n,1); 
y = zeros(n,1); 

% Создание фигуры и осей для анимации
figure;
h1 = scatter(x, y, 'k.'); 
axis([-2 2 -2 2]); 
set(h1, 'Marker', '.');

% Бесконечный цикл для анимации
for i = 1:steps
    dx = dh*(2*rand(n,1)-1); 
    dy = dh*(2*rand(n,1)-1); 
    x = x + dx;
    y = y + dy;
    set(h1, 'XData', x, 'YData', y); 
    drawnow;
end

% Вычисление расстояния от начала координат R
R = sqrt(x.^2 + y.^2);

% Создание осей для гистограммы
figure;
h2 = histogram(R, 'Normalization', 'pdf'); 
hold on;
Rmin = min(R); Rmax = max(R);
R_values = linspace(Rmin, Rmax, 100);
f = @(r) r/(sqrt(2*pi*n*dh^2)) .* exp(-r.^2/(2*n*dh^2)); % Теоретическая функция
plot(R_values, f(R_values), 'r'); 
hold off;
axis([Rmin Rmax 0 1]);
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%