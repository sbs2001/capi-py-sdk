import secrets
from typing import List, Dict
from collections import defaultdict
from  dataclasses import asdict

import jwt
import requests
import time
from more_itertools import batched


from cscapi.storage import StorageInterface, SignalModel, ReceivedDecision, MachineModel

CAPI_BASE_URL = "https://api.crowdsec.net/v2"
CAPI_WATCHER_REGISTER_URL = f"{CAPI_BASE_URL}/watchers"
CAPI_WATCHER_LOGIN_URL = f"{CAPI_BASE_URL}/watchers/login"
CAPI_ENROLL_URL = f"{CAPI_BASE_URL}/watchers/enroll"
CAPI_SIGNALS_URL = f"{CAPI_BASE_URL}/signals"
CAPI_DECISIONS_URL = f"{CAPI_BASE_URL}/decisions/stream"


def machine_token_is_valid(token:str)->bool:
    payload = jwt.decode(token, options={"verify_signature": False})
    return payload["exp"] < time.time()

class CAPIClient:
    def __init__(self, storage:StorageInterface):
        self.storage = storage
        self.http_client = requests.Session()
        self.http_client.hooks = {
            'response': lambda r, *args, **kwargs: r.raise_for_status()
        }

    def add_signals(self, signals: List[SignalModel]):
        for signal in signals:
            self.storage.update_or_create_signal(signal)
    
    def send_signals(self, prune_after_send:bool=False):
        unsent_signals = filter(lambda signal: not signal.sent, self.storage.get_all_signals())
        signals_by_machineid: Dict[SignalModel, str] = defaultdict(list)
        for signal in unsent_signals:
            signals_by_machineid[signal.machine_id].append(signal)

        machines_to_register = []
        machines_to_login = []
        machines_by_id: Dict[str, MachineModel] = {}

        for machine_id, signals in signals_by_machineid.items():
            machine = self.storage.get_machine_by_id(machine_id)
            signals_scenarios = ",".join(sorted(set([signal.scenario for signal in signals])))
            if not machine:
                machines_to_register.append(MachineModel(machine_id=machine_id, scenarios=signals_scenarios, password=secrets.token_urlsafe(22)))

            elif not machine_token_is_valid(machine.token):
                machines_to_login.append(MachineModel(machine_id=machine_id, scenarios=signals_scenarios, password=machine.password))

            else:
                machines_by_id[machine_id] = machine

        # For higher performance we can use async here. 
        updated_machines =  list(map(self._make_machine, machines_to_register))
        updated_machines =  list(map(self._refresh_machine_token, machines_to_login)).extend(updated_machines)

        machines_by_id = {machine.machine_id: machine for machine in updated_machines} | machines_by_id

        for machine_id, signals in signals_by_machineid.items():
            token = machines_by_id[machine_id].token
            self._send_signals(token, signals)
        
        if prune_after_send:
            self._prune_sent_signals()            

    def _send_signals(self, token:str, signals: SignalModel):
        for signal_batch in batched(signals, 250):
            resp = self.http_client.post(
                CAPI_SIGNALS_URL,
                json={"signals": [signal.to_dict() for signal in signal_batch]},
                headers={ "Authorization": token}
            )
            resp.raise_for_status()

    def _prune_sent_signals(self):
        signals = filter(lambda signal: signal.sent, self.storage.get_all_signals())
        self.storage.delete_signals(signals)

    def _refresh_machine_token(self, machine: MachineModel)->MachineModel:
        resp = self.http_client.post(CAPI_WATCHER_LOGIN_URL, json={
            "machine_id": machine.machine_id,
            "password": machine.password,
            "scenarios": machine.scenarios
        })
        new_machine = MachineModel(**asdict(machine) , token=resp.json()["token"])
        self.storage.update_or_create_machine(new_machine)
        return new_machine

    def _register_machine(self, machine: MachineModel)-> MachineModel:
        resp = self.http_client.post(CAPI_WATCHER_REGISTER_URL, json={
            "machine_id": machine.machine_id,
            "password": machine.password,
        })
        self.storage.update_or_create_machine(machine)
        return machine

    def _make_machine(self, machine: MachineModel):
        machine = self._register_machine(machine)
        return self._refresh_machine_token(machine)
        
    def get_decisions(self, main_machine_id: str, scenarios: List[str])->List[ReceivedDecision]:
        machine = self.storage.get_machine_by_id(main_machine_id)
        if not machine:
            machine = self._make_machine(MachineModel(machine_id=main_machine_id, password=secrets.token_urlsafe(22), scenarios=scenarios)) 

        elif not machine_token_is_valid(machine.token):
            machine = self._refresh_machine_token(MachineModel(machine_id=main_machine_id, password=machine.password, scenarios=scenarios))

        resp = self.http_client.get(CAPI_DECISIONS_URL, 
                                    headers={"Authorization": machine.token})

        return resp.json()

    
    def enroll_machines(self, machine_ids:List[str], name:str,  attachment_key:str, tags: List[str]):
        for machine_id in machine_ids:        
            machine = self.storage.get_machine_by_ids(machine_id)
            if not machine:
                machine = self._make_machine(MachineModel(machine_id=machine_id, password=secrets.token_urlsafe(22), scenarios=""))
            elif not machine_token_is_valid(machine.token):
                machine = self._refresh_machine_token(MachineModel(machine_id=machine_id, password=machine.password, scenarios=""))                             
            
            self.http_client.post(CAPI_ENROLL_URL, json={
                "name": name,
                "overwrite": True,
                "attachment_key": attachment_key,
                "tags": tags 
            })
