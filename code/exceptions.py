"""Askme Exception handling

When handling exception we always return a JSON object with 'status', 'message',
'stack' and 'details' properties. The stack property is a list and the details
property is a dictionary with any content, they are both there for development
and debugging purposes and should not be exposed to the regular AskMe user.

"""

import sys
import traceback

from fastapi import Request
from fastapi.responses import JSONResponse
from elasticsearch import ApiError


class AskmeException(Exception):

    def __init__(self,
                 message: str,
                 status: int = 500,
                 details: dict = None):
        self.status = status
        self.message = message
        # this is where we now put details that we got from ES.mget()
        self.details = {} if details is None else details


def handle_askme_exception(request: Request, exc: AskmeException):
    details = {
        "error_class": str(exc.__class__),
        "elastic_details": exc.details }
    return JSONResponse(
        status_code=exc.status,
        content={
            "status": exc.status,
            "message": f"AskMe Exception: {exc.message}",
            "stack": traceback.format_exception(*sys.exc_info()),
            "details": details})

def handle_elastic_exception(request: Request, exc: ApiError):
    details = {
        "status_code": exc.status_code,
        "error_class": str(exc.__class__),
        "message": exc.message,
        "body": exc.body }
    status =  details['status_code'] if 'status_code' in details else 400
    return JSONResponse(
        status_code=status,
        content={
            "status": status,
            "message": f"Elastic exception: {exc.message}",
            "stack": traceback.format_exception(*sys.exc_info()),
            "details": details})

def handle_python_exception(request: Request, exc: Exception):
    stack = traceback.format_exception(*sys.exc_info())
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "message": f"Python exception: {str(exc)}.",
            "stack": stack,
            "details": {
                "error_class": str(exc.__class__),
                "message": stack[-1] }})
