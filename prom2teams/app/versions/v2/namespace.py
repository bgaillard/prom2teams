import os

from flask import request, current_app as app
from flask_restplus import Resource

from prom2teams.app.sender import AlertSender
from prom2teams.prometheus.message_schema import MessageSchema
from .model import *
from marshmallow import EXCLUDE
ns = api_v2.namespace(name='', description='Version 2 connections')


@ns.route('/<string:connector>')
@api_v2.doc(params={'connector': 'Name of connector to use'},
            responses={201: 'OK'})
class AlertReceiver(Resource):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        print(f"AlertReceiver - __init__ config={app.config}")

        self.schema = MessageSchema(exclude_fields=app.config['LABELS_EXCLUDED'],
                                    exclude_annotations=app.config['ANNOTATIONS_EXCLUDED'])
        self.sender = AlertSender(template_path=app.config.get('TEMPLATE_PATH'),
                                  group_alerts_by=app.config['GROUP_ALERTS_BY'],
                                  teams_client_config=app.config.get('TEAMS_CLIENT_CONFIG'))

    @api_v2.expect(message)
    def post(self, connector):

        print(f"AlertReceiver - post - Connector - {connector}")
        print(f"AlertReceiver - post - Request - METHOD: {request.method}")
        print(f"AlertReceiver - post - Request - HEADERS: {request.headers}")
        print(f"AlertReceiver - post - Request - DATA: {request.data}")

        if connector not in app.config['MICROSOFT_TEAMS']:
            print(f"AlertReceiver - post - Connector {connector} not found in config!")
        else:
            print(f"AlertReceiver - post - Connector {connector} found in config!")

        if os.environ.get('DISABLE_SCHEMA', "false") == "true":
            print("AlertReceiver - post - Schema parsing disabled, not sending to Teams")
            return 'OK', 201

        alerts = self.schema.load(request.get_json())

        if os.environ.get('DISABLE_ALERTS', "false") == "true":
            print("AlertReceiver - post - Alerts disabled, not sending to Teams")
            return 'OK', 201

        self.sender.send_alerts(alerts, app.config['MICROSOFT_TEAMS'][connector])

        return 'OK', 201
