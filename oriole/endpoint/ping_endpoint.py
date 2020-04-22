from typing import Dict, Optional

from flask import request


class PingEndpoint:
    def get(self):
        return dict(_id=str(request.id), reply="pong")


class DynamicPingEndpoint:
    def get(self, id):
        return dict(_id=str(request.id), reply=f"pong for {id}")
