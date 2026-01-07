import textwrap
from pyatv.support.plist import decode_plist_body
from pyatv.support.hap_tlv8 import decode_tlv_body
from pyatv.support.http import HttpRequest, HttpResponse
from typing import Dict, Any, Mapping
import logging

NETWORK = logging.DEBUG + 1

def network(self, msg, *args, **kwargs):
    """
    Log 'msg % args' with severity 'NETWORK'.

    To pass exception information, use the keyword argument exc_info with
    a true value, e.g.

    logger.network("Houston, we have a %s", "thorny problem", exc_info=True)
    """
    if self.isEnabledFor(NETWORK):
        self._log(NETWORK, msg, args, **kwargs)

logging.addLevelName(NETWORK, 'NETWORK')
logging.Logger.network = network
logging.Logger.NETWORK = NETWORK

def decode_body(type, body) -> Any: 

    if type == "application/x-apple-binary-plist":
        return decode_plist_body(body)
    elif type == "application/octet-stream":
        return decode_tlv_body(body)            
    else:
        try:
            return decode_plist_body(body)
        except:
            try:
                return decode_tlv_body(body)
            except:
                return None

interesting_keys = [] # ['Content-Location', 'params', 'streams', 'qualifier', 'timing-port', 'timingPort', 'type', 'value']

def interesting_plist_fields(plist:Dict) -> str:
    if not isinstance(plist, Dict):
        return '' 
    
    interesting = []
    other = []
    for key in plist:
        value = plist[key]
        match value:
            case str():
                info = 'str(' + str(len(value)) + ')'
            case _:
                info = str(type(value).__name__)

        if key in interesting_keys:
            if key == 'params':
                interesting.append(key + "=" + str(decode_plist_body(plist[key]['data'])))
            else:
                interesting.append(key + "=" + str(plist[key]))
        else:
            other.append(str(key) + "=" + info)

    return ", ".join(interesting) # + other)

full_log_paths = []
show_all_values = True

def _format_object(obj, keyNames=None, padding="", first=True) -> str:
    result = ""
    indent = padding if first else padding + "  "
    if isinstance(obj, dict) or isinstance(obj, Mapping):
        result += "" if first else "\n"
        for key in obj:
            keyName = keyNames(key).name if (keyNames and key in keyNames.__members__.values()) else str(key)
            result += indent + keyName + ": " + _format_object(obj[key], keyNames, indent, False)
    else:
        value = str(obj)
        if isinstance(obj, bytes):
            value = decode_body(None, obj)
            if value:
                result += _format_object(value, keyNames, indent, False)
            else:
                result +=  str(obj) + "\n"
        else:
            result +=  value + "\n"

    return result


def log_request(logger, request: HttpRequest, message_prefix="", x:int=-1) -> None:
    log_request2(logger, request.method, request.path, request.headers, request.body, message_prefix, x)

def log_request2(logger, method, path, headers, body, message_prefix="", x:int=-1) -> None:
    """Log an AirPlay request with optional binary plist body."""

    log_http(logger, path, headers, body, message_prefix + f"> {method} {path}", x)

def log_response(logger, response: HttpResponse, message_prefix="", x:int=-1, req_path="") -> None:
    """Log an AirPlay response with optional binary plist body."""

    log_http(logger, req_path, response.headers, response.body, message_prefix + f"< {req_path} {response.code}", x)

def log_http(logger, path, headers, body, message_prefix, x) -> None: 
    payload = None
    headers = headers if headers else {}
    type = None
    content_length = len(body) if body else 0

    if x != 0:
        type = headers.get("Content-Type") if headers else None
        if type == "application/octet-stream":
            payload = decode_tlv_body(body)
        elif type == "application/x-apple-binary-plist":
            payload = decode_plist_body(body)
        else:
            try:
                payload = decode_plist_body(body)
                type = "application/x-apple-binary-plist"
            except: 
                try: 
                    payload = decode_tlv_body(body)
                    type = "application/octet-stream"
                except:
                    payload = None

        interesting = interesting_plist_fields(payload) if payload else None

    if interesting:
        log = "%s %s bytes (%s) %s" % (message_prefix, content_length, headers.get("Content-Type"), interesting)
    else:
        log = "%s %s bytes (%s)" % (message_prefix, content_length, headers.get("Content-Type"))

    if x >= 0:
        log = log[:x]

    logger(log)

    if show_all_values or (path in full_log_paths):
        headerValues = _format_object(headers)
        headerValues = textwrap.indent(headerValues, "  ")
        print(f"\n{headerValues}")

        keyValues = _format_object(payload if payload else body, TlvValue)
        keyValues = textwrap.indent(keyValues, "  ")
        print(f"{keyValues}\n")
    