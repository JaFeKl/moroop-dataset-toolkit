"""Reproduce the four figures supplied with the MoRoOp publication."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch

from .data import load_table

SHIFT = "2026_07_27_evening"
START = "2026-07-27 16:08:00+00:00"
END = "2026-07-27 16:13:00+00:00"
FIGURE_SIZE_GANTT = (8, 3.4)
FIGURE_SIZE_VELOCITY = (8, 2.4)
AXIS_LABEL_SIZE = 10
TICK_LABEL_SIZE = 9
LEGEND_SIZE = 9
ANNOTATION_FONT_SIZE = 9
FIGURE_SIZE_BATTERY = (6, 2.8)
BATTERY_KEYS = {
    "TL": "tl_charge_state",
    "TR": "tr_charge_state",
    "BL": "bl_charge_state",
    "BR": "br_charge_state",
}
BATTERY_COLORS = {
    "TL": "#0072B2",
    "TR": "#009E73",
    "BL": "#D55E00",
    "BR": "#CC79A7",
}
STATIONS = {
    "Charging": ((0.425, -1.8), "P", "#D6B656"),
    "Assembly": ((1.475, 0.397), "^", "#d95f02"),
    "Storage": ((4.681, -1.280), "s", "#446E2C"),
    "Kitting": ((7.661, 0.307), "D", "#7570b3"),
}


def _save(figure: plt.Figure, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path)
    plt.close(figure)


def _annotate_above_with_leader(
    axis: plt.Axes,
    x_position: float,
    text: str,
    line_start: float,
    text_height: float,
) -> None:
    """Draw a vertical leader line and centered annotation above a plotted item."""
    axis.vlines(
        x_position,
        line_start,
        text_height,
        color="0.35",
        linewidth=0.6,
        linestyles=(0, (4, 4)),
    )
    axis.text(
        x_position,
        text_height,
        text,
        ha="center",
        va="bottom",
        fontsize=ANNOTATION_FONT_SIZE,
    )


def _segments(
    operation: pd.Series, states: pd.DataFrame
) -> list[tuple[pd.Timestamp, pd.Timestamp, str]]:
    samples = states.loc[
        (states.created_at >= operation.start_time)
        & (states.created_at < operation.finish_time),
        ["created_at", "state"],
    ].sort_values("created_at")
    if samples.empty:
        return [(operation.start_time, operation.finish_time, "latency")]
    boundaries = [operation.start_time, *samples.created_at, operation.finish_time]
    labels, driving, segments = [], False, []
    for state in samples.state:
        if state == "Navigating":
            labels.append("navigating")
            driving = True
        else:
            labels.append("station_process" if driving else "latency")
    for segment_start, segment_end, label in zip(boundaries, boundaries[1:], labels):
        if segments and segments[-1][2] == label:
            segments[-1] = (segments[-1][0], segment_end, label)
        else:
            segments.append((segment_start, segment_end, label))
    return segments


def _wait_label(
    operation: pd.Series, job_type: str, index: int, color_count: int | None
) -> str:
    goal = json.loads(operation.payload)["goal"]
    if job_type == "empty_box_refill":
        return {"assembly": r"$t_{A,R}$", "kitting": r"$t_{K,R}$"}.get(goal, r"$t_R$")
    if color_count is None:
        raise ValueError("Assembly operations require a kit color count.")
    labels = {
        ("warehouse", 0): rf"$t_{{S,L,{color_count}}}$",
        ("kitting", 1): rf"$t_{{K,U,{color_count}}} + t_{{K,P,{color_count}}}$",
        ("assembly", 2): r"$t_{A,U}$",
        ("warehouse", 3): rf"$t_{{S,U,{color_count}}}$",
    }
    return labels.get((goal, index), r"$t$")


def _navigation_label(operation: pd.Series) -> str:
    """Return the destination label for a navigating segment."""
    destination = json.loads(operation.payload)["goal"]
    return f"Nav to {destination}"


def representative_gantt(data_directory: str | Path, output_path: str | Path) -> None:
    """Create the representative operation timeline figure."""
    start, end = pd.Timestamp(START), pd.Timestamp(END)
    jobs = load_table(data_directory, "jobs", shift=SHIFT)
    operations = load_table(data_directory, "operations", shift=SHIFT)
    states = load_table(data_directory, "robot_state_cleaned", shift=SHIFT)
    kits = load_table(data_directory, "kits")
    jobs = jobs.assign(
        job_type=jobs.payload.map(lambda payload: json.loads(payload)["job_type"])
    )
    jobs = jobs.loc[
        jobs.start_time.notna()
        & jobs.finish_time.notna()
        & jobs.start_time.between(start, end)
        & jobs.finish_time.between(start, end)
        & jobs.job_type.isin(["kit supply", "empty_box_refill"])
    ].sort_values("start_time")
    if (
        len(jobs) != 2
        or jobs.iloc[0].job_type != "kit supply"
        or jobs.iloc[1].job_type != "empty_box_refill"
    ):
        raise ValueError(
            "The representative interval must contain one kit supply job followed by one empty-box-refill job."
        )
    operations = operations.loc[
        operations.job_id.isin(jobs.id)
        & operations.start_time.notna()
        & operations.finish_time.notna()
    ].sort_values("start_time")
    states = states.loc[states.created_at.between(start, end)]
    job_types = jobs.set_index("id").job_type
    counts = kits.groupby("kit_id").color.nunique().to_dict()
    colors = {"kit supply": "#446E2C", "empty_box_refill": "#D6B656"}
    state_colors = {"navigating": "#377eb8", "station_process": "#d9d9d9"}
    job_color_counts = {
        row.id: counts[json.loads(row.payload)["kit_id"]]
        for row in jobs.itertuples()
        if row.job_type == "kit supply"
    }
    last_middle_navigation_time: pd.Timestamp | None = None
    navigation_label_separation = pd.Timedelta(seconds=40)
    figure, axis = plt.subplots(figsize=FIGURE_SIZE_GANTT, constrained_layout=True)
    for row, index in zip(
        operations.itertuples(index=False),
        operations.groupby("job_id").cumcount(),
        strict=True,
    ):
        operation = pd.Series(row._asdict())
        start_number = mdates.date2num(row.start_time)
        axis.broken_barh(
            [(start_number, mdates.date2num(row.finish_time) - start_number)],
            (0.65, 0.7),
            facecolors="none",
            edgecolors=colors[job_types[row.job_id]],
            linewidth=1.5,
            zorder=3,
        )
        for segment_start, segment_end, label in _segments(operation, states):
            if label == "latency":
                continue
            segment_number = mdates.date2num(segment_start)
            axis.broken_barh(
                [(segment_number, mdates.date2num(segment_end) - segment_number)],
                (0.68, 0.64),
                facecolors=state_colors[label],
                edgecolors="none",
                zorder=2,
            )
            midpoint = segment_start + (segment_end - segment_start) / 2
            if label == "navigating":
                navigation_height = 1.68
                if (
                    last_middle_navigation_time is not None
                    and midpoint - last_middle_navigation_time
                    < navigation_label_separation
                ):
                    navigation_height = 1.88
                else:
                    last_middle_navigation_time = midpoint
                _annotate_above_with_leader(
                    axis,
                    mdates.date2num(midpoint),
                    _navigation_label(operation),
                    line_start=1.20,
                    text_height=navigation_height,
                )
            elif label == "station_process":
                _annotate_above_with_leader(
                    axis,
                    mdates.date2num(midpoint),
                    _wait_label(
                        operation,
                        job_types[row.job_id],
                        index,
                        job_color_counts.get(row.job_id),
                    ),
                    line_start=1.20,
                    text_height=1.48,
                )

    for job in jobs.itertuples(index=False):
        job_start = mdates.date2num(job.start_time)
        job_end = mdates.date2num(job.finish_time)
        annotation_height = 0.55
        axis.annotate(
            "",
            xy=(job_start, annotation_height),
            xytext=(job_end, annotation_height),
            arrowprops={
                "arrowstyle": "|-|",
                "color": colors[job.job_type],
                "shrinkA": 0,
                "shrinkB": 0,
            },
        )
        axis.text(
            (job_start + job_end) / 2,
            annotation_height - 0.04,
            f"{job.job_type.replace('_', ' ').title()} job\n{job.id}",
            color=colors[job.job_type],
            ha="center",
            va="top",
            fontsize=ANNOTATION_FONT_SIZE,
        )

    axis.set_yticks([1], ["AMR"])
    axis.set_ylim(0.05, 2.15)
    axis.set_xlim(mdates.date2num(start), mdates.date2num(end))
    axis.xaxis.set_major_locator(mdates.MinuteLocator(interval=1, tz=start.tz))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=start.tz))
    axis.set_xlabel("Time (UTC)", fontsize=AXIS_LABEL_SIZE)
    axis.tick_params(axis="both", labelsize=TICK_LABEL_SIZE)
    axis.grid(axis="x", color="0.85")
    axis.legend(
        handles=[
            Patch(facecolor=state_colors["navigating"], label="Navigating"),
            Patch(
                facecolor=state_colors["station_process"], label="Waiting for process"
            ),
            Patch(
                facecolor="none",
                edgecolor=colors["kit supply"],
                label="Kit supply operation",
            ),
            Patch(
                facecolor="none",
                edgecolor=colors["empty_box_refill"],
                label="Empty-box refill operation",
            ),
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, 1.02),
        ncols=4,
        frameon=False,
        fontsize=LEGEND_SIZE,
    )
    _save(figure, output_path)


def representative_velocity(
    data_directory: str | Path, output_path: str | Path
) -> None:
    """Create the velocity plot for the representative operation interval."""
    start, end = pd.Timestamp(START), pd.Timestamp(END)
    states = load_table(
        data_directory,
        "robot_state_cleaned",
        shift=SHIFT,
        columns=["created_at", "velocity_x", "velocity_y"],
    ).sort_values("created_at")
    states = states.loc[states.created_at.between(start, end)]
    figure, axis = plt.subplots(figsize=FIGURE_SIZE_VELOCITY, constrained_layout=True)
    axis.plot(
        states.created_at,
        states.velocity_x,
        color="#0072B2",
        linewidth=1.2,
        label=r"$v_x$",
    )
    axis.plot(
        states.created_at,
        states.velocity_y,
        color="#D55E00",
        linewidth=1.2,
        label=r"$v_y$",
    )
    axis.set_xlim(start, end)
    axis.set_xlabel("Time (UTC)", fontsize=AXIS_LABEL_SIZE)
    axis.set_ylabel("Linear velocity (m/s)", fontsize=AXIS_LABEL_SIZE)
    axis.tick_params(axis="both", labelsize=TICK_LABEL_SIZE)
    axis.xaxis.set_major_locator(mdates.MinuteLocator(interval=1, tz=start.tz))
    axis.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", tz=start.tz))
    axis.grid(axis="y", color="0.85")
    handles, labels = axis.get_legend_handles_labels()
    axis.legend(
        handles,
        labels,
        loc="upper left",
        ncols=2,
        frameon=True,
        fontsize=LEGEND_SIZE,
    )
    _save(figure, output_path)


def _charging_intervals(
    robot_states: pd.DataFrame,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Return contiguous intervals during which the robot reported charging."""
    charging = robot_states["is_robot_charging"].fillna(0).astype(bool)
    groups = charging.ne(charging.shift()).cumsum()
    return [
        (group["created_at"].iloc[0], group["created_at"].iloc[-1])
        for _, group in robot_states.loc[charging].groupby(groups[charging])
    ]


