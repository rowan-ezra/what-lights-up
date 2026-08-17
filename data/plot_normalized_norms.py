import pandas as pd
import matplotlib.pyplot as plt

# --- 1. Load ---
df = pd.read_csv("residual_norms.csv")

# GPT's CSV uses this explicit column name.
df = df.rename(columns={"resid_post_final_token_norm": "norm"})

# Keep token ranges in logical order instead of alphabetical weirdness.
range_order = ["8-10", "20-25", "30-40"]

# --- 2. Normalize: each norm / cross-condition mean at that layer and range ---
df["norm_rel"] = df["norm"] / df.groupby(["layer", "range"])["norm"].transform("mean")

# Now 1.0 = average for this layer/range.
# 1.05 = 5% above that layer/range average.

# --- 3. Plot: one panel per token range ---
fig, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=True)

for ax, rng in zip(axes, range_order):
    sub = df[df["range"] == rng]

    for cond, grp in sub.groupby("condition"):
        grp = grp.sort_values("layer")
        ax.plot(grp["layer"], grp["norm_rel"], label=cond, marker=".", ms=3)

    ax.axhline(1.0, color="gray", lw=0.5, ls="--")
    ax.set_title(f"Tokens: {rng}")
    ax.set_xlabel("Layer")

axes[0].set_ylabel("Norm / layer-range mean")
axes[0].legend(fontsize=7)

plt.tight_layout()
plt.savefig("norms_normalized.png", dpi=150)
print("Saved norms_normalized.png")