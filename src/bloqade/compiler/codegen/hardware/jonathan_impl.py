import numpy as np


def __row_cluster(points0: np.ndarray, threshold: float, plotit=False):
    """
    Clusters points in 1 dimension using tree clustering
    points0 - Initial points
    threshold - The minimum distance between clusters
    """

    assert len(points0.shape) == 1, "Data must be 1 dimensional"
    assert np.isreal(points0).all(), "Data must be real"

    points = np.copy(points0)
    weights = np.ones(len(points))
    generation = np.zeros(len(points))

    i = 0
    for ctr in range(len(points0) - 1):
        dists = abs(points.reshape(len(points), 1) - points.reshape(1, len(points)))
        dists[range(len(points)), range(len(points))] = np.inf

        if dists.min() >= threshold:
            break

        i += dists.min()

        mindist = np.unravel_index(np.argmin(dists), dists.shape)
        points[[mindist[0], mindist[1]]]

        newpt = (
            points[mindist[0]] * weights[mindist[0]]
            + points[mindist[1]] * weights[mindist[1]]
        ) / (weights[mindist[0]] + weights[mindist[1]])
        newwt = weights[mindist[0]] + weights[mindist[1]]

        points = np.concatenate((np.delete(points, mindist), [newpt]))
        weights = np.concatenate((np.delete(weights, mindist), [newwt]))
        generation = np.concatenate((np.delete(generation, mindist), [i]))

    return points


def rowify(points0: np.ndarray, horizontal_threshold: float, row_threshold: float):
    """
    "Rowifys" a set of points to obey the row and minimum spacing constraint.
    INPUTS
    points - locations of vertices of some graph or other geometric object
    horizontal_threshold - Minimum horizontal spacing between atoms in the same row
    row_threshold - Minimum vertical (row) spacing between rows.

    RETURNS
    positions     - Positions of each atom in the array
    assignments_F - "Forward" assignements; a list indexed by vertex, with values of the atom index.
                       Note that multiple vertices may be assigned to a single atom (many-to-one)
    assignments_R - "Reverse" assignements; A dict indexed by atom number, with values as a list of
                       every vertex assigned to that atom.
    ERROR_OUT - The average root-mean-square error between vertex positions and atom positions

    """

    assert len(points0.shape) == 2, "Data must be 2d"
    assert points0.shape[1] == 2, "Data must be 2d"

    rows = __row_cluster(points0[:, 1], row_threshold, plotit=False)

    point_assignments = np.array([np.argmin(abs(rows - xx)) for xx in points0[:, 1]])

    all_columns = []
    all_atoms = []

    for ind in range(len(rows)):
        points_in = np.where(point_assignments == ind)[0]

        column = __row_cluster(
            points0[points_in, 0], horizontal_threshold, plotit=False
        )
        all_columns.append(column)

        all_atoms += [(xx, rows[ind]) for xx in column]

    all_atoms = np.array(all_atoms)

    # Determine point assignments to atoms...
    assignments_F = []
    assignments_R = {ind: [] for ind in range(all_atoms.shape[0])}
    RMS_error = 0
    for ind in range(points0.shape[0]):
        dist = (points0[ind, 0] - all_atoms[:, 0]) ** 2 + (
            points0[ind, 1] - all_atoms[:, 1]
        ) ** 2
        assignments_F.append(np.argmin(dist))
        assignments_R[np.argmin(dist)].append(ind)

        RMS_error += np.min(dist)

    ERROR_OUT = np.sqrt(RMS_error / points0.shape[0])
    return all_atoms, assignments_F, assignments_R, ERROR_OUT
