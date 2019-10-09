import dataclasses
import importlib
from typing import Any, Dict

from imagination.decorator import service

from oriole.helper.logger_factory import LoggerFactory

logger = LoggerFactory.get(__name__)


class MissingRouteConfigKeyError(RuntimeError):
    pass


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
        self.route_map[path] = Route(handler=handler)

        logger.info('Route %s: Handled by %s', path, handler)


@dataclasses.dataclass(frozen=True)
class Route:
    handler: Any
