# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class CriterionDoesNotExistError(Exception):
    def __init__(self, msg="", *args, **kwargs):
        if not msg:
            msg = (
                "There is no criterion corresponding to that name or version."
            )
        super(Exception, self).__init__(msg, *args, **kwargs)
