import os
import json
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd

from typing import List, Union, Optional
from pathlib import Path
from scipy.stats import gaussian_kde
from pymol import cmd

plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'Arial'
mpl.rcParams['lines.linewidth'] = 1

def motif_scaffolding_pymol_write(
    unique_designable_backbones: Union[str, Path],
    native_backbones: Union[str, Path],
    motif_json: Union[str, Path],
    save_path: Union[str, Path],
    native_motif_color: Optional[str] = "tellurium",
    design_motif_color: Optional[str] = "smudge",
    design_scaffold_color: Optional[str] = "rhenium"
    ):
    """
    Extract unique designable backbones, visualize the motifs and
    save them into a PyMol session file.

    Authored by: Bo Zhang
    """

    unique_designable_backbones_pdb = [i.replace(".pdb","") for i in os.listdir(unique_designable_backbones) if i.endswith('.pdb')]
    native_pdb = f"{native_backbones}/{unique_designable_backbones_pdb[0].split('_')[0]}.pdb"
    with open(motif_json,"r") as f:
        info = json.load(f)
    design_name_motif = {}
    for i in unique_designable_backbones_pdb:
        design_name_motif[i] = info[i]["motif_idx"]
    # re-initialize the pymol
    cmd.reinitialize()
    cmd.load(native_pdb, "native_pdb")
    contig = list(info.values())[0]["contig"]
    # "contig": "31-31/B25-46/32-32/A32/A4/A5"
    contig_list = [i for i in contig.split("/") if not i[0].isdigit()]
    config_folder = []
    for i in contig_list:
        chain = i[0]
        i = i[1:]
        if "-" in i:
            element = i.split("-")
            start = element[0]
            end = element[1]
            select = f"resi {start}-{end} and chain {chain}"
            config_folder.append(select)
        else:
            select = f"resi {i[1:]} and chain {chain}"
            config_folder.append(select)
    # merge all the contig into one
    config_extract = " or ".join(config_folder)
    print(f"loading native motif {config_extract}")

    cmd.extract("native_motif",config_extract)
    # delete native_pdb 
    cmd.delete("native_pdb")
    # color the native motif of PDB
    cmd.color(native_motif_color,"native_motif")
    cmd.show("sticks","native_motif")
    
    for i in os.listdir(unique_designable_backbones):
        print(i)
        if i.endswith(".pdb"):
            name = i.split(".")[0]
            cmd.load(f"{unique_designable_backbones}/{i}",name)
            cmd.color(design_scaffold_color,name)
            motif_residue = design_name_motif[name]
            cmd.select(f"{name}_motif","resi "+"+".join([str(i) for i in motif_residue])+" and "+name)
            cmd.color(design_motif_color,f"{name}_motif")
            cmd.show("sticks",f"{name}_motif")
            # align the motif
            cmd.align(f"{name}","native_motif")

    cmd.bg_color('white')
    # set grid_mode to 1
    cmd.set("grid_mode",1)
    # zoom on the {name}
    cmd.zoom(f"{name}")
    cmd.save(save_path)


import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from typing import *
from pathlib import Path
from scipy.stats import gaussian_kde

#plt.rcParams['font.sans-serif'] = 'Arial'
#plt.rcParams['font.family'] = 'Arial'
#mpl.rcParams['lines.linewidth'] = 1


def truncate_colormap(cmap, min_val=0.0, max_val=1.0, n=100):
    """ Truncate a colormap to use a fraction of it. """
    new_cmap = mpl.colors.LinearSegmentedColormap.from_list(
        f'trunc({cmap.name},{min_val:.2f},{max_val:.2f})',
        cmap(np.linspace(min_val, max_val, n)))
    return new_cmap


@mpl.rc_context({'lines.linewidth': 1, 'font.family': 'Arial', 'font.sans-serif': 'Arial'})
def plot_metrics_distribution(
    input: Union[str, Path, pd.DataFrame],
    save_path: Union[str, Path],
    save_mode: Literal['png', 'pdf', 'svg'] = 'png',
    dpi: Union[int, float] = 800
    ) -> str:
    results = pd.read_csv(input) if isinstance(input, (str or Path)) else input
    
    # Calculate sequence hit
    #results['seq_hit'] = results['seq_hit'].astype(int)
    #print(results['seq_hit'])
    #mean_seq_hit = results.groupby("backbone_path")["seq_hit"].mean().reset_index(name="mean_seq_hit").mean()
    
    # Set up the figure with main axes and marginal axes
    fig = plt.figure(figsize=(10, 10))
    
    # Main 2D plot
    ax_main = fig.add_axes([0.1, 0.1, 0.65, 0.65])
    
    # Marginal axes for histograms
    ax_histx = fig.add_axes([0.1, 0.76, 0.65, 0.2], sharex=ax_main)
    ax_histy = fig.add_axes([0.8, 0.25, 0.25, 0.65], sharey=ax_main)
    
    truncated_cmap = truncate_colormap(plt.get_cmap('PuBu'), min_val=0.1, max_val=1.0)

    # Main hexbin plot (motif_rmsd on x-axis, rmsd on y-axis)
    hb = ax_main.hexbin(results['motif_rmsd'], results['rmsd'], gridsize=30, cmap=truncated_cmap, mincnt=1)
    ax_main.set_xlabel('Motif-RMSD (Å)', fontweight='bold', fontsize=12)
    ax_main.set_ylabel('Backbone-RMSD (Å)', fontweight='bold', fontsize=12)
    
    # Add a color bar
    cb = fig.colorbar(hb, ax=ax_main, orientation="horizontal", pad=0.1)
    cb.set_label('Counts', fontweight='bold')

    # Marginal histogram on the top for motif_rmsd
    ax_histx.hist(results['motif_rmsd'], bins=50, color='#0888B5', alpha=0.6, density=True, edgecolor='black')
    ax_histx.axis('off')  # Hide ticks and labels
    
    # Marginal histogram on the right for rmsd
    ax_histy.hist(results['rmsd'], bins=50, color='#EE8400', alpha=0.6, density=True, orientation='horizontal', edgecolor='black')
    ax_histy.axis('off')  # Hide ticks and labels

    # Add KDE curves to the histograms
    motif_rmsd_kde = gaussian_kde(results['motif_rmsd'])
    rmsd_kde = gaussian_kde(results['rmsd'])

    x_motif = np.linspace(results['motif_rmsd'].min(), results['motif_rmsd'].max(), 100)
    x_rmsd = np.linspace(results['rmsd'].min(), results['rmsd'].max(), 100)
    
    ax_histx.fill_between(x_motif, motif_rmsd_kde(x_motif), color='#0888B5', lw=1.5, alpha=0.4)
    ax_histy.fill_between(rmsd_kde(x_rmsd), x_rmsd, color='#EE8400', lw=1.5, alpha=0.4)
    
    ax_main.spines['top'].set_visible(False)
    ax_main.spines['right'].set_visible(False)
    
    ax_main.axhline(2.0, color='#EE8400', linestyle="--", linewidth=2)
    ax_main.axvline(1.0, color='#0888B5', linestyle="--", linewidth=2)

    #plt.show()
    plt.savefig(os.path.join(save_path, f'metric_distribution.{save_mode}'), dpi=dpi)
    
    #return mean_seq_hit