#!/usr/bin/env python3
"""Reproducible economic model for 'The Economics of AI Loops'.

The script combines:
1. A price snapshot from official provider pages on 2026-07-24.
2. Local runtime telemetry supplied by the author.
3. Explicit scenario assumptions for one regulated-maintenance task cohort.

It generates calculation tables, LaTeX macros, and publication figures.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIG = ROOT / "figures"
SRC = ROOT / "src"
OUT = ROOT / "output"
for path in (FIG, OUT):
    path.mkdir(parents=True, exist_ok=True)

PRICE_FILE = DATA / "model_prices_2026-07-24.csv"
ASSUMPTION_FILE = DATA / "assumptions.json"


def load_inputs() -> tuple[pd.DataFrame, dict]:
    prices = pd.read_csv(PRICE_FILE)
    with ASSUMPTION_FILE.open("r", encoding="utf-8") as handle:
        assumptions = json.load(handle)
    return prices, assumptions


def cumulative_context_tokens(
    turns: np.ndarray | int,
    static_tokens: int,
    new_history_tokens: int,
    output_per_turn: int,
    policy: str,
    retained_tokens: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    n = np.asarray(turns, dtype=float)
    if policy == "full_replay":
        input_tokens = n * static_tokens + (n * (n - 1) / 2.0) * new_history_tokens
    elif policy in {"compaction", "fresh_state"}:
        input_tokens = n * (static_tokens + retained_tokens)
    else:
        raise ValueError(f"Unknown context policy: {policy}")
    output_tokens = n * output_per_turn
    return input_tokens, output_tokens


def cloud_model_cost(input_tokens: float, output_tokens: float, input_price: float, output_price: float) -> float:
    return input_tokens / 1_000_000 * input_price + output_tokens / 1_000_000 * output_price


def local_fixed_monthly(local: dict) -> float:
    return (
        (local["hardware_purchase_usd"] - local["residual_value_usd"])
        / local["economic_life_months"]
        + local["maintenance_monthly_usd"]
    )


def local_energy_per_candidate(local: dict) -> float:
    average_kw = local["measured_energy_kwh"] / local["measured_duration_hours"]
    return average_kw * local["inference_hours_per_candidate"] * local["electricity_usd_per_kwh"]


def expected_cascade_cost(stages: list[dict], human_escalation: float) -> float:
    survival = 1.0
    expected = 0.0
    for stage in stages:
        p = stage["conditional_success_probability"]
        expected += survival * (
            stage["automatic_attempt_cost_usd"]
            + p * stage["success_review_and_residual_risk_usd"]
        )
        survival *= 1.0 - p
    expected += survival * human_escalation
    return expected


def save_figure(fig: plt.Figure, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def figure_unit_of_account() -> None:
    fig, ax = plt.subplots(figsize=(12, 3.1))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")
    labels = [
        (0.35, "Seat", "Fixed access\nprice"),
        (2.75, "Token", "Metered model\nconsumption"),
        (5.15, "Candidate", "One probabilistic\nattempt"),
        (7.55, "Verified outcome", "Independent evidence\nand acceptance"),
        (9.95, "Business value", "Deployed result\nthat changes economics"),
    ]
    facecolors = ["#dcecff", "#fff0cf", "#f5e2ff", "#ddf3df", "#ffe1df"]
    for idx, (x, title, subtitle) in enumerate(labels):
        box = FancyBboxPatch(
            (x, 0.75), 1.7, 1.5,
            boxstyle="round,pad=0.05,rounding_size=0.08",
            linewidth=1.5, edgecolor="#343a40", facecolor=facecolors[idx]
        )
        ax.add_patch(box)
        ax.text(x + 0.85, 1.72, title, ha="center", va="center", fontsize=12, fontweight="bold")
        ax.text(x + 0.85, 1.20, subtitle, ha="center", va="center", fontsize=9)
        if idx < len(labels) - 1:
            ax.add_patch(FancyArrowPatch((x + 1.75, 1.5), (x + 2.35, 1.5), arrowstyle="->", mutation_scale=16, lw=1.5))
    ax.text(6, 0.30, "The invoice ends at tokens. Economic accountability begins after them.",
            ha="center", fontsize=11, fontweight="bold")
    save_figure(fig, "fig01_unit_of_account")


def figure_context_cost(prices: pd.DataFrame, assumptions: dict) -> pd.DataFrame:
    c = assumptions["context"]
    turns = np.arange(1, 61)
    sonnet = prices.loc[prices["model"] == "Claude Sonnet 5"].iloc[0]
    policies = {
        "Full history replay": ("full_replay", 0),
        "Compaction": ("compaction", c["compacted_retained_tokens"]),
        "Fresh context + external state": ("fresh_state", c["fresh_external_state_tokens"]),
    }
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    records = []
    for label, (policy, retained) in policies.items():
        inputs, outputs = cumulative_context_tokens(
            turns, c["static_tokens"], c["new_history_tokens_per_turn"], c["output_tokens_per_turn"], policy, retained
        )
        costs = cloud_model_cost(inputs, outputs, sonnet.input_usd_per_mtok, sonnet.output_usd_per_mtok)
        ax.plot(turns, costs, linewidth=2.3, label=label)
        idx = c["turns"] - 1
        records.append({
            "policy": label,
            "turns": c["turns"],
            "input_tokens": float(inputs[idx]),
            "output_tokens": float(outputs[idx]),
            "model_cost_usd": float(costs[idx]),
        })
        ax.scatter([c["turns"]], [costs[idx]], s=45, zorder=3)
        ax.annotate(f"${costs[idx]:.2f}", (c["turns"], costs[idx]), xytext=(6, 6), textcoords="offset points", fontsize=9)
    ax.set_title("Context architecture changes the cost curve", fontweight="bold", fontsize=14)
    ax.set_xlabel("Model turns")
    ax.set_ylabel("Cumulative model cost (USD)\nClaude Sonnet 5 promotional price, 24 Jul 2026")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(fig, "fig02_context_policy_cost")
    return pd.DataFrame(records)


def model_session_costs(prices: pd.DataFrame, assumptions: dict) -> pd.DataFrame:
    c = assumptions["context"]
    inputs, outputs = cumulative_context_tokens(
        c["turns"], c["static_tokens"], c["new_history_tokens_per_turn"], c["output_tokens_per_turn"],
        "fresh_state", c["fresh_external_state_tokens"]
    )
    rows = []
    for _, row in prices.iterrows():
        rows.append({
            "provider": row.provider,
            "model": row.model,
            "input_tokens": float(inputs),
            "output_tokens": float(outputs),
            "session_model_cost_usd": cloud_model_cost(float(inputs), float(outputs), row.input_usd_per_mtok, row.output_usd_per_mtok),
        })
    return pd.DataFrame(rows).sort_values("session_model_cost_usd")


def figure_model_session_cost(session_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    df = session_df.sort_values("session_model_cost_usd", ascending=True)
    bars = ax.barh(df["model"], df["session_model_cost_usd"])
    ax.bar_label(bars, labels=[f"${x:.2f}" for x in df["session_model_cost_usd"]], padding=4, fontsize=9)
    ax.set_title("Same fresh-context workload, different model invoice", fontweight="bold", fontsize=14)
    ax.set_xlabel("Model cost per 40-turn candidate (USD)")
    ax.grid(axis="x", alpha=0.25)
    ax.set_xlim(0, max(df["session_model_cost_usd"]) * 1.18)
    save_figure(fig, "fig03_model_session_cost")


def build_route_results(prices: pd.DataFrame, assumptions: dict, session_df: pd.DataFrame) -> pd.DataFrame:
    c = assumptions["task_cohort"]
    local = assumptions["local_runtime"]
    fixed = local_fixed_monthly(local)
    local_infra_candidate = fixed / c["tasks_per_month"] + local_energy_per_candidate(local)
    session_cost_map = dict(zip(session_df["model"], session_df["session_model_cost_usd"]))
    route_model_map = {
        "Local Qwen3.6-27B": None,
        "Gemini 3.6 Flash": "Gemini 3.6 Flash",
        "Claude Sonnet 5": "Claude Sonnet 5",
        "Claude Opus 4.8": "Claude Opus 4.8",
    }
    rows = []
    for route_name, params in assumptions["standalone_routes"].items():
        model_cost = local_infra_candidate if route_name.startswith("Local") else session_cost_map[route_model_map[route_name]]
        review = params["human_review_hours"] * c["human_hourly_cost_usd"]
        candidate = (
            model_cost + params["tools_environment_usd"] + params["automated_verification_usd"]
            + review + params["expected_rework_and_risk_usd"]
        )
        p = params["acceptance_probability"]
        rows.append({
            "route": route_name,
            "model_or_infrastructure_usd": model_cost,
            "tools_environment_usd": params["tools_environment_usd"],
            "automated_verification_usd": params["automated_verification_usd"],
            "human_review_usd": review,
            "expected_rework_and_risk_usd": params["expected_rework_and_risk_usd"],
            "candidate_cost_usd": candidate,
            "acceptance_probability": p,
            "cost_per_accepted_usd": candidate / p,
        })
    return pd.DataFrame(rows)


def figure_candidate_stack(routes: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 6.2))
    x = np.arange(len(routes))
    columns = [
        ("model_or_infrastructure_usd", "Model / infrastructure"),
        ("tools_environment_usd", "Tools and environment"),
        ("automated_verification_usd", "Automated verification"),
        ("human_review_usd", "Human review"),
        ("expected_rework_and_risk_usd", "Expected rework and risk"),
    ]
    bottom = np.zeros(len(routes))
    for col, label in columns:
        ax.bar(x, routes[col], bottom=bottom, label=label)
        bottom += routes[col].to_numpy()
    ax.set_xticks(x, routes["route"], rotation=15, ha="right")
    ax.set_ylabel("Complete candidate cost (USD)")
    ax.set_title("The model invoice is a small part of the candidate cost", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(ncol=2, frameon=False, loc="upper left")
    ax2 = ax.twinx()
    ax2.plot(x, routes["cost_per_accepted_usd"], marker="o", linewidth=2.2, label="Cost per accepted outcome")
    ax2.set_ylabel("Cost per accepted outcome (USD)")
    for xx, val in zip(x, routes["cost_per_accepted_usd"]):
        ax2.annotate(f"${val:.0f}", (xx, val), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=9)
    save_figure(fig, "fig04_candidate_cost_stack")


def figure_cost_per_accepted(routes: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    p = np.linspace(0.15, 0.95, 200)
    for candidate in [40, 60, 100, 128]:
        ax.plot(p * 100, candidate / p, label=f"${candidate} candidate")
    for _, row in routes.iterrows():
        ax.scatter(row.acceptance_probability * 100, row.cost_per_accepted_usd, s=65, zorder=4)
        ax.annotate(row.route, (row.acceptance_probability * 100, row.cost_per_accepted_usd),
                    xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set_yscale("log")
    ax.set_xlabel("Independent acceptance probability (%)")
    ax.set_ylabel("Cost per accepted outcome (USD, log scale)")
    ax.set_title("A cheap attempt becomes expensive when acceptance falls", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.25, which="both")
    ax.legend(frameon=False, ncol=2)
    save_figure(fig, "fig05_cost_per_accepted")


def build_policy_results(assumptions: dict) -> pd.DataFrame:
    cas = assumptions["cascade"]
    human = assumptions["task_cohort"]["human_escalation_after_machine_usd"]
    human_only = assumptions["task_cohort"]["human_hours_per_task"] * assumptions["task_cohort"]["human_hourly_cost_usd"]
    stages = [cas["local_first"], cas["local_verifier_guided_retry"], cas["opus_escalation"]]
    rows = [
        {"policy": "Human only", "expected_cost_usd": human_only},
        {"policy": "One local attempt, then human", "expected_cost_usd": expected_cascade_cost(stages[:1], human)},
        {"policy": "Two local attempts, then human", "expected_cost_usd": expected_cascade_cost(stages[:2], human)},
        {"policy": "Local-local-Opus cascade", "expected_cost_usd": expected_cascade_cost(stages, human)},
        {"policy": "Cascade + blind fourth retry", "expected_cost_usd": expected_cascade_cost(stages + [cas["blind_fourth_retry"]], human)},
    ]
    return pd.DataFrame(rows)


def figure_retry_policy(policy_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10.2, 5.7))
    bars = ax.bar(policy_df["policy"], policy_df["expected_cost_usd"])
    ax.bar_label(bars, labels=[f"${v:.0f}" for v in policy_df["expected_cost_usd"]], padding=4)
    ax.set_ylabel("Expected cost to obtain a completed outcome (USD)")
    ax.set_title("Retries are economical only when evidence changes the next attempt", fontsize=14, fontweight="bold")
    ax.tick_params(axis="x", rotation=18)
    ax.grid(axis="y", alpha=0.25)
    save_figure(fig, "fig06_retry_policy")


def build_break_even(prices: pd.DataFrame, assumptions: dict, session_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    local = assumptions["local_runtime"]
    fixed = local_fixed_monthly(local)
    energy = local_energy_per_candidate(local)
    local_p = assumptions["standalone_routes"]["Local Qwen3.6-27B"]["acceptance_probability"]
    task_grid = np.arange(5, 301)
    curves = pd.DataFrame({
        "tasks_per_month": task_grid,
        "Local Qwen3.6-27B": (fixed + energy * task_grid) / (task_grid * local_p),
    })
    cloud_names = ["Gemini 3.6 Flash", "Claude Sonnet 5", "Claude Opus 4.8"]
    session_map = dict(zip(session_df["model"], session_df["session_model_cost_usd"]))
    break_rows = []
    for name in cloud_names:
        p = assumptions["standalone_routes"][name]["acceptance_probability"]
        y = session_map[name] / p
        curves[name] = y
        denom = local_p * y - energy
        be = fixed / denom if denom > 0 else math.inf
        break_rows.append({"cloud_route": name, "break_even_tasks_per_month": be, "cloud_model_cost_per_accepted_usd": y})
    return curves, pd.DataFrame(break_rows)


def figure_break_even(curves: pd.DataFrame, break_even: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.8, 5.7))
    x = curves["tasks_per_month"]
    for col in curves.columns[1:]:
        ax.plot(x, curves[col], linewidth=2.1, label=col)
    for _, row in break_even.iterrows():
        ax.axvline(row.break_even_tasks_per_month, linestyle="--", linewidth=1, alpha=0.45)
        ax.annotate(f"{row.cloud_route}: {row.break_even_tasks_per_month:.0f} tasks/mo",
                    (row.break_even_tasks_per_month, row.cloud_model_cost_per_accepted_usd),
                    xytext=(4, 8), textcoords="offset points", fontsize=8, rotation=15)
    ax.set_xlim(5, 300)
    ax.set_ylim(0, min(20, curves.iloc[:, 1:].to_numpy().max()))
    ax.set_xlabel("Candidates routed per month")
    ax.set_ylabel("Model/infrastructure cost per accepted outcome (USD)")
    ax.set_title("Local capacity wins only when utilization and acceptance are high enough", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(fig, "fig07_local_cloud_break_even")


def build_capacity_results(assumptions: dict) -> pd.DataFrame:
    before = assumptions["capacity"]["before"]
    after = assumptions["capacity"]["after_verifier_investment"]
    rows = []
    for stage in before:
        rows.append({"stage": stage, "before": before[stage], "after": after[stage]})
    return pd.DataFrame(rows)


def figure_bottleneck(capacity_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.7))
    x = np.arange(len(capacity_df))
    w = 0.38
    bars1 = ax.bar(x - w / 2, capacity_df["before"], width=w, label="Before verifier investment")
    bars2 = ax.bar(x + w / 2, capacity_df["after"], width=w, label="After verifier investment")
    ax.set_xticks(x, capacity_df["stage"])
    ax.set_ylabel("Sustainable accepted-change capacity per month")
    ax.set_title("Generation is not throughput: the bottleneck migrates", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    min_before = capacity_df.loc[capacity_df["before"].idxmin()]
    min_after = capacity_df.loc[capacity_df["after"].idxmin()]
    ax.annotate(f"Constraint: {min_before.stage} ({min_before.before})",
                (capacity_df.index[capacity_df.stage == min_before.stage][0] - w / 2, min_before.before),
                xytext=(-15, -35), textcoords="offset points", arrowprops={"arrowstyle": "->"}, fontsize=9)
    ax.annotate(f"New constraint: {min_after.stage} ({min_after.after})",
                (capacity_df.index[capacity_df.stage == min_after.stage][0] + w / 2, min_after.after),
                xytext=(10, -45), textcoords="offset points", arrowprops={"arrowstyle": "->"}, fontsize=9)
    save_figure(fig, "fig08_bottleneck_migration")


def figure_verification_leverage(assumptions: dict) -> float:
    v = assumptions["verification_investment"]
    benefits = v["quarterly_rework_reduction_usd"] + v["quarterly_expected_failure_reduction_usd"]
    leverage = benefits / v["quarterly_cost_usd"]
    costs = np.linspace(5_000, 100_000, 200)
    lev = benefits / costs
    fig, ax = plt.subplots(figsize=(9.4, 5.3))
    ax.plot(costs / 1000, lev, linewidth=2.4)
    ax.axhline(1, linestyle="--", linewidth=1.5, label="Direct break-even")
    ax.scatter([v["quarterly_cost_usd"] / 1000], [leverage], s=70, zorder=4)
    ax.annotate(f"Case: {leverage:.1f}x", (v["quarterly_cost_usd"] / 1000, leverage),
                xytext=(8, 8), textcoords="offset points")
    ax.set_xlabel("Quarterly verifier cost (thousand USD)")
    ax.set_ylabel("Verification leverage")
    ax.set_title("Verification is productive capital when prevented loss exceeds its cost", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    save_figure(fig, "fig09_verification_leverage")
    return leverage


def figure_control_loop() -> None:
    fig, ax = plt.subplots(figsize=(9.7, 6.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")
    nodes = {
        "Economic hypothesis\nand task boundary": (5, 6.0, "#dcecff"),
        "Route and execute\nwithin budget": (8.2, 3.8, "#f2e5ff"),
        "Independent evidence\nand authorization": (6.8, 0.9, "#fff0cf"),
        "Deploy, observe,\nmeasure value": (3.2, 0.9, "#ddf3df"),
        "Portfolio allocation,\npolicy and human guardrails": (1.8, 3.8, "#ffe1df"),
    }
    centers = {}
    for label, (cx, cy, color) in nodes.items():
        w, h = 2.45, 1.05
        box = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                             boxstyle="round,pad=0.04,rounding_size=0.08",
                             facecolor=color, edgecolor="#343a40", linewidth=1.4)
        ax.add_patch(box)
        ax.text(cx, cy, label, ha="center", va="center", fontsize=10, fontweight="bold")
        centers[label] = (cx, cy)
    ordered = list(nodes.keys())
    for a, b in zip(ordered, ordered[1:] + ordered[:1]):
        ax.add_patch(FancyArrowPatch(centers[a], centers[b], arrowstyle="->", mutation_scale=15,
                                     connectionstyle="arc3,rad=0.04", lw=1.5,
                                     shrinkA=38, shrinkB=38))
    ax.add_patch(FancyArrowPatch((7.55, 1.45), (8.05, 3.25), arrowstyle="->", mutation_scale=14,
                                 linestyle="--", connectionstyle="arc3,rad=-0.30",
                                 shrinkA=6, shrinkB=8))
    ax.text(9.1, 2.2, "retry with evidence,\nswitch route or escalate", ha="center", fontsize=8.5)
    ax.text(5, 3.25, "Outcome telemetry updates\nroutes, budgets and portfolio",
            ha="center", va="center", fontsize=9.0, fontweight="bold",
            bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": "#adb5bd", "alpha": 0.97})
    save_figure(fig, "fig10_economic_control_loop")


def monte_carlo(assumptions: dict, samples: int = 100_000, seed: int = 20260724) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    counts = assumptions["pilot_counts_for_uncertainty"]
    # Uniform Beta(1,1) prior; posterior after illustrative pilot counts.
    p1 = rng.beta(counts["local_first"]["successes"] + 1,
                  counts["local_first"]["trials"] - counts["local_first"]["successes"] + 1, samples)
    p2 = rng.beta(counts["local_retry"]["successes"] + 1,
                  counts["local_retry"]["trials"] - counts["local_retry"]["successes"] + 1, samples)
    p3 = rng.beta(counts["opus_escalation"]["successes"] + 1,
                  counts["opus_escalation"]["trials"] - counts["opus_escalation"]["successes"] + 1, samples)
    cas = assumptions["cascade"]

    def lognormal_around(mean: float, cv: float = 0.15) -> np.ndarray:
        sigma2 = math.log(1 + cv * cv)
        mu = math.log(mean) - sigma2 / 2
        return rng.lognormal(mu, math.sqrt(sigma2), samples)

    a1 = lognormal_around(cas["local_first"]["automatic_attempt_cost_usd"])
    s1 = lognormal_around(cas["local_first"]["success_review_and_residual_risk_usd"])
    a2 = lognormal_around(cas["local_verifier_guided_retry"]["automatic_attempt_cost_usd"])
    s2 = lognormal_around(cas["local_verifier_guided_retry"]["success_review_and_residual_risk_usd"])
    a3 = lognormal_around(cas["opus_escalation"]["automatic_attempt_cost_usd"])
    s3 = lognormal_around(cas["opus_escalation"]["success_review_and_residual_risk_usd"])
    human = lognormal_around(assumptions["task_cohort"]["human_escalation_after_machine_usd"], cv=0.20)
    result = (
        a1 + p1 * s1
        + (1 - p1) * (a2 + p2 * s2)
        + (1 - p1) * (1 - p2) * (a3 + p3 * s3)
        + (1 - p1) * (1 - p2) * (1 - p3) * human
    )
    summary = {
        "samples": samples,
        "mean_usd": float(np.mean(result)),
        "median_usd": float(np.median(result)),
        "p10_usd": float(np.quantile(result, 0.10)),
        "p90_usd": float(np.quantile(result, 0.90)),
        "p95_usd": float(np.quantile(result, 0.95)),
    }
    pd.DataFrame({"simulated_expected_cost_usd": result}).to_csv(OUT / "monte_carlo_draws.csv", index=False)
    return pd.DataFrame([summary])


def write_macros(context_df: pd.DataFrame, routes: pd.DataFrame, policy_df: pd.DataFrame,
                 break_even: pd.DataFrame, capacity: pd.DataFrame, leverage: float,
                 monte: pd.DataFrame, assumptions: dict) -> None:
    context_map = context_df.set_index("policy")["model_cost_usd"].to_dict()
    route_map = routes.set_index("route")["cost_per_accepted_usd"].to_dict()
    policy_map = policy_df.set_index("policy")["expected_cost_usd"].to_dict()
    be_map = break_even.set_index("cloud_route")["break_even_tasks_per_month"].to_dict()
    human_baseline = assumptions["task_cohort"]["human_hours_per_task"] * assumptions["task_cohort"]["human_hourly_cost_usd"]
    cascade = policy_map["Local-local-Opus cascade"]
    savings = (1 - cascade / human_baseline) * 100
    before_min = int(capacity["before"].min())
    after_min = int(capacity["after"].min())
    macro_lines = [
        "% Generated by ai_economics_model.py -- do not edit manually.",
        f"\\newcommand{{\\SnapshotDate}}{{24 July 2026}}",
        f"\\newcommand{{\\FullReplayCost}}{{{context_map['Full history replay']:.2f}}}",
        f"\\newcommand{{\\CompactionCost}}{{{context_map['Compaction']:.2f}}}",
        f"\\newcommand{{\\FreshStateCost}}{{{context_map['Fresh context + external state']:.2f}}}",
        f"\\newcommand{{\\LocalAcceptedCost}}{{{route_map['Local Qwen3.6-27B']:.2f}}}",
        f"\\newcommand{{\\GeminiAcceptedCost}}{{{route_map['Gemini 3.6 Flash']:.2f}}}",
        f"\\newcommand{{\\SonnetAcceptedCost}}{{{route_map['Claude Sonnet 5']:.2f}}}",
        f"\\newcommand{{\\OpusAcceptedCost}}{{{route_map['Claude Opus 4.8']:.2f}}}",
        f"\\newcommand{{\\HumanBaselineCost}}{{{human_baseline:.2f}}}",
        f"\\newcommand{{\\CascadeExpectedCost}}{{{cascade:.2f}}}",
        f"\\newcommand{{\\CascadeSavingsPercent}}{{{savings:.1f}}}",
        f"\\newcommand{{\\MonteCarloMedian}}{{{monte.iloc[0].median_usd:.2f}}}",
        f"\\newcommand{{\\MonteCarloPten}}{{{monte.iloc[0].p10_usd:.2f}}}",
        f"\\newcommand{{\\MonteCarloPninety}}{{{monte.iloc[0].p90_usd:.2f}}}",
        f"\\newcommand{{\\LocalBreakEvenGemini}}{{{be_map['Gemini 3.6 Flash']:.0f}}}",
        f"\\newcommand{{\\LocalBreakEvenSonnet}}{{{be_map['Claude Sonnet 5']:.0f}}}",
        f"\\newcommand{{\\LocalBreakEvenOpus}}{{{be_map['Claude Opus 4.8']:.0f}}}",
        f"\\newcommand{{\\ThroughputBefore}}{{{before_min}}}",
        f"\\newcommand{{\\ThroughputAfter}}{{{after_min}}}",
        f"\\newcommand{{\\VerificationLeverage}}{{{leverage:.1f}}}",
    ]
    (SRC / "generated_values.tex").write_text("\n".join(macro_lines) + "\n", encoding="utf-8")


def main() -> None:
    prices, assumptions = load_inputs()
    figure_unit_of_account()
    context_df = figure_context_cost(prices, assumptions)
    session_df = model_session_costs(prices, assumptions)
    figure_model_session_cost(session_df)
    routes = build_route_results(prices, assumptions, session_df)
    figure_candidate_stack(routes)
    figure_cost_per_accepted(routes)
    policy_df = build_policy_results(assumptions)
    figure_retry_policy(policy_df)
    curves, break_even = build_break_even(prices, assumptions, session_df)
    figure_break_even(curves, break_even)
    capacity = build_capacity_results(assumptions)
    figure_bottleneck(capacity)
    leverage = figure_verification_leverage(assumptions)
    figure_control_loop()
    monte = monte_carlo(assumptions)

    context_df.to_csv(OUT / "context_policy_results.csv", index=False)
    session_df.to_csv(OUT / "model_session_costs.csv", index=False)
    routes.to_csv(OUT / "standalone_route_results.csv", index=False)
    policy_df.to_csv(OUT / "retry_policy_results.csv", index=False)
    break_even.to_csv(OUT / "local_cloud_break_even.csv", index=False)
    capacity.to_csv(OUT / "capacity_results.csv", index=False)
    monte.to_csv(OUT / "monte_carlo_summary.csv", index=False)

    write_macros(context_df, routes, policy_df, break_even, capacity, leverage, monte, assumptions)

    summary = {
        "context": context_df.to_dict(orient="records"),
        "model_session_costs": session_df.to_dict(orient="records"),
        "standalone_routes": routes.to_dict(orient="records"),
        "retry_policies": policy_df.to_dict(orient="records"),
        "break_even": break_even.to_dict(orient="records"),
        "capacity": capacity.to_dict(orient="records"),
        "verification_leverage": leverage,
        "monte_carlo": monte.to_dict(orient="records")[0],
    }
    (OUT / "results_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
