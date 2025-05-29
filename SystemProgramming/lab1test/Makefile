CFLAGS=-Wall -Wextra -Werror -O2
TARGETS=lab1test lab1call libavg.so

.PHONY: all clean

all: $(TARGETS)

clean:
	rm -rf *.o $(TARGETS)

lab1test: lab1test.c plugin_api.h
	gcc $(CFLAGS) -o lab1test lab1test.c -ldl

lab1call: lab1call.c plugin_api.h
	gcc $(CFLAGS) -o lab1call lab1call.c -ldl

libavg.so: libavg.c plugin_api.h
	gcc $(CFLAGS) -shared -fPIC -o libavg.so libavg.c -ldl -lm


