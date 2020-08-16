===================
Tempest Pushgateway
===================
Tempest Pushgateway is a small tool which takes a set of OpenStack credentials
using the environment variables, generates a ``tempest.conf`` configuration
file, runs the list of tests provided in the arguments and then pushes the
results to a Prometheus Pushgateway.

This tool is helpful in running full integration tests against your cloud in
a periodic manner and seeing how long they take and if they passed or failed,
it also means that you can capitalize on all of the existing set of Tempest
integration tests.

Usage
-----
You can use the Docker container which is published to ``vexxhost/tempest-pushgateway``
and provide your OpenStack creentials in the environment, alternatively you can
simply install this locally and call ``tempest-pushgateway`` directly.  The
only requirement is to set ``TEMPEST_PROMETHEUS`` environment variable to point
towards your Prometheus Pushgateway.
