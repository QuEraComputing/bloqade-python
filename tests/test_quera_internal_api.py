from bloqade import start
from bloqade.task import HardwareFuture
import vcr


@vcr.use_cassette("tests/data/cassettes/quera_submit.yaml")
def test_quera_submit():
    job_future = (
        start.add_position((0, 0))
        .rydberg.rabi.amplitude.uniform.piecewise_linear(
            [0.1, "run_time", 0.1], [0, 15, 15, 0]
        )
        .assign(run_time=2.0)
        .parallelize(20)
        .quera(10, config_file="tests/data/config/mock_quera_api.json")
        .remove_invalid_tasks()
        .submit()
    )

    job_future.save_json("tests/data/jobs/quera_submit.json")


@vcr.use_cassette("tests/data/cassettes/quera_fetch.yaml")
def test_quera_retrieve():
    job_future = HardwareFuture()
    job_future.load_json("tests/data/jobs/quera_submit.json")
    for number, future in job_future.futures.items():
        print(future.status())
    print(job_future.report().markdown)


test_quera_submit()
test_quera_retrieve()
