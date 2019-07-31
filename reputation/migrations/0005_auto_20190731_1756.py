# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-07-31 17:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("reputation", "0004_auto_20190731_1723")]

    operations = [
        migrations.AlterField(
            model_name="usescriterion",
            name="reputation_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="criteria",
                to="reputation.ReputationType",
            ),
        )
    ]