def battery_state(
    data_directory: str | Path, output_path: str | Path, shift: str = SHIFT
) -> None:
    """Create the four-battery state-of-charge figure for one shift."""
    states = load_table(
        data_directory,
        "robot_state_cleaned",
        shift=shift,
        columns=["created_at", "is_robot_charging", *BATTERY_KEYS.values()],
    ).sort_values("created_at")
    figure, axis = plt.subplots(figsize=FIGURE_SIZE_BATTERY, constrained_layout=True)
    for label, key in BATTERY_KEYS.items():
        axis.plot(
            states["created_at"],
            states[key],
            label=label,
            color=BATTERY_COLORS[label],
            linewidth=1.2,
        )
    for interval_start, interval_end in _charging_intervals(states):
        axis.axvspan(
            interval_start,
            interval_end,
            color="#D6B656",
            alpha=0.25,
        )
    axis.set_xlim(states["created_at"].iloc[0], states["created_at"].iloc[-1])
    axis.set_ylim(0, 100)
    axis.set_xlabel("Time (UTC)", fontsize=AXIS_LABEL_SIZE)
    axis.set_ylabel("Battery state of charge (SoC) (%)", fontsize=AXIS_LABEL_SIZE)
    axis.tick_params(axis="both", labelsize=TICK_LABEL_SIZE)
    axis.xaxis.set_major_locator(
        mdates.HourLocator(interval=1, tz=states["created_at"].dt.tz)
    )
    axis.xaxis.set_major_formatter(
        mdates.DateFormatter("%H:%M", tz=states["created_at"].dt.tz)
    )
    axis.grid(axis="y", color="0.85")
    axis.legend(
        handles=[
            *(
                Patch(color=BATTERY_COLORS[label], label=label)
                for label in BATTERY_KEYS
            ),
            Patch(facecolor="#D6B656", alpha=0.25, label="Charging"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 1.16),
        ncols=5,
        frameon=False,
        fontsize=LEGEND_SIZE,
    )
    _save(figure, output_path)


def driving_path(
    data_directory: str | Path, output_path: str | Path, shift: str = SHIFT
) -> None:
    """Create the AMR driving-path figure for all navigating observations."""
    states = load_table(
        data_directory,
        "robot_state_cleaned",
        shift=shift,
        columns=["created_at", "pos_x", "pos_y", "state"],
    ).sort_values("created_at")
    states = states.loc[
        states.state.eq("Navigating") & states.pos_x.notna() & states.pos_y.notna()
    ].copy()
    if states.empty:
        raise ValueError("No navigating robot-state observations found.")
    states["path_segment"] = (
        states.created_at.diff().gt(pd.Timedelta(seconds=10)).cumsum()
    )
    figure, axis = plt.subplots(figsize=(6, 2.35), constrained_layout=True)
    for _, segment in states.groupby("path_segment"):
        axis.plot(segment.pos_x, segment.pos_y, color="#377eb8", linewidth=0.8)
    for name, (position, marker, color) in STATIONS.items():
        axis.scatter(*position, marker=marker, color=color, s=50, label=name, zorder=3)
    axis.set(xlabel="Position x-coordinate (m)", ylabel="Position y-coordinate (m)")
    axis.set_aspect(1.0, adjustable="box")
    axis.grid(color="0.85")
    axis.legend(loc="upper center", bbox_to_anchor=(0.5, 1.2), ncols=4, frameon=False)
    _save(figure, output_path)
