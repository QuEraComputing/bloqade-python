Use_bokeh = True

if Use_bokeh:
    from .display import display_ir, display_report, display_task_ir, display_builder
else:

    def display_ir(obj, assignemnts):
        raise Warning("Bokeh not installed", UserWarning)

    def display_report(report):
        raise Warning("Bokeh not installed", UserWarning)

    def display_task_ir(task_ir):
        raise Warning("Bokeh not installed", UserWarning)

    def display_builder(builder, batch_id):
        raise Warning("Bokeh not installed", UserWarning)
