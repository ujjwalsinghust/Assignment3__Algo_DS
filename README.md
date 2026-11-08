# MSCS 532 Assignment 3

This assignment compares randomized Quicksort with first-pivot Quicksort and implements a hash table with separate chaining. The hash table supports insertion, search, deletion, and resizing.

## How to run

Run `python3 assignment3.py` from this folder. The script uses the Python standard library. It checks both sorting algorithms and the hash table, then runs the sorting benchmarks. Individual measurements are saved in `results/raw_timings.csv`, and median runtimes are saved in `results/summary.csv`.

## Findings

I compared both pivot strategies over five trials per input size and distribution. On 2,000 sorted values, the random pivot took 3.426 ms and the first pivot took 128.268 ms. When I doubled the sorted input from 1,000 to 2,000 values, the first-pivot runtime increased from 32.792 ms to 128.268 ms, nearly fourfold. This is consistent with quadratic growth because the first pivot repeatedly selects the smallest remaining value.

The first pivot was faster on random input at all three sizes. At 2,000 values, it took 3.161 ms compared with 3.765 ms for the random pivot. The two versions were close on repeated values, where both implementations group equal keys during partitioning.
