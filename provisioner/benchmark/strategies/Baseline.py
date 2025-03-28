import asyncio
from multiprocessing import Array, Lock
from typing import override

from hexbytes import HexBytes
from web3 import AsyncWeb3, WebSocketProvider
from provisioner.benchmark.workers.Worker import Worker
from provisioner.benchmark.strategies.WorkerStrategy import WorkerStrategy
from provisioner.quorum.Quorum import Quorum


class Baseline(WorkerStrategy):
    @override
    def __init__(
        self,
        jsondata: dict,
        quorum: Quorum,
    ) -> None:
        self.quorum = quorum
        self.address = AsyncWeb3().eth.account.create().address
        self.lock: Lock = Lock()  # type: ignore

    @override
    def prepare_strategy(self):
        hosts = [
            node.get_conn_data().get_ws_url() for node in self.quorum.get_targets()
        ]
        self.host_to_id = {host: i for i, host in enumerate(hosts)}
        self.nonces: Array = Array(  # type: ignore
            "i", asyncio.run(self.init_nonces(hosts)), lock=False
        )

    async def init_nonces(self, hosts: list[str]):
        nonces = []
        for host in hosts:
            async with AsyncWeb3(WebSocketProvider(host)) as connector:
                nonces.append(
                    await connector.eth.get_transaction_count(
                        (await connector.eth.accounts)[0]
                    )
                )
        return nonces

    @override
    async def prepare_worker(self, worker: Worker):
        pass

    @override
    async def send_transaction(self, connector, nonce, pid) -> HexBytes:
        with self.lock:
            id = self.host_to_id[connector.provider.endpoint_uri]  # type: ignore
            nonce = self.nonces[id]
            self.nonces[id] += 1

        return await connector.eth.send_transaction(
            {
                "nonce": nonce,
                "to": self.address,
                "value": 1,
                "from": connector.eth.default_account,
                "gas": 25_000_000,
                "gasPrice": 0,
                "chainId": 1337,
            }  # type: ignore
        )

    @override
    def get_name(self) -> str:
        return "baseline"