# MoRoOp Dataset Toolkit

Python tools for downloading, loading, and reproducing the figures from the Mobile Robot Operations (MoRoOp) dataset. The package targets the versioned dataset release used for the accompanying Scientific Data submission.

## Installation

```bash
git clone https://github.com/JaFeKl/moroop-dataset-toolkit.git
cd moroop-dataset-toolkit
python -m pip install .
```

For development and test dependencies:

```bash
python -m pip install -e ".[test]"
```

## Quick Start

Follow the [MoRoOp dataset walkthrough](examples/moroop_dataset_walkthrough.ipynb) to download, inspect, and plot the dataset in Jupyter.

## Download the data

Download a tagged snapshot from the Hugging Face Hub:

```bash
moroop download --source huggingface --revision 1.0.0 --destination data/moroop
```

The dataset is also available through the [KTH Data Repository](https://datarepository.kth.se/records/0qdea-h5385). To download its ZIP archive, obtain the direct ZIP download URL from that record and run:

```bash
moroop download --source kth --url "https://..." --destination data/moroop
```

The downloaded dataset's `data/` directory contains the Parquet files. Pass that directory to the examples below.

## Load Parquet tables

```python
from moroop_dataset_toolkit import load_table

data_directory = "data/moroop/data"
jobs = load_table(data_directory, "jobs", shift="2026_07_27_evening")
robot_states = load_table(
	data_directory,
	"robot_state_cleaned",
	shift="2026_07_27_evening",
	columns=["created_at", "pos_x", "pos_y", "state"],
)
kits = load_table(data_directory, "kits")
```

Available shift-level tables are `jobs`, `operations`, `dispatch_events`, `robot_state_raw`, and `robot_state_cleaned`. The `kits` catalogue is shared across shifts.

## Reproduce publication figures

After downloading the data, generate all four figures:

```bash
moroop figures --data-directory data/moroop/data --output-directory figures
```

This creates:

- `representative_operations_gantt.pdf`
- `representative_operations_velocity.pdf`
- `robot_battery_state.pdf`
- `robot_driving_path.pdf`

The figures use the representative shift and time interval specified in the accompanying publication.

## Tests

```bash
pytest
```

## Cite As

Klein, J.-F. (2026). *MoRoOp: A Dataset of Autonomous Mobile Robot Operations in Production Logistics* (Version 1.0.0) \[Dataset]. datarepository.kth.se. [https://doi.org/10.71775/kth.0qdea-h5385](https://doi.org/10.71775/kth.0qdea-h5385)

## License

See [LICENSE](LICENSE).