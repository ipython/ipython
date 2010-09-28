""" Provides basic funtionality for payload backends.
"""

# Local imports.
from IPython.core.interactiveshell import InteractiveShell


def add_plot_payload(format, data, metadata={}):
    """ Add a plot payload to the current execution reply.

    Parameters:
    -----------
    format : str
        Identifies the format of the plot data.

    data : str
        The raw plot data.

    metadata : dict, optional [default empty]
        Allows for specification of additional information about the plot data.
    """
    payload = dict(
        source='IPython.zmq.pylab.backend_payload.add_plot_payload', 
        format=format, data=data, metadata=metadata
    )
    InteractiveShell.instance().payload_manager.write_payload(payload)
