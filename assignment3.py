import csv
import random
from pathlib import Path
from statistics import median
from time import perf_counter_ns


# Part 1: Randomized and deterministic Quicksort

def partition(values, low, high, pivot_index):
    """Group values into three regions: less than, equal to, and greater than the pivot."""
    pivot = values[pivot_index]
    values[low], values[pivot_index] = values[pivot_index], values[low]

    # Move values smaller than the pivot to the left.
    less_end = low
    for index in range(low + 1, high + 1):
        if values[index] < pivot:
            less_end += 1
            values[less_end], values[index] = values[index], values[less_end]

    values[low], values[less_end] = values[less_end], values[low]

    # Group all other copies of the pivot next to it.
    equal_end = less_end
    for index in range(less_end + 1, high + 1):
        if values[index] == pivot:
            equal_end += 1
            values[equal_end], values[index] = values[index], values[equal_end]

    return less_end, equal_end


def quicksort(values, rng=None):
    """Sort in place. Use the first pivot unless a random generator is supplied."""
    def sort_range(low, high):
        while low < high:
            pivot_index = low if rng is None else rng.randrange(low, high + 1)
            equal_start, equal_end = partition(values, low, high, pivot_index)

            # Recurse on the smaller side and use the loop for the larger side.
            # This bounds stack depth even when the pivots are consistently poor.
            if equal_start - low < high - equal_end:
                sort_range(low, equal_start - 1)
                low = equal_end + 1
            else:
                sort_range(equal_end + 1, high)
                high = equal_start - 1

    sort_range(0, len(values) - 1)


def randomized_quicksort(values, rng=None):
    if rng is None:
        rng = random.Random()
    quicksort(values, rng)


def deterministic_quicksort(values):
    quicksort(values)


# Part 2: Hash table with separate chaining

class ChainedHashTable:
    """Store key-value pairs in buckets. Keys are integers from 0 through PRIME - 1."""

    PRIME = 2**61 - 1

    def __init__(self, capacity=8, seed=None):
        if not isinstance(capacity, int) or capacity < 1:
            raise ValueError("Capacity must be a positive integer.")

        rng = random.Random(seed)
        self._a = rng.randrange(1, self.PRIME)
        self._b = rng.randrange(self.PRIME)
        self._buckets = [[] for _ in range(capacity)]
        self._size = 0

    @property
    def capacity(self):
        return len(self._buckets)

    @property
    def load_factor(self):
        return self._size / self.capacity

    def __len__(self):
        return self._size

    def _index(self, key):
        if type(key) is not int or not 0 <= key < self.PRIME:
            raise ValueError("Key must be an integer from 0 through PRIME - 1.")
        return ((self._a * key + self._b) % self.PRIME) % self.capacity

    def _resize(self):
        old_buckets = self._buckets
        self._buckets = [[] for _ in range(2 * len(old_buckets))]

        # Bucket indices depend on capacity, so rehash every existing key.
        for bucket in old_buckets:
            for key, value in bucket:
                self._buckets[self._index(key)].append((key, value))

    def insert(self, key, value):
        """Add a new key or update the value of an existing key."""
        bucket = self._buckets[self._index(key)]
        for position, (stored_key, _) in enumerate(bucket):
            if stored_key == key:
                bucket[position] = (key, value)
                return

        if (self._size + 1) / self.capacity > 0.75:
            self._resize()
            bucket = self._buckets[self._index(key)]

        bucket.append((key, value))
        self._size += 1

    def search(self, key):
        """Return the stored value, or raise KeyError if the key is absent."""
        for stored_key, value in self._buckets[self._index(key)]:
            if stored_key == key:
                return value
        raise KeyError(key)

    def delete(self, key):
        """Remove the key and return its value, or raise KeyError if absent."""
        bucket = self._buckets[self._index(key)]
        for position, (stored_key, value) in enumerate(bucket):
            if stored_key == key:
                bucket.pop(position)
                self._size -= 1
                return value
        raise KeyError(key)


# Correctness checks

