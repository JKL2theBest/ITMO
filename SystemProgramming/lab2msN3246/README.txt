lab2abc_client.c

Принимает 2 строки:
Числа
Способ округления: floor (в сторону минус бесконечности), ceil (в сторону плюс бесконечности), trunc (в сторону нуля)
A simple TCP client that connects to a server, sends two lines of input:

Usage:
  lab2msN3246_client [опции] ["Числа"] [Округление]

Если числа или округление не задано - считать с stdin

----------------------------------------------------

lab2abc_server.c

Принимает 2 строки и выдает округленные числа

Usage:
  lab2msN3246_server [опции]
