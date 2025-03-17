import argparse
from multiprocessing import Barrier, cpu_count
from pathlib import Path


from bench_utils import Benchmark, ContractWorker, MoneyWorker


def entrypoint():
    global barrier

    global_parser = argparse.ArgumentParser(prog="benchmark")
    global_parser.add_argument(
        "--hosts", help="Comma separated list of host urls", required=True, type=str
    )
    global_parser.add_argument(
        "--rps", help="Requests per second", required=True, type=int
    )
    global_parser.add_argument(
        "--duration", help="Duration of the benchmark", required=True, type=int
    )
    global_parser.add_argument(
        "--output", help="Log the transactions", required=True, type=Path
    )
    global_parser.add_argument(
        "--processes",
        help="Number of processes",
        required=False,
        type=int,
        default=cpu_count(),
    )
    global_parser.add_argument(
        "--timeout",
        help="Timeout for the transactions",
        required=False,
        type=int,
        default=30,
    )
    subparser = global_parser.add_subparsers(title="type", dest="type")
    contract_parser = subparser.add_parser("contract")
    contract_parser.add_argument(
        "--address", help="Address of the deployed contract", type=str
    )
    contract_parser.add_argument("--abi", help="ABI of the deployed contract", type=str)

    args = global_parser.parse_args()
    if args.type == "contract":
        worker = ContractWorker
        worker_args = {"contract_address": args.address, "contract_abi": args.abi}
    else:
        worker = MoneyWorker
        worker_args = None
    hosts = args.hosts.split(",")
    rps = args.rps
    duration = args.duration
    output = args.output
    processes = args.processes
    barrier = Barrier(processes)
    timeout = args.timeout

    Benchmark(
        hosts, rps, duration, output, processes, timeout, worker, worker_args # type: ignore
    ).start()


if __name__ == "__main__":
    entrypoint()
