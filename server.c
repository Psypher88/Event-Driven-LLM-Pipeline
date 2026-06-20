#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#define PORT 9000
#define BUFFER_SIZE 256
#define CIRCUIT_BREAKER_THRESHOLD -4

/* Purpose: check if a sentiment score is too extreme to forward
 * Input: value (int) - the score received from the client
 * Output: (int) 1 if circuit breaker triggered, 0 if safe to proceed */
int check_circuit_breaker(int value) {
    if (value <= CIRCUIT_BREAKER_THRESHOLD) {
        printf("CIRCUIT BREAKER triggered: value %d is at or below threshold %d\n",
               value, CIRCUIT_BREAKER_THRESHOLD);
        return 1;
    }
    return 0;
}

/* Purpose: initialize the Winsock subsystem (required on Windows before any socket call)
 * Input: none
 * Output: (int) 0 on success, -1 on failure */
int init_winsock() {
    WSADATA wsa;
    int result;

    result = WSAStartup(MAKEWORD(2, 2), &wsa);
    if (result != 0) {
        printf("WSAStartup failed, error: %d\n", result);
        return -1;
    }
    return 0;
}

/* Purpose: create a TCP socket, bind to PORT, and start listening
 * Input: none
 * Output: SOCKET handle on success, INVALID_SOCKET on failure */
SOCKET create_server_socket() {
    SOCKET server_fd;
    struct sockaddr_in addr;
    int opt = 1;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == INVALID_SOCKET) {
        printf("socket() failed, error: %d\n", WSAGetLastError());
        return INVALID_SOCKET;
    }

    /* allow port reuse so server can restart quickly */
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, (char *)&opt, sizeof(opt));

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr)) == SOCKET_ERROR) {
        printf("bind() failed, error: %d\n", WSAGetLastError());
        closesocket(server_fd);
        return INVALID_SOCKET;
    }

    if (listen(server_fd, 5) == SOCKET_ERROR) {
        printf("listen() failed, error: %d\n", WSAGetLastError());
        closesocket(server_fd);
        return INVALID_SOCKET;
    }

    return server_fd;
}

/* Purpose: receive data from a client, run circuit breaker check, echo back if safe
 * Input: client_fd (SOCKET) - handle of the connected client
 * Output: none */
void handle_client(SOCKET client_fd) {
    char buffer[BUFFER_SIZE];
    int bytes_received;
    int value;
    int breaker;

    memset(buffer, 0, BUFFER_SIZE);
    bytes_received = recv(client_fd, buffer, BUFFER_SIZE - 1, 0);

    if (bytes_received <= 0) {
        printf("client disconnected or recv error\n");
        closesocket(client_fd);
        return;
    }

    buffer[bytes_received] = '\0';
    printf("received: %s\n", buffer);

    value = atoi(buffer);  /* convert string to int for circuit breaker check */
    breaker = check_circuit_breaker(value);

    if (breaker == 1) {
        /* close without sending anything back */
        closesocket(client_fd);
        return;
    }

    /* echo data back to client */
    send(client_fd, buffer, bytes_received, 0);
    printf("forwarded data back to client\n");

    closesocket(client_fd);
}

int main() {
    SOCKET server_fd;
    SOCKET client_fd;
    struct sockaddr_in client_addr;
    int client_len;
    fd_set read_fds;
    int activity;

    if (init_winsock() != 0) {
        return 1;
    }

    server_fd = create_server_socket();
    if (server_fd == INVALID_SOCKET) {
        WSACleanup();
        return 1;
    }

    printf("waiting for connections on port %d\n", PORT);
    printf("press Ctrl+C to stop\n");

    while (1) {
        FD_ZERO(&read_fds);
        FD_SET(server_fd, &read_fds);

        /* select blocks until a connection arrives (avoids busy-wait) */
        activity = select(0, &read_fds, NULL, NULL, NULL);

        if (activity == SOCKET_ERROR) {
            printf("select() failed, error: %d\n", WSAGetLastError());
            break;
        }

        if (FD_ISSET(server_fd, &read_fds)) {
            client_len = sizeof(client_addr);
            client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);

            if (client_fd == INVALID_SOCKET) {
                printf("accept() failed, error: %d\n", WSAGetLastError());
                continue;
            }

            printf("new client connected\n");
            handle_client(client_fd);
        }
    }

    closesocket(server_fd);
    WSACleanup();
    return 0;
}
