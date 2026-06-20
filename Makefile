all:
	gcc server.c -o server -lws2_32

clean:
	del server.exe
