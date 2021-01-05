# Integration tests

The goal of this suite of "functional" or "end-to-end" tests is to simulate the user experience in an environment that resembles production as closely as possible.  Unit tests cover the individual details of each view whereas the goal of these tests to run full scripts covering key workflows.

Due to the multiple server nature of the production environment, and its replication using multiple containers, we cannot override settings within tests as is usually possible.  The alternative is to update fixtures based on values the test_settings.py.  For example, the admin fixture can be updated from settings.MANAGERS:

```
admin.username = settings.MANAGERS[0][0]
admin.email = settings.MANAGERS[0][1]
admin.save()
```

These tests are intended to run with docker without invalidating the standalone single-process test runner (assuming selenium and webdrivers are locally available).


## TODO

- live_app celery interface is currently broken as celery uses test db not live db.
