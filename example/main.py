from cscapi.client import CAPIClient
from cscapi.sql_storage import SQLStorage
from cscapi.utils import create_signal, generate_machine_id_from_key

client = CAPIClient(SQLStorage())

signals = [
    create_signal(
        ip="1.2.3.4",
        scenario="crowdsecurity/ssh-bf",
        created_at="2023-11-17",
        machine_id=generate_machine_id_from_key("1.2.3.6"),
    )
]

client.add_signals(signals)
client.send_signals()
