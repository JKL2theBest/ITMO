CC = gcc
CFLAGS = -Wall -Wextra -Werror -g -O3
LDFLAGS =

SRCS = lab11msN3246.c

OBJS = $(SRCS:.c=.o)

APP = lab11msN3246

.PHONY: all clean

all: $(APP)

$(APP): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $<

clean:
	@rm -f $(OBJS) $(APP)
