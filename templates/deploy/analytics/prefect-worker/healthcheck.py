#!/opt/venv/bin/python
import os
import sys

import requests

PREFECT_API_URL = os.environ["PREFECT_API_URL"]


def main(worker_name, work_pool_name):
    url = f"{PREFECT_API_URL}/work_pools/{work_pool_name}/workers/filter"
    response = requests.post(url, verify=False)
    response.raise_for_status()

    workers = response.json()
    workers = [
        worker
        for worker in workers
        if worker["name"] == worker_name and worker["status"] == "ONLINE"
    ]

    if not workers:
        sys.exit(1)

    print(workers[0])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python healthcheck.py WORKER_NAME WORK_POOL_NAME")
        sys.exit(1)

    worker_name = sys.argv[1]
    work_pool_name = sys.argv[2]
