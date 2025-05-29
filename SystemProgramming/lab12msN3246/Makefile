CC = gcc
CFLAGS = -Wall -Wextra -Werror -O3 -D_XOPEN_SOURCE=700
LDFLAGS = -ldl
SRC = main.c utils.c
OBJ = $(SRC:.c=.o)
EXEC = lab12msN3246
PLUGIN_SRC = libmsN3246.c
PLUGIN_SO = libmsN3246.so

all: $(EXEC) $(PLUGIN_SO)

$(EXEC): $(OBJ)
	$(CC) $(OBJ) -o $(EXEC) $(LDFLAGS)

$(PLUGIN_SO): $(PLUGIN_SRC)
	$(CC) -shared -fPIC $(CFLAGS) $< -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ) $(EXEC) $(PLUGIN_SO)

.PHONY: all clean
