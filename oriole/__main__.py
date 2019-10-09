import argparse
import importlib
import logging
import os

import yaml

from imagination.standalone import container

from oriole.helper.logger_factory import LoggerFactory
from oriole.service.front_controller import FrontController

from .base.exc import UnknownBackendModeError

parser = argparse.ArgumentParser('oriole')
parser.add_argument('--config-file', '-f', help='Configuration file path', default=os.path.abspath(os.path.join(os.getcwd(), 'config/app.yml')))
parser.add_argument('--debug', '-d', action='store_true', help='Enable the debug mode')

args = parser.parse_args()

logger = LoggerFactory.get('oriole', level=logging.DEBUG if args.debug else None)

logger.debug('Application Configuration File: %s', args.config_file)

with open(args.config_file) as f:
    config = yaml.load(f.read(), yaml.SafeLoader)

    fc: FrontController = container.get(FrontController, lock_down_enabled=False)

    fc.map(config['routes'])

    main_web_module_name = f'oriole.{config["backend"]}.web'

    try:
        web = importlib.import_module(main_web_module_name)
        web.main(args)
    except ImportError:
        raise UnknownBackendModeError(f'The "backend" configuration can only be either "sync" or "async".')
