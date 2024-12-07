import hashlib
import hmac
import json
from collections import OrderedDict
from typing import Any, Dict
from urllib.parse import urlencode
import math
import urllib.parse

from hummingbot.connector.time_synchronizer import TimeSynchronizer
from hummingbot.core.web_assistant.auth import AuthBase
from hummingbot.core.web_assistant.connections.data_types import RESTMethod, RESTRequest, WSRequest


class CoinstoreAuth(AuthBase):
    def __init__(self, api_key: str, secret_key: str, time_provider: TimeSynchronizer):
        self.api_key = api_key
        self.secret_key = secret_key
        self.time_provider = time_provider

    async def rest_authenticate(self, request: RESTRequest) -> RESTRequest:
        """
        Adds the server time and the signature to the request, required for authenticated interactions. It also adds
        the required parameter in the request header.
        :param request: the request to be configured for authenticated interaction
        """
        headers = {}

        if request.method == RESTMethod.POST:
            if request.data == None :
              request.data = {} 
              request.data = json.dumps(request.data)
            request.data = request.data.encode("utf-8")
            headers.update(self.header_for_authentication(payload=request.data))

        else:
            payload = urllib.parse.urlencode(sorted(request.params.items()))
            payload = payload.encode("utf-8")
            headers.update(self.header_for_authentication(payload=payload))

        if request.headers is not None:
            headers.update(request.headers)
        request.headers = headers

        return request

    async def ws_authenticate(self, request: WSRequest) -> WSRequest:
        """
        This method is intended to configure a websocket request to be authenticated. Coinstore does not use this
        functionality
        """
        return request  # pass-throughss

    def header_for_authentication(self, payload) -> Dict[str, str]:
        timestamp = int(self.time_provider.time() * 1e3)
        expires_key = str(math.floor(timestamp / 30000))
        expires_key = expires_key.encode("utf-8")
        key = hmac.new(self.secret_key.encode("utf8"), expires_key, hashlib.sha256).hexdigest()
        key = key.encode("utf-8")
        signature = hmac.new(key, payload, hashlib.sha256).hexdigest()

        headers = {
            'X-CS-APIKEY': self.api_key,
            'X-CS-SIGN': signature,
            'X-CS-EXPIRES': str(timestamp),
            'exch-language': 'en_US',
            'Content-Type': 'application/json',
            'Accept': '*/*',
            'Connection': 'keep-alive'
           }
        
        return headers
