# -*- coding: utf-8 -*-
import werkzeug
import json
from odoo.http import request

def authenticate(**kw):
    if request.httprequest.authorization:
        username  =  request.httprequest.authorization.get("username")
        password = request.httprequest.authorization.get('password')
    else:
        username = ''
        password = ''
    
    capiter_config = request.env['invoice.integration.config'].sudo()
    response = capiter_config.auth_validate(username, password)
    return response

def json_response(response, status_code=None):
    mime='application/json; charset=utf-8'
    body = json.dumps(response)

    headers = [
                ('Content-Type', mime),
                ('Content-Length', len(body))
            ]
    
    if response['success'] == False and 'message' not in response:
        return werkzeug.wrappers.Response(body, status=401, headers=headers)

    return werkzeug.wrappers.Response(body, status=status_code, headers=headers)