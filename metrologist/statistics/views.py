"""
Compute and save statistic outputs into static/img
Functions are provided by functions.py on the same dir.

Here we limit our program to extract cv_values of a given
microscope id from Cv table and show results as barplot. 

Note: As statistic figures are of temporary use, we will not consider
saving them into database. We consider them as temporary files. 
"""
from flask import Blueprint, render_template
import metrologist.statistics.functions  as fct
from pathlib import Path

blueprint = Blueprint(
    "statistics", __name__, url_prefix="/statistics", static_folder="../static"
)
PARENT2 = Path(__file__).resolve().parents[2]
@blueprint.route("/")

def statistics():
    # 0. inputs: selections from user
    # in fine, this should be a pop-up window with scroll options to chose from
    microscope_id = 12121212
    metroloj_report_table_name = "Cv"
    names_colname = "created_at"
    param_colname = "cv_table_cv_value"

    # 1. data wrangling: extract values from database
    """to active if provided microscope id
    cv_values =fct.get_col_from_db(microscope_id,
                                metroloj_report_table_name,
                                param_colname)
    """
    # vales for test
    dates = ["01/02/2022","10/02/2022","01/04/2022","21/04/2022","01/04/2022"]
    cv_values = [0.9,0.85,0.81,0.59,0.50]

    # 2. data vizualisation: values into barplot
    graph_path_temp = str(PARENT2) +  "/assets/img/"
    build_path_temp = "build/img/"
    cv_values_barplot_path = graph_path_temp + "cv_values_barplot.png"
    cv_values_barplot_build_path = build_path_temp + "cv_values_barplot.png"

    fct.values_to_barplot(
        microscope_id,
        dates,
        cv_values,
        xlab="date of creation",
        ylab="cv values",
        plot_title="cv values",
        save_path=cv_values_barplot_path
        )

    return render_template(
        "statistics/statistics.html",
        cv_values_barplot_path=cv_values_barplot_build_path
    )
