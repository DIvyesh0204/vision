from common_utils import IN_CIRCLE_CI, CIRCLECI_GPU_NO_CUDA_MSG, IN_FBCODE, IN_RE_WORKER, CUDA_NOT_AVAILABLE_MSG
import torch
import pytest


def pytest_configure(config):
    # register an additional marker (see pytest_collection_modifyitems)
    config.addinivalue_line(
        "markers", "needs_cuda: mark for tests that rely on a CUDA device"
    )


def pytest_collection_modifyitems(items):
    # This hook is called by pytest after it has collected the tests (google its name!)
    # We can ignore some tests as we see fit here, or add marks, such as a skip mark.

    out_items = []
    for item in items:
        # The needs_cuda mark will exist if the test was explicitely decorated with
        # the @needs_cuda decorator. It will also exist if it was parametrized with a
        # parameter that has the mark: for example if a test is parametrized with
        # @pytest.mark.parametrize('device', cpu_and_gpu())
        # the "instances" of the tests where device == 'cuda' will have the 'needs_cuda' mark,
        # and the ones with device == 'cpu' won't have the mark.
        needs_cuda = item.get_closest_marker('needs_cuda') is not None

        if needs_cuda and not torch.cuda.is_available():
            # In general, we skip cuda tests on machines without a GPU
            # There are special cases though, see below
            item.add_marker(pytest.mark.skip(reason=CUDA_NOT_AVAILABLE_MSG))

        if IN_FBCODE:
            # fbcode doesn't like skipping tests, so instead we  just don't collect the test
            # so that they don't even "exist", hence the continue statements.
            if not needs_cuda and IN_RE_WORKER:
                # The RE workers are the machines with GPU, we don't want them to run CPU-only tests.
                continue
            if needs_cuda and not torch.cuda.is_available():
                # On the test machines without a GPU, we want to ignore the tests that need cuda.
                # TODO: something more robust would be to do that only in a sandcastle instance,
                # so that we can still see the test being skipped when testing locally from a devvm
                continue
        elif IN_CIRCLE_CI:
            # Here we're not in fbcode, so we can safely collect and skip tests.
            if not needs_cuda and torch.cuda.is_available():
                # Similar to what happens in RE workers: we don't need the CircleCI GPU machines
                # to run the CPU-only tests.
                item.add_marker(pytest.mark.skip(reason=CIRCLECI_GPU_NO_CUDA_MSG))

        out_items.append(item)

    items[:] = out_items
