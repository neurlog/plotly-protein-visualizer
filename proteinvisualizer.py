import os
import sys
import pandas as pd
from biopandas.pdb import PandasPdb
import plotly.express as px

# Colour modes
COLOR_MODES = [
    "element_symbol",
    "residue_number",
    "residue_name",
    "b_factor",
    "atom_name",
]

# Main function stuff
def load_pdb(path: str) -> PandasPdb:
    if not os.path.isfile(path):
        sys.exit(f"[ERROR] File not found: {path}")
    if not path.lower().endswith(".pdb"):
        print(f"[WARNING] File does not have a .pdb extension: {path}")
    print(f"\n[INFO] Loading {path} ...")
    pdb = PandasPdb().read_pdb(path)

    atom_df = pdb.df.get("ATOM")
    if atom_df is None or atom_df.empty:
        sys.exit("[ERROR] No ATOM records found in the PDB file.")

    print(f"{len(atom_df):,} ATOM records loaded.")
    print(f"Residues : {atom_df['residue_number'].nunique()}")
    print(f"Chains   : {atom_df['chain_id'].unique().tolist()}")
    print(f"Elements : {sorted(atom_df['element_symbol'].dropna().unique().tolist())}")
    return pdb

# Figures
def build_figure(atom_df: pd.DataFrame, color: str, title: str, template: str, color_scale: str = "Plotly3"):
    if color not in atom_df.columns:
        sys.exit(
            f"[ERROR] Column '{color}' not found in ATOM DataFrame.\n"
            f"Available columns: {list(atom_df.columns)}"
        )

    fig = px.scatter_3d(
        atom_df,
        x="x_coord",
        y="y_coord",
        z="z_coord",
        color=color,
        hover_data=["atom_name", "residue_name", "residue_number", "chain_id"],
        title=title,
        labels={
            "x_coordinates": "X (Å)",
            "y_coordinates": "Y (Å)",
            "z_coordinates": "Z (Å)",
        },
        color_continuous_scale=color_scale,
    )

    fig.update_traces(marker=dict(size=4, opacity=0.85))
    fig.update_layout(
        template=template,
        height=800,
        title=dict(font=dict(size=20)),
        scene=dict(
            xaxis_title="X (Å)",
            yaxis_title="Y (Å)",
            zaxis_title="Z (Å)",
        ),
        legend=dict(title=color.replace("_", " ").title()),
    )
    return fig

# Brief summary of atom records
def print_summary(atom_df: pd.DataFrame) -> None:
    print("\n── ATOM DataFrame summary ──────────────────────────")
    print(f"  Shape       : {atom_df.shape}")
    print(f"  X range     : {atom_df['x_coord'].min():.2f} → {atom_df['x_coord'].max():.2f} Å")
    print(f"  Y range     : {atom_df['y_coord'].min():.2f} → {atom_df['y_coord'].max():.2f} Å")
    print(f"  Z range     : {atom_df['z_coord'].min():.2f} → {atom_df['z_coord'].max():.2f} Å")
    if "b_factor" in atom_df.columns:
        print(f"  B-factor    : mean={atom_df['b_factor'].mean():.2f}, "
              f"min={atom_df['b_factor'].min():.2f}, "
              f"max={atom_df['b_factor'].max():.2f}")
    print("────────────────────────────────────────────────────\n")

def save_html(fig, output_path: str) -> None:
    fig.write_html(output_path, include_plotlyjs="cdn")
    print(f"Saved → {output_path}")

def prompt_file_path() -> str:
    print("=" * 50)
    print("   PDB 3D Protein Structure Visualizer")
    print("=" * 50)
    path = input("\nEnter the path to your .pdb file:\n> ").strip().strip("'\"")
    if not path:
        sys.exit("[ERROR] No path entered. Exiting.")
    return path

def prompt_color_mode() -> str:
    print("Colour modes available:")
    for i, mode in enumerate(COLOR_MODES, 1):
        print(f"  {i}. {mode}")
    print(f"  {len(COLOR_MODES) + 1}. All (saves each as a separate HTML file)")

    choice = input(
        f"\nChoose a colour mode [1–{len(COLOR_MODES) + 1}] "
        f"(default: residue_number):\n> "
    ).strip()

    if choice == "":
        return "residue_number"
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(COLOR_MODES):
            return COLOR_MODES[idx]
        if idx == len(COLOR_MODES):
            return "all"
    print("[WARNING] Invalid choice — using default: residue_number")
    return "residue_number"

def prompt_background() -> str:
    ans = input("\nChoose a white or black figure background? [w/b] "
                "(default: black):\n> ").strip().lower()
    if ans in ("white", "w"):
        return "plotly"
    if ans in ("black", "b"):
        return "plotly_dark"
    if ans != "":
        print("[WARNING] Invalid choice — using default: black")
    return "plotly_dark"

COLOR_SCALES = ["Plotly3", "Viridis", "Plasma", "Bluered", "Rainbow"]

def prompt_color_scale() -> str:
    print("\nDot colour theme options:")
    for i, scale in enumerate(COLOR_SCALES, 1):
        print(f"  {i}. {scale}")

    choice = input(
        f"\nChoose a dot colour scale [1–{len(COLOR_SCALES)}] "
        f"(default: Plotly3):\n> "
    ).strip()

    if choice == "":
        return "Plotly3"
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(COLOR_SCALES):
            return COLOR_SCALES[idx]
    print("[WARNING] Invalid choice — using default: Plotly3")
    return "Plotly3"

def prompt_save() -> bool:
    ans = input("\nSave as HTML file instead of opening in browser? [y/n]:\n> ").strip().lower()
    return ans in ("y", "yes")

# Main
def main() -> None:
    pdb_file = prompt_file_path()
    pdb = load_pdb(pdb_file)
    atom_df = pdb.df["ATOM"]
    print_summary(atom_df)

    color_choice = prompt_color_mode()
    template = prompt_background()

    # Color scale prompt only for numeric colour modes (residue_number, b_factor, all)
    if color_choice in ("residue_number", "b_factor", "all"):
        color_scale = prompt_color_scale()
    else:
        color_scale = "Plotly3"

    base_name = os.path.splitext(os.path.basename(pdb_file))[0]
    base_title = f"Protein Structure — {base_name}"

    if color_choice == "all":
        print("\nRendering all colour modes and saving as HTML ...")
        for mode in COLOR_MODES:
            title = f"{base_title} | coloured by {mode.replace('_', ' ').title()}"
            fig = build_figure(atom_df, color=mode, title=title, template=template, color_scale=color_scale)
            out = f"{base_name}_{mode}.html"
            save_html(fig, out)
        print("Done. Open the .html files in any browser.")
    else:
        save = prompt_save()
        title = f"{base_title} | {color_choice.replace('_', ' ').title()}"
        fig = build_figure(atom_df, color=color_choice, title=title, template=template, color_scale=color_scale)

        if save:
            out = f"{base_name}_{color_choice}.html"
            save_html(fig, out)
        else:
            print("Opening interactive plot in browser ...")
            fig.show()

if __name__ == "__main__":
    main()
