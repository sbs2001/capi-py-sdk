from typing import List
from dataclasses import asdict

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, Time, update, select, delete
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

from cscapi import storage

Base = declarative_base()

class MachineDBModel(Base):
    __tablename__ = 'machine_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    machine_id = Column(String)
    token = Column(String)
    password = Column(String)
    scenarios = Column(String)

class DecisionDBModel(Base):
    __tablename__ = 'decision_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    duration = Column(String)
    uuid = Column(String)
    scenario = Column(String)
    origin = Column(String)
    scope = Column(String)
    simulated = Column(Boolean)
    until = Column(String)
    type = Column(String)
    value = Column(String)

class SourceDBModel(Base):
    __tablename__ = 'source_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    scope = Column(String)
    ip = Column(String)
    latitude = Column(Float)
    as_number = Column(String)
    range = Column(String)
    cn = Column(String)
    value = Column(String)
    as_name = Column(String)
    longitude = Column(Float)

class ContextDBModel(Base):
    __tablename__ = 'context_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    value = Column(String)
    key = Column(String)

class SignalDBModel(Base):
    __tablename__ = 'signal_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(String)
    machine_id = Column(String)
    source_id = Column(Integer, ForeignKey('source_models.id'), nullable=True)
    source = relationship("SourceDBModel")
    scenario_version = Column(String, nullable=True)
    message = Column(String, nullable=True)
    uuid = Column(String)
    start_at = Column(String, nullable=True)
    scenario_trust = Column(String, nullable=True)
    scenario_hash = Column(String, nullable=True)
    scenario = Column(String, nullable=True)
    stop_at = Column(String, nullable=True)
    sent = Column(Boolean, default=False)

    context_id = Column(Integer, ForeignKey('context_models.id'), nullable=True)
    decisions_id = Column(Integer, ForeignKey('decision_models.id'), nullable=True)

    context = relationship("ContextDBModel", backref="signal_models")
    decisions = relationship("DecisionDBModel", backref="signal_models")


class SQLStorage(storage.StorageInterface):
    def __init__(self, connection_string="sqlite:///your_database.db") -> None:
        engine = create_engine(connection_string, echo=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def get_all_signals(self) -> List[storage.SignalModel]:
        result = self.session.query(SignalDBModel).all()
        return result
        
    def get_machine_by_id(self, machine_id:str) -> storage.MachineModel:
        exisiting = self.session.query(MachineDBModel).filter(MachineDBModel.machine_id == machine_id).first()
        if not exisiting:
            return 
        return MachineDBModel(machine_id=exisiting.machine_id, token=exisiting.token, password=exisiting.password, scenarios=exisiting.scenarios)
    
    def update_or_create_machine(self, machine: storage.MachineModel) -> bool:
        exisiting = self.session.query(MachineDBModel).filter(MachineDBModel.machine_id == machine.machine_id).all()
        if not exisiting:
            self.session.add(MachineDBModel(**asdict(machine)))
            self.session.commit()
            return True

        update_stmt = update(MachineDBModel).where(
            MachineDBModel.machine_id == machine.machine_id
        ).values(**asdict(machine))
        self.session.execute(update_stmt)
        return False


    def update_or_create_signal(self, signal: storage.SignalModel) -> bool:
        to_insert = SignalDBModel(**{k:v for k,v in asdict(signal).items() if k != "source" and k != "context" and k != "decisions"})
        # to_insert.decisions = [DecisionDBModel(**asdict(decision)) for decision in signal.decisions]
        # to_insert.context = [ContextDBModel(**asdict(context)) for context in signal.context]

        if not signal.id:
            self.session.add(to_insert)
            self.session.commit()
            return True
        
        exisiting = self.session.query(SignalDBModel).filter(SignalDBModel.id == signal.id).all()
        if not exisiting:
            self.session.add(to_insert)
            self.session.commit()
            return True

        update_stmt = update(SignalDBModel).where(
            SignalDBModel.id == signal.id
        ).values(**asdict(to_insert))
        self.session.execute(update_stmt)


        return False

    def delete_signals(self, signals: List[storage.SignalModel]):
        stmt = delete(SignalDBModel).where(
            SignalDBModel.id in ([signal.id for signal in signals])
        )
        self.session.execute(stmt)

    def delete_machines(self, machines: List[storage.MachineModel]):
        stmt = delete(MachineDBModel).where(
            MachineDBModel.machine_id in ([machine.machine_id for machine in machines])
        )
        self.session.execute(stmt)
