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

| Option Name      | Default  | Explanation                                       |
| ---------------- | -------- | ------------------------------------------------- |
| `result`         | latest   | Directory in which the results are stored in      |
| `max_time`       | 60       | Maximum time per job                              |
| `kill_time`      | 30       | Additional time to max_time until a job is killed |
| `max_jobs`       | inf      | Maximum number of added jobs, if inf then whole testset |
| `max_total_time` | inf      | Maximum time until no jobs are processed anymore  |
| `threads`        | 1        | Number of threads to run jobs in parallel         |
| `output`         |          | Output format, see below                          |

The output is grouped in pairs of columns, e.g. model characteristics. The option
`output` lists the displayed groups separated by `|`. Full output would be:
`jobs|name|config|model|status|objective|time`.

### Testset

| Option Name      | Default  | Explanation                                       |
| ---------------- | -------- | ------------------------------------------------- |
| `testset`        | minlplib | Testset to be used (minlplib, princetonlib, other) |
| `modelpath`      |          | If testset is other, this specifies the path to the models |
| `interface`      | direct   | Modelling interface (direct GAMS call, JuMP, Pyomo) |

### GAMS Options

| Option Name      | Default  | Explanation                                       |
| ---------------- | -------- | ------------------------------------------------- |
| `gams`           | /opt/gams| Path to GAMS system directory                     |
| `gamsopt`        |          | GAMS solver options, see below                    |

GAMS options can be passed via `--gamsopt="opt1=val1,opt2=val2;opt3=val3..."`.
Here, different configurations are separated by `;` and different options by
`,`. For example,
`--gamsopt="solver=conopt,iterlim=101;solver=minos,iterlim=102"` will add each
testset instance twice and solve: (i) with `conopt` within 101 iterations and
(ii) with `minos` within 102 iterations.


[GAMS]: https://www.gams.com/
[JuMP]: https://github.com/JuliaOpt/JuMP.jl
[Pyomo]: https://github.com/Pyomo/pyomo
[MINLPlib]: http://www.minlplib.org/
[Paver2]: https://github.com/coin-or/Paver

