# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-31 17:23
from __future__ import unicode_literals

from django.db import migrations

import dalite.models.custom_fields


class Migration(migrations.Migration):

    dependencies = [("reputation", "0003_auto_20190522_1817")]

    operations = [
        migrations.RemoveField(model_name="nanswerscriterion", name="ceiling"),
        migrations.RemoveField(model_name="nanswerscriterion", name="floor"),
        migrations.RemoveField(
            model_name="nanswerscriterion", name="growth_rate"
        ),
        migrations.RemoveField(
            model_name="nquestionscriterion", name="ceiling"
        ),
        migrations.RemoveField(model_name="nquestionscriterion", name="floor"),
        migrations.RemoveField(
            model_name="nquestionscriterion", name="growth_rate"
        ),
        migrations.RemoveField(model_name="usescriterion", name="weight"),
        migrations.AddField(
            model_name="nanswerscriterion",
            name="points_per_threshold",
            field=dalite.models.custom_fields.CommaSepField(
                default=1,
                help_text="Number of reputation points for each criterion "
                "point up to the next threadhold, split by commas. This list "
                "should have the same length or have one more element than "
                "Thresholds.",
                verbose_name="Points per threshold",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="nanswerscriterion",
            name="thresholds",
            field=dalite.models.custom_fields.CommaSepField(
                default="",
                help_text="Thresholds for number of point change. If empty, "
                "all criterion points will give the same number of points. If "
                "one less than `Points per threshold`, the last point number "
                "goes to infinity. If it's the same length, the last number "
                "indicates the threshold after which points aren't gained.",
                verbose_name="Thresholds",
            ),
        ),
        migrations.AddField(
            model_name="nquestionscriterion",
            name="points_per_threshold",
            field=dalite.models.custom_fields.CommaSepField(
                default=1,
                help_text="Number of reputation points for each criterion "
                "point up to the next threadhold, split by commas. This list "
                "should have the same length or have one more element than "
                "Thresholds.",
                verbose_name="Points per threshold",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="nquestionscriterion",
            name="thresholds",
            field=dalite.models.custom_fields.CommaSepField(
                default="",
                help_text="Thresholds for number of point change. If empty, "
                "all criterion points will give the same number of points. If "
                "one less than `Points per threshold`, the last point number "
                "goes to infinity. If it's the same length, the last number "
                "indicates the threshold after which points aren't gained.",
                verbose_name="Thresholds",
            ),
        ),
    ]
