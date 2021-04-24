from http import HTTPStatus
import mimetypes
import os

mimetypes.init()


class HttpProcess:
    def __init__(self, host, port, path_if_not_found):
        self.host = host
        self.port = port
        self.path_if_not_found = path_if_not_found

    async def process_request(self, sever_root, path, request_headers):
        """Serves a file when doing a GET request with a valid path."""

        if "Upgrade" in request_headers:
            return  # Probably a WebSocket connection
        is_download = True if path.endswith('?download') else False
        if is_download:
            path = path.replace('?download', '')
        if path == '/':
            path = '/index.html'

        response_headers = [
            ('Server', 'IHF Server'),
            ('Connection', 'close'),
        ]

        # Derive full system path
        full_path = os.path.realpath(os.path.join(sever_root + '/www', path[1:]))

        if "/private/" in full_path:
            print("HTTP GET {} 403 FORBIDDEN".format(path))
            return HTTPStatus.FORBIDDEN, [], b'403 FORBIDDEN'
        if os.path.isdir(full_path):
            full_path += '/index.html'
        # Validate the path
        if os.path.commonpath((sever_root, full_path)) != sever_root or \
                not os.path.exists(full_path) or not os.path.isfile(full_path):
            full_path = self.path_if_not_found + '/' + path[1:]
            if not os.path.isfile(full_path):
                print("HTTP GET {} 404 NOT FOUND".format(path))
                return HTTPStatus.NOT_FOUND, [], b'404 NOT FOUND'

        extension = full_path.split(".")[-1]
        mime_type = "application/octet-stream" if is_download else mimetypes.types_map.get('.' + extension, "application/octet-stream")
        response_headers.append(('Content-Type', mime_type))

        # Read the whole file into memory and send it out
        if extension in ['html', 'htm']:
            body = open(full_path, 'r').read()
            body = bytes(body.replace('{host}', self.host).replace('{port}', str(self.port)), encoding='utf8')
        else:
            body = open(full_path, 'rb').read()
        response_headers.append(('Content-Length', str(len(body))))
        print("HTTP GET {} 200 OK".format(path))
        return HTTPStatus.OK, response_headers, body
