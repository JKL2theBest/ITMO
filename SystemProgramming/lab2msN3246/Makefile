CC = gcc
CFLAGS = -Wall -Wextra -Werror -O3
LDFLAGS = -lm
TARGETS = lab2msN3246_client lab2msN3246_server

.PHONY: all clean

all: $(TARGETS)

%: %.c
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

clean:
	rm -f $(TARGETS)
