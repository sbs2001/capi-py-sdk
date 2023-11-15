import os
from unittest import TestCase
from cscapi.sql_storage import SQLStorage, MachineDBModel
from cscapi.storage import MachineModel


import time


class TestSQLStorage(TestCase):
    def setUp(self) -> None:
        self.db_path = f"{str(int(time.time()))}.db"
        db_uri = f"sqlite:///{self.db_path}"
        self.storage: SQLStorage = SQLStorage(db_uri)

    def tearDown(self) -> None:
        try:
            os.remove(self.db_path)
        except:
            pass

    def test_create_and_retrieve_machine(self):
        m1 = MachineModel(
            machine_id="1",
            token="1",
            password="1",
            scenarios="crowdsecurity/http-probing",
        )

        # Should return true if db row is created, else return false
        self.assertTrue(self.storage.update_or_create_machine(m1))
        self.assertFalse(self.storage.update_or_create_machine(m1))

        retrieved = self.storage.get_machine_by_id("1")

        self.assertEqual(retrieved.machine_id, m1.machine_id)
        self.assertEqual(retrieved.token, m1.token)
        self.assertEqual(retrieved.password, m1.password)
        self.assertEqual(retrieved.scenarios, m1.scenarios)

    def test_update_machine(self):
        m1 = MachineModel(
            machine_id="1",
            token="1",
            password="1",
            scenarios="crowdsecurity/http-probing",
        )
        self.storage.update_or_create_machine(m1)

        retrieved = self.storage.get_machine_by_id("1")

        self.assertEqual(retrieved.machine_id, m1.machine_id)
        self.assertEqual(retrieved.token, m1.token)
        self.assertEqual(retrieved.password, m1.password)
        self.assertEqual(retrieved.scenarios, m1.scenarios)

        m2 = MachineModel(
            machine_id="1", token="2", password="2", scenarios="crowdsecurity/http-bf"
        )
        self.storage.update_or_create_machine(m2)
        self.assertEqual(1, self.storage.session.query(MachineDBModel).count())

        retrieved = self.storage.get_machine_by_id("1")

        self.assertEqual(retrieved.machine_id, m2.machine_id)
        self.assertEqual(retrieved.token, m2.token)
        self.assertEqual(retrieved.password, m2.password)
        self.assertEqual(retrieved.scenarios, m2.scenarios)
