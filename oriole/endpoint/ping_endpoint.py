from flask import request


class PingEndpoint:
    def get(self):
        return dict(_id=str(request.id), reply="pong")