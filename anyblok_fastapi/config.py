from os import environ
from typing import TYPE_CHECKING

from anyblok.config import AnyBlokPlugin, Configuration
from anyblok.config import get_db_name as gdb
from starlette.requests import Request

if TYPE_CHECKING:
    from anyblok.config import AnyBlokArgumentGroup

Configuration.add_application_properties(
    "uvicorn",
    ["logging", "uvicorn", "plugins"],
    prog="AnyBlok asgi app, version",
    description="ASGI AnyBlok / uvicorn / Starlette / FastAPI app",
)

Configuration.add_application_properties(
    "gunicorn",
    [],
    prog="AnyBlok gunicorn asgi app",
    description="WSGI for test your AnyBlok / Pyramid app",
    configuration_groups=["logging", "gunicorn", "database", "plugins"],
)


def get_db_name(request: Request) -> str:
    return gdb()


@Configuration.add("uvicorn", label="Uvicorn")
def define_uvicorn_option(group: "AnyBlokArgumentGroup") -> None:
    group.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Bind socket to this host.",
    )

    group.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Bind socket to this port.",
    )
    # group.add_argument("--uds", type=str, default=None, help="Bind to a UNIX domain socket.")
    # group.add_argument(
    #     "--fd", type=int, default=None, help="Bind to socket from this file descriptor."
    # )
    group.add_argument(
        "--debug", action="store_true", default=False, help="Enable debug mode."
    )
    group.add_argument(
        "--reload", action="store_true", default=False, help="Enable auto-reload."
    )
    # group.add_argument(
    #     "--reload-dir",
    #     "reload_dirs",
    #     multiple=True,
    #     help="Set reload directories explicitly, instead of using the current working"
    #     " directory.",
    # )
    group.add_argument(
        "--workers",
        default=None,
        type=int,
        help="Number of worker processes. Defaults to the $WEB_CONCURRENCY environment"
        " variable if available. Not valid with --reload.",
    )
    # group.add_argument(
    #     "--loop",
    #     type=LOOP_CHOICES,
    #     default="auto",
    #     help="Event loop implementation.",

    # )
    # group.add_argument(
    #     "--http",
    #     type=HTTP_CHOICES,
    #     default="auto",
    #     help="HTTP protocol implementation.",

    # )
    # group.add_argument(
    #     "--ws",
    #     type=WS_CHOICES,
    #     default="auto",
    #     help="WebSocket protocol implementation.",

    # )
    # group.add_argument(
    #     "--lifespan",
    #     type=LIFESPAN_CHOICES,
    #     default="auto",
    #     help="Lifespan implementation.",

    # )
    # group.add_argument(
    #     "--interface",
    #     type=INTERFACE_CHOICES,
    #     default="auto",
    #     help="Select ASGI3, ASGI2, or WSGI as the application interface.",

    # )
    # group.add_argument(
    #     "--env-file",
    #     type=click.Path(exists=True),
    #     default=None,
    #     help="Environment configuration file.",

    # )
    # group.add_argument(
    #     "--log-config",
    #     type=click.Path(exists=True),
    #     default=None,
    #     help="Logging configuration file.",

    # )
    # group.add_argument(
    #     "--log-level",
    #     type=LEVEL_CHOICES,
    #     default=None,
    #     help="Log level. [default: info]",

    # )
    group.add_argument(
        "--access-log/--no-access-log",
        action="store_true",
        default=True,
        help="Enable/Disable access log.",
    )
    group.add_argument(
        "--use-colors/--no-use-colors",
        action="store_true",
        default=None,
        help="Enable/Disable colorized logging.",
    )
    group.add_argument(
        "--proxy-headers/--no-proxy-headers",
        action="store_true",
        default=True,
        help="Enable/Disable X-Forwarded-Proto, X-Forwarded-For, X-Forwarded-Port to "
        "populate remote address info.",
    )
    group.add_argument(
        "--forwarded-allow-ips",
        type=str,
        default=None,
        help="Comma seperated list of IPs to trust with proxy headers. Defaults to"
        " the $FORWARDED_ALLOW_IPS environment variable if available, or '127.0.0.1'.",
    )
    group.add_argument(
        "--root-path",
        type=str,
        default="",
        help="Set the ASGI 'root_path' for applications submounted below a given URL path.",
    )
    group.add_argument(
        "--limit-concurrency",
        type=int,
        default=None,
        help="Maximum number of concurrent connections or tasks to allow, before issuing"
        " HTTP 503 responses.",
    )
    group.add_argument(
        "--backlog",
        type=int,
        default=2048,
        help="Maximum number of connections to hold in backlog",
    )
    group.add_argument(
        "--limit-max-requests",
        type=int,
        default=None,
        help="Maximum number of requests to service before terminating the process.",
    )
    group.add_argument(
        "--timeout-keep-alive",
        type=int,
        default=5,
        help="Close Keep-Alive connections if no new data is received within this timeout.",
    )
    # group.add_argument(
    #     "--ssl-keyfile", type=str, default=None, help="SSL key file"
    # )
    # group.add_argument(
    #     "--ssl-certfile",
    #     type=str,
    #     default=None,
    #     help="SSL certificate file",

    # )
    # group.add_argument(
    #     "--ssl-version",
    #     type=int,
    #     default=SSL_PROTOCOL_VERSION,
    #     help="SSL version to use (see stdlib ssl module's)",

    # )
    # group.add_argument(
    #     "--ssl-cert-reqs",
    #     type=int,
    #     default=ssl.CERT_NONE,
    #     help="Whether client certificate is required (see stdlib ssl module's)",

    # )
    # group.add_argument(
    #     "--ssl-ca-certs",
    #     type=str,
    #     default=None,
    #     help="CA certificates file",

    # )
    # group.add_argument(
    #     "--ssl-ciphers",
    #     type=str,
    #     default="TLSv1",
    #     help="Ciphers to use (see stdlib ssl module's)",

    # )
    # group.add_argument(
    #     "--header",
    #     "headers",
    #     multiple=True,
    #     help="Specify custom default HTTP response headers as a Name:Value pair",
    # )
    # group.add_argument(
    #     "--app-dir",
    #     "app_dir",
    #     default=".",

    #     help="Look for APP in the specified directory, by adding this to the PYTHONPATH."
    #     " Defaults to the current working directory.",
    # )


@Configuration.add("gunicorn")
def add_configuration_file(parser: "AnyBlokArgumentGroup") -> None:
    parser.add_argument(
        "--anyblok-configfile",
        dest="configfile",
        default=environ.get("ANYBLOK_CONFIG_FILE"),
        help="Relative path of the AnyBlok config file",
    )
    parser.add_argument(
        "--without-auto-migration", dest="withoutautomigration", action="store_true"
    )


@Configuration.add("plugins", must_be_loaded_by_unittest=True)
def update_plugins(group: "AnyBlokArgumentGroup") -> None:
    group.add_argument(
        "--get-db-name-plugin",
        dest="get_db_name",
        type=AnyBlokPlugin,
        default="anyblok_fastapi.config:get_db_name",
        help="get_db_name function to use in order to properly "
        "set registry object "
        "on asgi request.state.anyblok_registry",
    )
    group.set_defaults(
        Registry="anyblok_fastapi.fastapi:FastAPIRegistry",
    )
