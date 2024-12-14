CC = gcc
CFLAGS = -Wall -Wextra
LDFLAGS = 

all: test

bind.h: test.h
	../sbindgen -o bind.h -d bind.md test.h

test: test.c bind.h
	$(CC) $(CFLAGS) -o test test.c $(LDFLAGS)

clean:
	rm -f test bind.h doc.md
	
run: test
	./test