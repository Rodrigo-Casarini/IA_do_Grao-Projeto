import ssl
import sys
from pathlib import Path

from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)
from django.core.servers.basehttp import WSGIServer


class SSLWSGIServer(WSGIServer):
    certfile = None
    keyfile = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.certfile, self.keyfile)
        self.socket = context.wrap_socket(self.socket, server_side=True)


class Command(RunserverCommand):
    help = "Starts a lightweight HTTPS server for development."
    protocol = "https"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--certificate",
            default=str(
                Path(sys.prefix) / "Lib" / "site-packages" / "sslserver" / "certs" / "development.crt"
            ),
            help="Path to the PEM certificate file.",
        )
        parser.add_argument(
            "--key",
            default=str(
                Path(sys.prefix) / "Lib" / "site-packages" / "sslserver" / "certs" / "development.key"
            ),
            help="Path to the PEM private key file.",
        )

    def inner_run(self, *args, **options):
        self.server_cls = type(
            "ConfiguredSSLWSGIServer",
            (SSLWSGIServer,),
            {"certfile": options["certificate"], "keyfile": options["key"]},
        )
        super().inner_run(*args, **options)
