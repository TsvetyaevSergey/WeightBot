from pathlib import Path
from typing import Dict, List
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import CHARTS_DIR, USERS

import matplotlib.dates as mdates

def build_weight_chart(all_weights: List[dict], start_date_iso: str) -> str:
    out_dir = Path(CHARTS_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "weights.png"

    series: Dict[str, Dict[str, float]] = {k: {} for k in USERS.keys()}
    for rec in all_weights:
        series[rec["user_key"]][rec["date"]] = float(rec["weight"])

    plt.figure(figsize=(9, 5), dpi=150)
    for key, title in USERS.items():
        if not series[key]:
            continue
        dates = sorted(series[key].keys())
        xs = [datetime.fromisoformat(d) for d in dates]
        ys = [series[key][d] for d in dates]
        plt.plot(xs, ys, marker="o", label=title)

    plt.title("Динамика веса (с начала испытания)")
    plt.xlabel("Дата")
    plt.ylabel("Вес, кг")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()

    # Формат оси X
    ax = plt.gca()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return str(out_path)

