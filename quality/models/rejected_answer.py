# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import models

from .quality import Quality
from ..utils import LazyEncoder


class RejectedAnswer(models.Model):
    quality = models.ForeignKey(Quality)
    rationale = models.TextField()
    reasons = models.TextField(
        help_text="json string containing info about criterions used to "
        "reject the rationale"
    )

    def __iter__(self):
        return {
            "rationale": self.rationale,
            "reasons": json.loads(self.reasons),
        }.iteritems()

    @staticmethod
    def add(quality, rationale, reasons):
        """
        Adds the bad rationale and the reasons for its rejection, formatting
        them. The reasons correspond to the version and rules for each
        criterion and the scored quality and threshold

        Parameters
        ----------
        rationale : str
            Rationale given
        reasons : Dict[str, Dict[str, Any]]
            Reasons in the format:
                {
                    name:
                        version: int
                        rules: {
                            name: value
                        }
                        threshold: float
                        quality: float
                }

        Returns
        -------
        BadAnswer
            Created instance
        """
        return RejectedAnswer.objects.create(
            quality=quality,
            rationale=rationale,
            reasons=json.dumps(reasons, cls=LazyEncoder),
        )
