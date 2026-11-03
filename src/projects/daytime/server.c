// daytime server
// compile: gcc -o server server.c

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <netinet/in.h>

// puts current time into buf
void get_time(char *buf) {
    time_t now;
    struct tm *t;
    now = time(NULL);
    t = localtime(&now);
    strftime(buf, 64, "%Y-%m-%dT%H:%M:%S\n", t);
}

int main(int argc, char *argv[]) {
    int tcp = 0;
    int udp = 0;
    int port = 13;
    int i;
    int sock;
    char msg[64];
    struct sockaddr_in addr;

    // parse args
    for (i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("usage: %s [-t] [-u] [-p PORT]\n", argv[0]);
            printf("  -t, --tcp   use TCP\n");
            printf("  -u, --udp   use UDP\n");
            printf("  -p PORT     port number\n");
            return 0;
        } else if (strcmp(argv[i], "-t") == 0 || strcmp(argv[i], "--tcp") == 0) {
            tcp = 1;
        } else if (strcmp(argv[i], "-u") == 0 || strcmp(argv[i], "--udp") == 0) {
            udp = 1;
        } else if (strcmp(argv[i], "-p") == 0 || strcmp(argv[i], "--port") == 0) {
            i++;
            port = atoi(argv[i]);
        }
    }

    if (tcp == 0 && udp == 0) {
        printf("pick --tcp or --udp\n");
        return 1;
    }
    if (tcp == 1 && udp == 1) {
        printf("pick only one protocol\n");
        return 1;
    }

    // set up address
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);

    if (tcp == 1) {
        int conn;
        int opt = 1;

        sock = socket(AF_INET, SOCK_STREAM, 0);
        setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        bind(sock, (struct sockaddr *)&addr, sizeof(addr));
        listen(sock, 5);

        printf("Starting a TCP server on port %d\n", port);

        while (1) {
            conn = accept(sock, NULL, NULL);
            get_time(msg);
            send(conn, msg, strlen(msg), 0);
            close(conn);
        }
    } else {
        // udp
        struct sockaddr_in client;
        socklen_t len;
        char buf[1024];

        sock = socket(AF_INET, SOCK_DGRAM, 0);
        bind(sock, (struct sockaddr *)&addr, sizeof(addr));

        printf("Starting a UDP server on port %d\n", port);

        while (1) {
            len = sizeof(client);
            recvfrom(sock, buf, 1024, 0, (struct sockaddr *)&client, &len);
            get_time(msg);
            sendto(sock, msg, strlen(msg), 0, (struct sockaddr *)&client, len);
        }
    }

    return 0;
}
