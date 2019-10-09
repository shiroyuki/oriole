import argparse
import datetime
import json
from typing import Dict, Optional
import uuid

from flask import Flask
from flask import request
from flask import Request, Response

from imagination.standalone import container

from werkzeug.exceptions import (BadRequest, NotFound, MethodNotAllowed,
                                 PreconditionRequired, Unauthorized, Forbidden,
                                 InternalServerError)

from oriole.helper.logger_factory import LoggerFactory
from oriole.security.authenticator import Authenticator, InvalidTokenError, ExpiredTokenError
from oriole.service.front_controller import FrontController

logger = LoggerFactory.get(__name__)

app = Flask(__name__)
auto_path_prefix = '/experimental'


def make_json_response(content, status: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    resp = Response(json.dumps(_normalize_value(content),
                               sort_keys=True),
                    status=status,
                    headers=headers or dict(),
                    content_type='application/json')

    return resp


def _normalize_value(o):
    if isinstance(o, (list, tuple)):
        return [
            _normalize_value(i)
            for i in o
        ]

    if isinstance(o, dict):
        return {
            k: _normalize_value(v)
            for k, v in o.items()
        }

    if isinstance(o, datetime.datetime):
        return o.strftime('%Y-%m-%d %H:%M:%S')

    if isinstance(o, (bool, int, float, str)):
        return o

    if o is None:
        return None

    data = dict()

    for attribute_name in dir(o):
        if '_' == attribute_name[0]:
            continue

        attribute = getattr(o, attribute_name)

        if callable(attribute):
            continue

        data[attribute_name] = _normalize_value(attribute)

    return data


def make_error_response(code, details=None, status: int = 500) -> Response:
    return make_json_response(dict(code=code, details=details), status)


@app.before_request
def protected():
    """
    Enforce the bearer token authentication

    .. note:: In this method, returning nothing will yield back to the request handling methods.
    """
    current_request: Request = request
    request_path = current_request.path
    request_method = current_request.method
    request.id = uuid.uuid4()
    request.claims = dict()
    request.user_id = None

    non_secure_requests = [
        # dict(method: str, rule: str)
    ]

    if request_method == 'OPTIONS':
        return _allow_cors(Response('', status=200, content_type='text/plain'))

    for non_secure_request in non_secure_requests:
        if request_method == non_secure_request.get('method') and request_path == non_secure_request.get('rule'):
            logger.debug(f'REQUEST {request.id}: Request to {request_path} is extempted from authentication check.')
            return

    try:
        bearer_token = current_request.headers['authorization']
    except KeyError:
        return _allow_cors(
            make_error_response('missing_bearer_token', status=401)
        )

    if not bearer_token.startswith('Bearer '):
        return _allow_cors(
            make_error_response('bearer_token_required', status=401)
        )

    authenticator: Authenticator = container.get(Authenticator)

    try:
        access_token = bearer_token[7:]
        request.claims = authenticator.decode_token(access_token)
        request.user_id = request.claims['sub']
    except InvalidTokenError:
        logger.warning(f'REQUEST {request.id}: Someone tried to use a fake token ("{access_token}").')
        return _allow_cors(
            make_error_response('invalid_token', status=401)
        )
    except ExpiredTokenError:
        logger.info(f'REQUEST {request.id}: Intercepted an expired token ("{access_token}").')
        return _allow_cors(
            make_error_response('expired_token', status=401)
        )


@app.after_request
def finalize_response(response: Response):
    return _finalize_response(response)


@app.route(f'{auto_path_prefix}/<path:request_path>', methods=('POST', 'GET', 'PUT', 'DELETE', 'PATCH'))
def delegate_to_front_controller(request_path):
    fc: FrontController = container.get(FrontController)

    method = str(request.method).lower()

    if request_path == 'all':
        if method != 'get':
            return make_error_response('method_not_allowed', status=405)
        return make_json_response(fc.route_map)
    if request_path not in fc.route_map:
        return make_error_response('endpoint_not_found', status=404)

    route = fc.route_map[request_path]

    if not hasattr(route.handler, method):
        return make_error_response('method_not_allowed',
                                   details=dict(handler_class_name=type(route.handler).__name__,
                                                handler_module_name=type(route.handler).__module__,
                                                method=method.upper()),
                                   status=405)

    return make_json_response(getattr(route.handler(), method)())


def handle_error(e):
    return _finalize_response(make_error_response(type(e).__name__, None, e.code))


app.register_error_handler(BadRequest, handle_error)
app.register_error_handler(Unauthorized, handle_error)
app.register_error_handler(Forbidden, handle_error)
app.register_error_handler(NotFound, handle_error)
app.register_error_handler(MethodNotAllowed, handle_error)
app.register_error_handler(PreconditionRequired, handle_error)
app.register_error_handler(InternalServerError, handle_error)


def _finalize_response(response: Response):
    _allow_cors(response)

    response.headers['Server'] = 'zg-api/1.0'
    response.headers['X-Request-ID'] = request.id

    if 'X-State' in request.headers:
        response.headers['X-State'] = request.headers['X-State']

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    logger.debug(f'Responding {response.data.decode()}')

    return response


def _allow_cors(response: Response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = ', '.join(('Content-Type', 'Authorization', 'X-State',
                                                                  'X-Cors-Mode', 'X-State'))
    response.headers['Access-Control-Allow-Methods'] = ', '.join(('POST', 'GET', 'OPTIONS', 'PUT', 'DELETE', 'PATCH'))

    return response


def main(args: argparse.Namespace):
    app.run(host='0.0.0.0', debug=args.debug)
