from bloqade import start
from bloqade.task import HardwareBatchFuture
import pytest


@pytest.mark.vcr
def test_quera_submit():
    job_future = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "run_time", 0.1], [0, 15, 15, 0]
        )
        .assign(run_time=2.0)
        .parallelize(20)
        .quera(10, config_file="tests/data/config/submit_quera_api.json")
        .submit()
    )

    job_future.save_json("tests/data/jobs/quera_submit.json")


@pytest.mark.vcr
def test_quera_retrieve():
    job_future = HardwareBatchFuture()
    job_future.load_json("tests/data/jobs/quera_submit.json")
    for number, future in job_future.hardware_task_futures.items():
        print(f"{number}: {future.status()}")
    print(job_future.report().markdown)
