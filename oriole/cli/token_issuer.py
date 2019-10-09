from argparse import ArgumentParser

from gallium.interface import ICommand
from imagination.standalone import container
from oriole.security.authenticator import Authenticator


class TokenIssuerCommand(ICommand):
    def identifier(self):
        return 'jwt:issue'

    def define(self, parser: ArgumentParser):
        parser.add_argument('subject', help='Subject')
        parser.add_argument('scopes', nargs='+', help='Access Scopes')

    def execute(self, args):
        authenticator: Authenticator = container.get(Authenticator)
        token = authenticator.encode_token(dict(sub=args.subject, scopes=args.scopes))

        print(f'Bearer Token: {token}')
        print(f'Claims: {authenticator.decode_token(token)}')
