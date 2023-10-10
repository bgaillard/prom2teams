import logging.config
import os
import psutil

from flask import Flask, Blueprint, send_from_directory
from marshmallow.exceptions import ValidationError

from prom2teams.app.configuration import config_app, setup_logging
from .exceptions import MicrosoftTeamsRequestException
from .versions.v1 import api_v1
from .versions.v1.namespace import ns as ns_v1
from .versions.v2 import api_v2
from .versions.v2.namespace import ns as ns_v2

log = logging.getLogger('prom2teams_app')

app = Flask(__name__)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/alive')
def alive():

    memory_usage = psutil.virtual_memory()
    log.debug(f"api - /alive - Memory Usage: {memory_usage.percent}%")

    return "YES", 200


@app.route('/ready')
def ready():

    memory_usage = psutil.virtual_memory()
    log.debug(f"api - /ready - Memory Usage: {memory_usage.percent}%")

    return ("YES", 200) if app.config['FINISH_INIT'] else ("NO", 503)


def error_handler(e):
    msg = 'An unhandled exception occurred. {}'.format(e)
    log.exception(msg)
    if isinstance(e, MicrosoftTeamsRequestException):
        return str(e), e.code
    if isinstance(e, ValidationError):
        return str(e), 400

    memory_usage = psutil.virtual_memory()
    log.debug(f"error_handler - Memory Usage: {memory_usage.percent}%")

    return str(e), 500


def register_api(application, api, namespace, blueprint):
    api.init_app(blueprint)
    api.add_namespace(namespace)
    application.register_blueprint(blueprint)


def init_app(application):
    config_app(application)
    setup_logging(application)

    blueprint_v1 = Blueprint('api_v1', __name__, url_prefix=application.config['API_V1_URL_PREFIX'])
    blueprint_v2 = Blueprint('api_v2', __name__, url_prefix=application.config['API_V2_URL_PREFIX'])
    register_api(application, api_v1, ns_v1, blueprint_v1)
    register_api(application, api_v2, ns_v2, blueprint_v2)
    application.register_error_handler(500, error_handler)
    application.config['FINISH_INIT'] = True


init_app(app)
log.info('{} started on {}:{}'.format(app.config['APP_NAME'], app.config['HOST'], app.config['PORT']))