def check_algorithms():
    examples = [
        [],
        [7],
        [4, 4, 4, 4],
        [5, -2, 5, 0, -2, 3],
        list(range(100)),
        list(range(99, -1, -1)),
    ]

    for example in examples:
        expected = sorted(example)
        first = example.copy()
        second = example.copy()
        randomized_quicksort(first, random.Random(42))
        deterministic_quicksort(second)
        assert first == expected
        assert second == expected

    table = ChainedHashTable(capacity=8, seed=42)

    # Find two keys that share a bucket and check that deleting one preserves the other.
    first_key = 0
    second_key = next(
        key for key in range(1, 1000)
        if table._index(key) == table._index(first_key)
    )
    table.insert(first_key, "first")
    table.insert(second_key, "second")
    table.insert(first_key, "updated")
    assert len(table) == 2
    assert table.search(first_key) == "updated"
    assert table.delete(first_key) == "updated"
    assert table.search(second_key) == "second"

    for operation in (table.search, table.delete):
        try:
            operation(first_key)
        except KeyError:
            pass
        else:
            raise AssertionError("A missing key should raise KeyError.")

    # Force several resizes and verify that every stored value survives.
    for key in range(1000, 1100):
        table.insert(key, key * 2)

    assert len(table) == 101
    assert table.capacity > 8
    assert table.load_factor <= 0.75
    assert table.search(second_key) == "second"
    assert all(table.search(key) == key * 2 for key in range(1000, 1100))
    print("Correctness checks passed.")


# Empirical comparison

def make_input(distribution, size, rng):
    if distribution == "Sorted":
        return list(range(size))
    if distribution == "Reverse sorted":
        return list(range(size - 1, -1, -1))
    if distribution == "Repeated":
        return [rng.randrange(10) for _ in range(size)]
    if distribution == "Random":
        values = list(range(size))
        rng.shuffle(values)
        return values
    raise ValueError(f"Unknown distribution: {distribution}")


def run_benchmarks():
    sizes = (500, 1000, 2000)
    distributions = ("Random", "Sorted", "Reverse sorted", "Repeated")
    trials = 5
    output_dir = Path(__file__).resolve().parent / "results"
    output_dir.mkdir(exist_ok=True)
    raw_rows = []
    summary_rows = []

    print("\nMedian runtime in milliseconds")
    print(f"{'Input':<16} {'Size':>6} {'Random pivot':>14} {'First pivot':>14}")

    for group, distribution in enumerate(distributions):
        for size in sizes:
            timings = {"Random pivot": [], "First pivot": []}

            for trial in range(trials):
                data_seed = group * 1_000_000 + size * 10 + trial
                pivot_seed = 10_000_000 + data_seed
                original = make_input(distribution, size, random.Random(data_seed))
                expected = sorted(original)
                pivot_rng = random.Random(pivot_seed)

                # Alternate execution order. Both versions get identical input.
                order = ["Random pivot", "First pivot"]
                if trial % 2:
                    order.reverse()

                for name in order:
                    values = original.copy()
                    start = perf_counter_ns()
                    if name == "Random pivot":
                        randomized_quicksort(values, pivot_rng)
                    else:
                        deterministic_quicksort(values)
                    elapsed_ms = (perf_counter_ns() - start) / 1_000_000

                    if values != expected:
                        raise AssertionError(f"{name} failed on {distribution} input.")

                    timings[name].append(elapsed_ms)
                    raw_rows.append([
                        distribution, size, trial + 1, name, data_seed,
                        pivot_seed if name == "Random pivot" else "",
                        f"{elapsed_ms:.6f}",
                    ])

            random_ms = median(timings["Random pivot"])
            first_ms = median(timings["First pivot"])
            print(f"{distribution:<16} {size:>6} {random_ms:>14.3f} {first_ms:>14.3f}")
            summary_rows.append([distribution, size, f"{random_ms:.6f}", f"{first_ms:.6f}"])

    with (output_dir / "raw_timings.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([
            "distribution", "size", "trial", "algorithm",
            "data_seed", "pivot_seed", "runtime_ms",
        ])
        writer.writerows(raw_rows)

    with (output_dir / "summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["distribution", "size", "random_pivot_ms", "first_pivot_ms"])
        writer.writerows(summary_rows)

    print(f"\nResults saved in {output_dir}")


if __name__ == "__main__":
    check_algorithms()
    run_benchmarks()