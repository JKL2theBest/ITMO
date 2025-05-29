CC = gcc
CFLAGS = -Wall -Wextra -Werror -pthread -lm -O3
SRC = main.c psrs.c
OBJ = $(SRC:.c=.o)
TARGET = psrs

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJ)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)
