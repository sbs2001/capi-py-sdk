from abc import ABC, abstractmethod
from typing import List, Optional

from dataclasses import dataclass

@dataclass
class ReceivedDecision:
    Duration: Optional[str]
    Value: Optional[str]
    Scenario: Optional[str]
    Scope: Optional[str]

@dataclass
class MachineModel:
    machine_id: Optional[str] = None
    token: Optional[str] = None
    password: Optional[str] = None
    scenarios: Optional[str] = None

@dataclass
class DecisionModel:
    duration: Optional[str] = None
    uuid: Optional[str] = None
    scenario: Optional[str] = None
    origin: Optional[str] = None
    scope: Optional[str] = None
    simulated: Optional[bool] = None
    until: Optional[str] = None
    id: Optional[int] = None
    type: Optional[str] = None
    value: Optional[str] = None

@dataclass
class SourceModel:
    ip: Optional[str] = None
    range: Optional[str] = None
    scope: Optional[str] = None
    latitude: Optional[float] = None
    as_number: Optional[str] = None
    cn: Optional[str] = None
    value: Optional[str] = None
    as_name: Optional[str] = None
    longitude: Optional[float] = None

    def __post_init__(self):
        if self.ip:
            self.scope = "ip"
        elif self.range:
            self.scope = "range"

@dataclass
class ContextModel:
    value: Optional[str]
    key: Optional[str]

@dataclass
class SignalModel:
    created_at: Optional[str]
    machine_id: Optional[str]
    source: Optional[SourceModel]# foreign key
    scenario_version: Optional[str]
    message: Optional[str]
    uuid: Optional[str]
    start_at: Optional[str]
    scenario_trust: Optional[str]
    scenario_hash: Optional[str]
    scenario: Optional[str]
    context: Optional[List[ContextModel] ] # foreign key
    decisions: Optional[List[DecisionModel]]# foreign key
    stop_at: Optional[str]
    sent: Optional[bool] = False
    id: Optional[int] = None

    def __post_init__(self):
        if self.source:
            self.source = SourceModel(**self.source)
        if self.context:
            self.context = [ContextModel(**context) for context in self.context]
        if self.decisions:
            self.decisions = [DecisionModel(**decision) for decision in self.decisions]

class StorageInterface(ABC):
    @abstractmethod
    def get_all_signals(self) -> List[SignalModel]:
        raise NotImplementedError
    
    @abstractmethod
    def get_machine_by_id(self, machine_id:str) -> MachineModel:
        raise NotImplementedError
    
    @abstractmethod
    def update_or_create_machine(self, machine:MachineModel) -> bool:
        # returns true if created new row else false 
        raise NotImplementedError

    @abstractmethod
    def update_or_create_signal(self, signal:SignalModel) -> bool:
        # returns true if created new row else false
        raise NotImplementedError

    @abstractmethod
    def delete_signals(self, signals:List[SignalModel]):
        raise NotImplementedError

    @abstractmethod
    def delete_machines(self, machines: List[MachineModel]):
        raise NotImplementedError