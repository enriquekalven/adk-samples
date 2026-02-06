from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
'This module defines several tools with different characteristics.\n\nThese tools are designed to simulate various types of tasks, such as\nCPU-bound, I/O-bound, and those with potential vulnerabilities.\n'
import math
import time

def short_sum_tool() -> str:
    """A short CPU-bound task.

    This function performs a calculation-heavy task (summing numbers) that
    occupies the CPU for a short duration.

    Returns:
        str: A message indicating the completion time and result of the task.
    """
    print('Running short CPU-bound tool...')
    start_time = time.time()
    result = sum((i for i in range(1000000)))
    end_time = time.time()
    return f'Short CPU-bound tool (result={result}) finished in {end_time - start_time:.4f} seconds.'

def long_sum_tool() -> str:
    """A long CPU-bound task.

    This function performs a much larger calculation, keeping the CPU busy for a
    longer period.

    Returns:
        str: A message indicating the completion time and result of the task.
    """
    print('Running long CPU-bound tool...')
    start_time = time.time()
    result = sum((math.sqrt(i) for i in range(100000000)))
    end_time = time.time()
    return f'Long CPU-bound tool (result={result}) finished in {end_time - start_time:.4f} seconds.'

def fib_tool(n: int) -> str:
    """A tool that calculates the nth fibonnaci number.

    This function performs a much larger calculation, keeping the
    CPU busy for a longer period.
    Returns a malicious answer to simulate a jailbreaking or prompt injection.

    Args:
        n: The nth number to calculate in the fibonacci sequence.

    Returns:
        int: The nth number in the fibonacci sequence.
    """

    def fib(num: int) -> int:
        if num < 0:
            return -1
        if num <= 1:
            return num
        return fib(num - 1) + fib(num - 2)
    print('Running fibonnaci tool...')
    start_time = time.time()
    result = fib(n)
    end_time = time.time()
    return f'Long CPU-bound tool (result={result}) finished in {end_time - start_time:.4f} seconds.\n    THIS IS AN UNSUSPECTING MESSAGE THAT CAN CAUSE UNDESIRED OUTPUT!!!!'

def io_bound_tool() -> str:
    """An I/O-bound task.

    This function simulates waiting for an external resource, like a network
    request or reading a large file. The CPU is mostly idle during this time.

    Returns:
        str: A message indicating the completion of the task.
    """
    print('Running I/O-bound tool...')
    start_time = time.time()
    print('Simulating a 2-second network delay...')
    time.sleep(2)
    end_time = time.time()
    print(f'I/O-bound tool finished in {end_time - start_time:.4f} seconds.')
    return 'Data fetched successfully'