"""
Functions to extract data from database
And build visuals to render 

The user must provide:
1. microscope id (choose from microscope.id column)
2. the report containing the parameter to investigate
3. the parameter to investigate

Here we limit our program to extract cv_values of a given
microscope id from Cv table and show results as barplot. 
"""

from metrologist.extensions import db
import matplotlib.pylab as plt


def get_col_from_db(microscope_id, table_name, colname):
    """
    This function realise a SELECT query to extract one single microscope
    quality assessement parameter of a specific microscope.

    Args:
        microscope_id (int):
            Chose from the list of database microscopes.
        table_name (str):
            Table name of the report containing the parameter to investigate.
        colname (str):
            Among table columns, chose the parameter to investigate,
            i.e. column name.
    Returns:
        list: list of 
    """
    values = db.session.query(table_name).filter_by(name=microscope_id).values(colname)
    # dict to list
    values = list(values.values())[0]
    return values


def values_to_barplot(
    microscope_id, xvalues, yvalues, plot_title,
    xlab=None, ylab=None, save_path=None
    ):
    """
    This function display a list of values on a horizontal barplot.

    Args:
        microscope_id (int):
            Chose from the list of database microscopes.
        xvalues (list):
            x_axis list of elements, i.g. date of image aquisition.
        yvalues (list):
            list of the chosen parameter values of a specific microscope.
        xlab (str):
            x axis label.
        ylab (str):
            y axis label.
        plot_title (str):
            plot title
        save_path (str):
            path to save the generated figure including filename.
            Default is None.
    """

    fig, ax = plt.subplots()
    ax.bar(xvalues, yvalues)

    # Remove axes splines
    for s in ['top', 'bottom', 'left', 'right']:
        ax.spines[s].set_visible(False)
    # Remove x, y Ticks
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')

    # Add padding between axes and labels
    ax.xaxis.set_tick_params(pad = 5)
    ax.yaxis.set_tick_params(pad = 10)
    
    # Add x, y gridlines
    ax.grid(b = True, color ='grey',
            linestyle ='-.', linewidth = 0.5,
            alpha = 0.2)
    
    # Show oldest to newest images
    # ax.invert_yaxis()
    
    # Add annotation to bars
    """
    for i in ax.patches:
        plt.text(i.get_width()+0.2, i.get_y()+0.5,
                str(round((i.get_width()), 2)),
                fontsize = 10, fontweight ='bold',
                color ='grey')
    """
    
    # Add Plot Title
    ax.set_title(f"parameter: {plot_title}\n microscope id: {microscope_id}",
                 loc ='center')

    # Add x and y labels (optional)
    if xlab:
        plt.xlabel(xlab, fontsize=12, labelpad=10)
    if ylab:
        plt.ylabel(ylab, fontsize=12, labelpad=10)

    # Save (optional)
    if save_path:
        plt.savefig(str(save_path),
                    bbox_inches='tight')
