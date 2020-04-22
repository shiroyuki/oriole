import dataclasses
import importlib
import re
from typing import Any, Dict

from imagination.decorator import service

from oriole.helper.logger_factory import LoggerFactory

logger = LoggerFactory.get(__name__)


class MissingRouteConfigKeyError(RuntimeError):
    pass


class RouteNotFoundError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class Route:
    handler: Any
    secured: bool


@service.registered()
class FrontController:
    def __init__(self):
        self.route_map: Dict[str, Route] = dict()

    def map(self, route_map: Dict[str, Dict[str, Any]]):
        for path, handling_config in route_map.items():
            self.map_one(path, handling_config)

    def map_one(self, path: str, route_config: Dict[str, Any]):
        if 'handler' not in route_config:
            raise MissingRouteConfigKeyError('handler')

        module_name_blocks = route_config['handler'].split('.')
        module = importlib.import_module('.'.join(module_name_blocks[0:-1]))
        handler = getattr(module, module_name_blocks[-1])

        self.route_map[path] = Route(
            handler=handler,
            secured=route_config.get('secured') or False,
        )

        logger.info('Route %s: Handled by %s', path, handler)

    def find_route(self, request_path: str) -> Route:
        for routing_pattern in self.route_map:
            if re.match(routing_pattern, request_path):
                route = self.route_map[routing_pattern]
                return route

        raise RouteNotFoundError(request_path)

    def require_access_control(self, request_path: str):
        route = self.find_route(request_path)

        return route.secured
