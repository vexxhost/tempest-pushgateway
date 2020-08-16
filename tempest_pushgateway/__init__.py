# Copyright 2020 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import io
import subprocess
import sys
import tempfile
import testtools

import prometheus_client
import subunit


class PrometheusResult(testtools.TestResult):

    def __init__(self):
        super().__init__()

        self._registry = prometheus_client.CollectorRegistry()
        self._last_run_result = prometheus_client.Enum(
            'tempest_last_run_result',
            'Result of the last Tempest run',
            labelnames=['instance'],
            states=[
                'success',
                'failure',
                'error',
                'skip',
                'expectedfailure',
                'unexpectedsucces',
            ],
            registry=self._registry
        )
        self._last_run_unixtime = prometheus_client.Gauge(
            'tempest_last_run_unixtime',
            'Time of the last Tempest test run',
            labelnames=['instance'],
            registry=self._registry
        )
        self._last_run_time = prometheus_client.Gauge(
            'tempest_last_run_time',
            'Run-time for the last Tempest run',
            labelnames=['instance'],
            registry=self._registry
        )

    def stopTest(self, test):
        start_timestamp = test._timestamps[0].timestamp()
        end_timestamp = test._timestamps[1].timestamp()
        outcome = test._outcome.replace('add', '').lower()

        if outcome != 'success':
            print(test.__dict__)

        labels = {
            'instance': test.id(),
        }

        self._last_run_unixtime.labels(**labels).set(end_timestamp)
        self._last_run_time.labels(**labels).set(
            end_timestamp - start_timestamp
        )
        self._last_run_result.labels(**labels).state(outcome)

    def stopTestRun(self):
        super().stopTestRun()
        prometheus_client.push_to_gateway(os.getenv('TEMPEST_PROMETHEUS'),
                                          job='tempest',
                                          registry=self._registry)


def main():
    tests = "\n".join(sys.argv[1:])

    tempest_conf = tempfile.NamedTemporaryFile(mode='w+')
    accounts_file = tempfile.NamedTemporaryFile(mode='w+')

    result = subprocess.call([
        'discover-tempest-config', '--debug', '--non-admin',
        '--convert-to-raw',
        '--create-accounts-file', accounts_file.name,
        '--out', tempest_conf.name
    ])
    if result != 0:
        return

    with tempfile.NamedTemporaryFile(mode='w') as whitelist_file:
        whitelist_file.write(tests)
        whitelist_file.flush()

        result = subprocess.run([
            'tempest', 'run', '--debug', '--subunit', '--concurrency=1',
            '--config-file', tempest_conf.name,
            '--whitelist-file', whitelist_file.name
        ], capture_output=True)

        stream = io.BytesIO(result.stdout)

        suite = subunit.ByteStreamToStreamResult(stream)
        result = testtools.StreamToExtendedDecorator(PrometheusResult())
        result.startTestRun()
        try:
            suite.run(result)
        finally:
            result.stopTestRun()
