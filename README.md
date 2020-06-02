![GitHub CI](https://github.com/renkekuhlmann/gams-benchmark/workflows/GitHub%20CI/badge.svg)

# GAMS Benchmark

This is a small Python script for benchmarking [GAMS] -
either directly using the command line interface or through [JuMP] or [Pyomo].
The results are exported to `.trc` files that can be analyzed with [Paver2].

Benchmark runs can be interrupted at any time and resumed later on. Simply restart
with the same options.

For help, run:
```bash
python benchmark.py -h
```

## Testset Models

Input formats are either [GAMS] models (`.gms` files), [Pyomo] models that define
a concrete model, i.e.,
```python
m = ConcreteModel()
```
in the main namespace, or analogously [JuMP] models:
```julia
m = Model()
```

There are a few testlibs that can be setup conveniently, for example the
[MINLPlib]. Simply do
```bash
cd testests/minlplib
./update.sh
```
to download (or update) the model files and
```bash
cd testsets
./convert.sh minlplib pyomo
```
to convert the models to the [Pyomo] format.


## Options

### Benchmark

Results are stored in the directory given by `--result=<result_directory>`
(default: latest). A job has a maximum time of `--max_time=<time_in_seconds>`
(default: 60) and will be killed after further `--kill_time=<time_in_seconds>`
(default: 30) have passed. The benchmark runs at most
`--jobs_max=<number_of_jobs>` number of jobs and will terminate (if not finished
earlier) after `--jobs_max_time=<time_in_seconds>`. Jobs can be executed in
parallel with `--threads=<number_of_threads>` (default: 1) number of threads.

### Testset

Specify the testset by `--testset=<testset>` (default: minlplib). For a custom
testset, use `--testset=other` and provide the path to the `.gms`, `.py` or
`.jl` files with `--modelpath=<path_to_model_files>`. The used interface has to
be specfied with `--interface=<interface>` (default: direct), e.g.,
`--interface=pyomo`.

### GAMS Options

The GAMS system directory is given by `--gams=<gams_system_dir>`. GAMS options
can be passed via `--gamsopt="opt1=val1,opt2=val2;opt3=val3..."`. Here, different
configurations are separated by `;` or different options by `,`. For example,
`--gamsopt="solver=conopt,iterlim=101;solver=minos,iterlim=102"` will add each
testset instance twice and solve: (i) with `conopt` within 101 iterations and (ii)
with `minos` within 102 iterations.


[GAMS]: https://www.gams.com/
[JuMP]: https://github.com/JuliaOpt/JuMP.jl
[Pyomo]: https://github.com/Pyomo/pyomo
[MINLPlib]: http://www.minlplib.org/
[Paver2]: https://github.com/coin-or/Paver

