from re import findall
from socket import socket, AF_INET, SOCK_STREAM
from sys import argv, exit, stderr, stdout


def get_url_input() -> str:
    # program should take exactly one parameter
    if len(argv) != 2:
        exit(1)
    return argv[1]


def get_url_parts(url: str) -> tuple:
    # input url must start with 'http://'
    if url[:5] == "https":
        stderr.write("Program does not support HTTPS protocol.")
        exit(1)
    if url[:7] != "http://":
        exit(1)

    host_and_page, port = findall("http://([^:]+):?([0-9]+)?", url)[0]
    host, page = findall("([^/]+)(/.+)?", host_and_page)[0]

    return host, "/" if page == "" else page, 80 if port == "" else int(port)


def get_header_info(s, data: list) -> str:
    ans = []
    while True:
        buf = s.recv(1)
        buf_decoded = buf.decode()
        if buf_decoded == "\r":
            data.append("\r")
            break
        ans.append(buf_decoded)
        data.append(buf_decoded)
    return "".join(ans)


def make_get_request(url: str) -> bool:
    host, page, port = get_url_parts(url)

    s = socket(AF_INET, SOCK_STREAM)
    s.connect((host, port))
    req = f"GET {page} HTTP/1.0\r\nHost: {host}\r\n\r\n"
    s.sendall(req.encode())

    status_code = 0
    content_len = 0
    content_type = ""

    data = []
    is_body = False
    while True:
        # receive one byte at a time; break when no more
        buf = s.recv(1)
        if not buf:
            break
        data.append(buf.decode())

        # get response status code
        if len(data) == 12:
            status_code = int("".join(data[-3:]))

        # if two consecutive returns, then body starts
        if "".join(data[-4:]) == "\r\n\r\n":
            is_body = True

        # if body started and content length specified, break when content length bytes are received
        if is_body and content_len:
            content_len -= 1
            if content_len == 0:
                break

        # if body not started, check for content length and content type info
        if not is_body:
            if not content_len and "".join(data[-16:]) == "Content-Length: ":
                content_len = int(get_header_info(s, data))
            if not content_type and "".join(data[-14:]) == "Content-Type: ":
                content_type = get_header_info(s, data)
                if content_type[:9] != "text/html":
                    return False
            if status_code in [301, 302] and "".join(data[-10:]) == "Location: ":
                redirect_url = get_header_info(s, data)
                return make_get_request(redirect_url)

    stdout.write("".join(data))
    return status_code < 400


def main() -> None:
    url = get_url_input()
    if not make_get_request(url):
        exit(1)
    exit(0)


if __name__ == "__main__":
    main()
