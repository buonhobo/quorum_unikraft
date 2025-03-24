from pathlib import Path
from typing import override

from provinew.quorum.node.NodeData import ConnData
from provinew.virtualization.Virtualizer import (
    VirtData,
    HostNetVirtualizer,
    Virtualizer,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from provinew.quorum.node.Node import Node


class Podman(HostNetVirtualizer):
    class PodmanData(VirtData):
        @override
        def __init__(self, virtualizer: "Virtualizer", cpus: int, image: str) -> None:
            super().__init__(virtualizer)
            self.cpus = cpus
            self.image = image

    @override
    def initialize(self, jsondata: dict):
        self.image = jsondata["image"]

    @override
    def handle_node(self, node: "Node", jsondata: dict) -> VirtData:
        return Podman.PodmanData(
            self, jsondata.get("cpus", 1), jsondata.get("image", self.image)
        )

    @override
    def get_stop_command(self):
        return "podman rm --force --filter label=quorum=true"

    @override
    async def pre_start(self, node: "Node"):
        pass

    @override
    def get_start_command(self, node: "Node", options: str):
        assert node.data is not None
        assert isinstance(node.virt_data, Podman.PodmanData)
        command = (
            f"podman run -d --rm --replace "
            f"--name {node.name} "
            f"--label quorum=true "
            f"--cpus {node.virt_data.cpus} "
            f"--net host "
            f"-v {node.data.dir}:/node:Z "
            f"{node.virt_data.image} "
            f"{options}"
        )
        return command

    @override
    def get_conn_data(self, node: "Node") -> "ConnData":
        return ConnData(
            self.host_ip,
            port=30300 + node.id + 1,
            ws_port=32000 + node.id + 1,
            raft_port=53000 + node.id + 1,
        )


    @override
    def get_mapped_dir(self, node: "Node") -> Path:
        return Path("/node")
