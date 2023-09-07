Use_bokeh = True

if Use_bokeh:
    from .display import display_ir, display_report, display_task_ir, display_builder
    from .task_visualize import get_task_ir_figure

    # from .atom_arragement_visualize import get_atom_arrangement_figure
else:
    # display
    def display_ir(obj, assignemnts):
        raise Warning("Bokeh not installed", UserWarning)

    def display_report(report):
        raise Warning("Bokeh not installed", UserWarning)

    def display_task_ir(task_ir):
        raise Warning("Bokeh not installed", UserWarning)

    def display_builder(builder, batch_id):
        raise Warning("Bokeh not installed", UserWarning)

    # visualization
    def get_task_ir_figure(task_ir, **fig_kwargs):
        raise Warning("Bokeh not installed", UserWarning)

    # atom arrangement
    # def get_atom_arrangement_figure(atom_arng_ir, fig_kwargs=None, **assignments):
    #    raise Warning("Bokeh not installed", UserWarning)
