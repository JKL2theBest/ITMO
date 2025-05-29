CC = gcc
CFLAGS = -Wall -Wextra -Werror -pthread -O3
LDFLAGS = -lm 

SRC = main.c queue.c psrs.c bm.c
OBJ = $(SRC:.c=.o)
TARGET = psrs

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJ) $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(TARGET)
