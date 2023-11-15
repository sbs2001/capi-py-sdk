"""

Send Signals
1. Send signals from fresh state. Assert machine creation, token creation, correct scenarios etc.
2. Send signals except the machines are already in the DB. Assert no new registrations 
3. Send signals except the machines are already in the DB but tokens are stale.
4. Send signals except some machines are fresh, some have stale token, some are good to send. 

Get decisions
1. Get decisions from fresh machine
2. Get decisions from alright machine
3. Get decisions from stale token machine

Enroll

1. Enroll from fresh machine
2. Enroll from alright machine
3. Enroll from stale token machine

"""

import os
import time
from unittest import TestCase

from cscapi.client import (
    CAPIClient,
    CAPI_WATCHER_REGISTER_URL,
    CAPI_WATCHER_LOGIN_URL,
    CAPI_SIGNALS_URL,
    CAPI_DECISIONS_URL,
)
from cscapi.storage import SignalModel
from cscapi.sql_storage import SQLStorage
from pytest_httpx import HTTPXMock


mock_signals = [SignalModel(**z) for z in [
    {

        "decisions": [
            {
                "duration": "59m49.264032632s",
                "id": 1,
                "origin": "crowdsec",
                "scenario": "crowdsecurity/ssh-bf",
                "scope": "Ip",
                "simulated": False,
                "type": "ban",
                "value": "1.1.1.172",
            }
        ],
        "context": [ 
                    {"key": "target_user", "value": "netflix"},
                    {"key": "service", "value": "ssh"},
                    {"key": "target_user", "value": "netflix"},
                    {"key": "service", "value": "ssh"},
        ],
        "uuid": 1,
        "machine_id": "test",
        "message": "Ip 1.1.1.172 performed 'crowdsecurity/ssh-bf' (6 events over 2.920062ms) at 2020-11-28 10:20:46.845619968 +0100 CET m=+5.903899761",
        "scenario": "crowdsecurity/ssh-bf",
        "scenario_hash": "4441dcff07020f6690d998b7101e642359ba405c2abb83565bbbdcee36de280f",
        "scenario_version": "0.1",
        "scenario_trust": "trusted",
        "source": {
            "as_name": "Cloudflare Inc",
            "cn": "AU",
            "ip": "1.1.1.172",
            "latitude": -37.7,
            "longitude": 145.1833,
            "range": "1.1.1.0/24",
            "scope": "Ip",
            "value": "1.1.1.172",
        },
        "start_at": "2020-11-28 10:20:46.842701127 +0100 +0100",
        "stop_at": "2020-11-28 10:20:46.845621385 +0100 +0100",
        "created_at": "2020-11-28T10:20:47+01:00",
    }
]]


class TestSendSignals:
    # def setUp(self) -> None:
    #     self.db_name = f"{time.time()}.db"
    #     self.storage = SQLStorage(f"sqlite:///{self.db_name}")
    #     self.client = CAPIClient(self.storage)

    # def tearDown(self) -> None:
    #     self.storage.session.close_all()
    #     try:
    #         os.remove(self.db_name)
    #     except:
    #         pass

    def test_fresh_send_signals(self, httpx_mock: HTTPXMock):

        self.db_name = f"{time.time()}.db"
        self.storage = SQLStorage(f"sqlite:///{self.db_name}")
        self.client = CAPIClient(self.storage)

        assert len(self.storage.get_all_signals()) ==  0

        httpx_mock.add_response(method="POST", url=CAPI_WATCHER_LOGIN_URL, json={"token": "abcd"})
        httpx_mock.add_response(method="POST", url=CAPI_WATCHER_REGISTER_URL, json={"message": "OK"})
        httpx_mock.add_response(method="POST", url=CAPI_SIGNALS_URL, text="OK")

        self.client.add_signals(mock_signals)
        assert len(self.storage.get_all_signals()) ==  1

        assert self.storage.get_machine_by_id("test") is None

        self.client.send_signals()

        machine = self.storage.get_machine_by_id("test")
        assert machine is not None


