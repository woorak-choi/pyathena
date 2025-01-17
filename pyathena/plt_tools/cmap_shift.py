
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

def cmap_shift(cmap, start=0.0, midpoint=0.5, stop=1.0, name='shiftedcmap'):
    """Function to offset the center of a colormap. Useful for data with a
    negative min and positive max and you want the middle of the colormap's
    dynamic range to be at zero.

    Parameters
    ----------
    cmap : matplotlib colormap
        Colormap to be modified
    start : float
        Offset from lowest point in the colormap's range. Should be between 0.0
        and `midpoint`. Default value is 0.0 (no lower ofset).
    midpoint : float
        New center of the colormap. Should be between 0.0 and 1.0. In general,
        this should be 1 - vmax/(vmax + abs(vmin)). For example, if the data
        ranges from -15.0 to +5.0 and you want the center of the colormap at
        0.0, `midpoint` should be set to 1 - 5/(5 + 15)) or 0.75. Default value
        is 0.5 (no shift).
    stop : float
        Offset from highets point in the colormap's range. Should be between
        `midpoint` and 1.0. Default value is 1.0 (no upper ofset).

    Returns
    -------
    cmap_new : matplotlib colormap
        New colormap
    """

    cdict = dict(red=[], green=[], blue=[], alpha=[])

    # regular index to compute the colors
    reg_index = np.linspace(start, stop, 257)

    # shifted index to match the data
    shift_index = np.hstack([
        np.linspace(0.0, midpoint, 128, endpoint=False),
        np.linspace(midpoint, 1.0, 129, endpoint=True)
    ])

    for ri, si in zip(reg_index, shift_index):
        r, g, b, a = cmap(ri)
        cdict['red'].append((si, r, r))
        cdict['green'].append((si, g, g))
        cdict['blue'].append((si, b, b))
        cdict['alpha'].append((si, a, a))

    cmap_new = matplotlib.colors.LinearSegmentedColormap(name, cdict)
    #plt.register_cmap(cmap=cmap_new)

    return cmap_new

