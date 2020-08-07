![GitHub CI](https://github.com/renkekuhlmann/gams-benchmark/workflows/GitHub%20CI/badge.svg)

# GAMS Benchmark

This is a small Python script for benchmarking [GAMS] -
either directly using the command line interface or through [JuMP] or [Pyomo].
The results are exported to `.trc` files that can be analyzed with [Paver2].

To start a benchmark, run for example:
```
python src/benchmark --testset=minlplib --threads=4 --gams=/opt/gams --gamsopt="solver=scip"
```

Benchmark runs can be interrupted at any time and resumed later on. Simply restart
with the same options. If a `.trc` file can be found for a model, those results
will be used. Otherwise the process is (re-)started.

For further help, run:
```bash
python src/benchmark -h
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
cd <repository_root>/testests/minlplib
./update.sh
```
to download (or update) the model files and
```bash
cd <repository_root>/testsets
./convert.sh minlplib pyomo
```
to convert the models to the [Pyomo] format.


## Options

### Benchmark

```
--result=<result_directory>
--max_time=<max_time_in_seconds>
--kill_time=<kill_time_in_seconds>
--max_jobs=<number_of_jobs>
--max_total_time=<max_total_time_in_seconds>
--threads=<number_of_threads>
```
Results are stored in the directory `<result_directory>` (default: latest). A
job has a maximum time of `<max_time_in_seconds>` (default: 60) and will be
killed after further `<kill_time_in_seconds>` (default: 30) have passed. The
benchmark runs at most `<number_of_jobs>` number of jobs and will terminate (if
not finished earlier) after `<max_total_time_in_seconds>`. Jobs can be executed
in parallel with `<number_of_threads>` (default: 1) number of threads.

### Testset

```
--testset=<testset>
--modelpath=<path_to_model_files>
--interface=<interface>
```
Specify the testset by `--testset=<testset>` (default: minlplib). For a custom
testset, use `--testset=other` and provide the path to the `.gms`, `.py` or
`.jl` files with `--modelpath=<path_to_model_files>`. The used interface has to
be specfied with `--interface=<interface>` (default: direct), e.g.,
`--interface=pyomo`.

### GAMS Options

```
--gams=<gams_system_dir>
--gamsopt="opt1=val1,opt2=val2;opt3=val3..."
```
The GAMS system directory is given by `--gams=<gams_system_dir>`. GAMS options
can be passed via `--gamsopt="opt1=val1,opt2=val2;opt3=val3..."`. Here, different
configurations are separated by `;` and different options by `,`. For example,
`--gamsopt="solver=conopt,iterlim=101;solver=minos,iterlim=102"` will add each
testset instance twice and solve: (i) with `conopt` within 101 iterations and (ii)
with `minos` within 102 iterations.


[GAMS]: https://www.gams.com/
[JuMP]: https://github.com/JuliaOpt/JuMP.jl
[Pyomo]: https://github.com/Pyomo/pyomo
[MINLPlib]: http://www.minlplib.org/
[Paver2]: https://github.com/coin-or/Paver

