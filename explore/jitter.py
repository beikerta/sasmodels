#!/usr/bin/env python
"""
Application to explore the difference between sasview 3.x orientation
dispersity and possible replacement algorithms.
"""
from __future__ import division, print_function

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

import mpl_toolkits.mplot3d   # Adds projection='3d' option to subplot
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, CheckButtons
from matplotlib import cm
import numpy as np
from numpy import pi, cos, sin, sqrt, exp, degrees, radians

def draw_beam(ax, view=(0, 0)):
    """
    Draw the beam going from source at (0, 0, 1) to detector at (0, 0, -1)
    """
    #ax.plot([0,0],[0,0],[1,-1])
    #ax.scatter([0]*100,[0]*100,np.linspace(1, -1, 100), alpha=0.8)

    steps = 25
    u = np.linspace(0, 2 * np.pi, steps)
    v = np.linspace(-1, 1, steps)

    r = 0.02
    x = r*np.outer(np.cos(u), np.ones_like(v))
    y = r*np.outer(np.sin(u), np.ones_like(v))
    z = 1.3*np.outer(np.ones_like(u), v)

    theta, phi = view
    shape = x.shape
    points = np.matrix([x.flatten(), y.flatten(), z.flatten()])
    points = Rz(phi)*Ry(theta)*points
    x, y, z = [v.reshape(shape) for v in points]

    ax.plot_surface(x, y, z, rstride=4, cstride=4, color='y', alpha=0.5)

def draw_jitter(ax, view, jitter, dist='gaussian', size=(0.1, 0.4, 1.0)):
    """
    Represent jitter as a set of shapes at different orientations.
    """
    # set max diagonal to 0.95
    scale = 0.95/sqrt(sum(v**2 for v in size))
    size = tuple(scale*v for v in size)
    draw_shape = draw_parallelepiped
    #draw_shape = draw_ellipsoid

    #np.random.seed(10)
    #cloud = np.random.randn(10,3)
    cloud = [
        [-1, -1, -1],
        [-1, -1,  0],
        [-1, -1,  1],
        [-1,  0, -1],
        [-1,  0,  0],
        [-1,  0,  1],
        [-1,  1, -1],
        [-1,  1,  0],
        [-1,  1,  1],
        [ 0, -1, -1],
        [ 0, -1,  0],
        [ 0, -1,  1],
        [ 0,  0, -1],
        [ 0,  0,  0],
        [ 0,  0,  1],
        [ 0,  1, -1],
        [ 0,  1,  0],
        [ 0,  1,  1],
        [ 1, -1, -1],
        [ 1, -1,  0],
        [ 1, -1,  1],
        [ 1,  0, -1],
        [ 1,  0,  0],
        [ 1,  0,  1],
        [ 1,  1, -1],
        [ 1,  1,  0],
        [ 1,  1,  1],
    ]
    dtheta, dphi, dpsi = jitter
    if dtheta == 0:
        cloud = [v for v in cloud if v[0] == 0]
    if dphi == 0:
        cloud = [v for v in cloud if v[1] == 0]
    if dpsi == 0:
        cloud = [v for v in cloud if v[2] == 0]
    draw_shape(ax, size, view, [0, 0, 0], steps=100, alpha=0.8)
    scale = 1/sqrt(3) if dist == 'rectangle' else 1
    for point in cloud:
        delta = [scale*dtheta*point[0], scale*dphi*point[1], scale*dpsi*point[2]]
        draw_shape(ax, size, view, delta, alpha=0.8)
    for v in 'xyz':
        a, b, c = size
        lim = np.sqrt(a**2+b**2+c**2)
        getattr(ax, 'set_'+v+'lim')([-lim, lim])
        getattr(ax, v+'axis').label.set_text(v)

def draw_ellipsoid(ax, size, view, jitter, steps=25, alpha=1):
    """Draw an ellipsoid."""
    a,b,c = size
    u = np.linspace(0, 2 * np.pi, steps)
    v = np.linspace(0, np.pi, steps)
    x = a*np.outer(np.cos(u), np.sin(v))
    y = b*np.outer(np.sin(u), np.sin(v))
    z = c*np.outer(np.ones_like(u), np.cos(v))
    x, y, z = transform_xyz(view, jitter, x, y, z)

    ax.plot_surface(x, y, z, rstride=4, cstride=4, color='w', alpha=alpha)

    draw_labels(ax, view, jitter, [
         ('c+', [ 0, 0, c], [ 1, 0, 0]),
         ('c-', [ 0, 0,-c], [ 0, 0,-1]),
         ('a+', [ a, 0, 0], [ 0, 0, 1]),
         ('a-', [-a, 0, 0], [ 0, 0,-1]),
         ('b+', [ 0, b, 0], [-1, 0, 0]),
         ('b-', [ 0,-b, 0], [-1, 0, 0]),
    ])

def draw_parallelepiped(ax, size, view, jitter, steps=None, alpha=1):
    """Draw a parallelepiped."""
    a,b,c = size
    x = a*np.array([ 1,-1, 1,-1, 1,-1, 1,-1])
    y = b*np.array([ 1, 1,-1,-1, 1, 1,-1,-1])
    z = c*np.array([ 1, 1, 1, 1,-1,-1,-1,-1])
    tri = np.array([
        # counter clockwise triangles
        # z: up/down, x: right/left, y: front/back
        [0,1,2], [3,2,1], # top face
        [6,5,4], [5,6,7], # bottom face
        [0,2,6], [6,4,0], # right face
        [1,5,7], [7,3,1], # left face
        [2,3,6], [7,6,3], # front face
        [4,1,0], [5,1,4], # back face
    ])

    x, y, z = transform_xyz(view, jitter, x, y, z)
    ax.plot_trisurf(x, y, triangles=tri, Z=z, color='w', alpha=alpha)

    draw_labels(ax, view, jitter, [
         ('c+', [ 0, 0, c], [ 1, 0, 0]),
         ('c-', [ 0, 0,-c], [ 0, 0,-1]),
         ('a+', [ a, 0, 0], [ 0, 0, 1]),
         ('a-', [-a, 0, 0], [ 0, 0,-1]),
         ('b+', [ 0, b, 0], [-1, 0, 0]),
         ('b-', [ 0,-b, 0], [-1, 0, 0]),
    ])

def draw_sphere(ax, radius=10., steps=100):
    """Draw a sphere"""
    u = np.linspace(0, 2 * np.pi, steps)
    v = np.linspace(0, np.pi, steps)

    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_surface(x, y, z, rstride=4, cstride=4, color='w')

def draw_mesh(ax, view, jitter, radius=1.2, n=11, dist='gaussian'):
    """
    Draw the dispersion mesh showing the theta-phi orientations at which
    the model will be evaluated.
    """
    theta, phi, psi = view
    dtheta, dphi, dpsi = jitter

    if dist == 'gaussian':
        t = np.linspace(-3, 3, n)
        weights = exp(-0.5*t**2)
    elif dist == 'rectangle':
        # Note: uses sasmodels ridiculous definition of rectangle width
        t = np.linspace(-1, 1, n)*sqrt(3)
        weights = np.ones_like(t)
    else:
        raise ValueError("expected dist to be 'gaussian' or 'rectangle'")

    #PROJECTION = 'stretched_phi'
    PROJECTION = 'azimuthal_equidistance'
    #PROJECTION = 'azimuthal_equal_area'
    if PROJECTION == 'stretced_phi':
        def rotate(theta_i, phi_j):
            if theta_i != 90:
                phi_j /= cos(radians(theta_i))
            return Rx(phi_j)*Ry(theta_i)
        def weight(theta_i, phi_j, wi, wj):
            if theta_i != 90:
                phi_j /= cos(radians(theta_i))
            return wi*wj if abs(phi_j) < 180 else 0
    elif PROJECTION == 'azimuthal_equidistance':
        # https://en.wikipedia.org/wiki/Azimuthal_equidistant_projection
        def rotate(theta_i, phi_j):
            latitude = sqrt(theta_i**2 + phi_j**2)
            longitude = degrees(np.arctan2(phi_j, theta_i))
            #print("(%+7.2f, %+7.2f) => (%+7.2f, %+7.2f)"%(theta_i, phi_j, latitude, longitude))
            return Rz(longitude)*Ry(latitude)
        def weight(theta_i, phi_j, wi, wj):
            # Weighting for each point comes from the integral:
            #     \int\int I(q, lat, log) sin(lat) dlat dlog
            # We are doing a conformal mapping from disk to sphere, so we need
            # a change of variables g(theta, phi) -> (lat, long):
            #     lat, long = sqrt(theta^2 + phi^2), arctan(phi/theta)
            # giving:
            #     dtheta dphi = det(J) dlat dlong
            # where J is the jacobian from the partials of g. Using
            #     R = sqrt(theta^2 + phi^2),
            # then
            #     J = [[x/R, Y/R], -y/R^2, x/R^2]]
            # and
            #     det(J) = 1/R
            # with the final integral being:
            #    \int\int I(q, theta, phi) sin(R)/R dtheta dphi
            #
            # This does approximately the right thing, decreasing the weight
            # of each point as you go farther out on the disk, but it hasn't
            # yet been checked against the 1D integral results. Prior
            # to declaring this "good enough" and checking that integrals
            # work in practice, we will examine alternative mappings.
            #
            # The issue is that the mapping does not support the case of free
            # rotation about a single axis correctly, with a small deviation
            # in the orthogonal axis independent of the first axis.  Like the
            # usual polar coordiates integration, the integrated sections
            # form wedges, though at least in this case the wedge cuts through
            # the entire sphere, and treats theta and phi identically.
            latitude = sqrt(theta_i**2 + phi_j**2)
            w = sin(radians(latitude))/latitude if latitude != 0 else 1
            return w*wi*wj if latitude < 180 else 0
    elif PROJECTION == 'azimuthal_equal_area':
        # https://en.wikipedia.org/wiki/Lambert_azimuthal_equal-area_projection
        def rotate(theta_i, phi_j):
            R = min(1, sqrt(theta_i**2 + phi_j**2)/180)
            latitude = 180-degrees(2*np.arccos(R))
            longitude = degrees(np.arctan2(phi_j, theta_i))
            #print("(%+7.2f, %+7.2f) => (%+7.2f, %+7.2f)"%(theta_i, phi_j, latitude, longitude))
            return Rz(longitude)*Ry(latitude)
        def weight(theta_i, phi_j, wi, wj):
            latitude = sqrt(theta_i**2 + phi_j**2)
            w = sin(radians(latitude))/latitude if latitude != 0 else 1
            return w*wi*wj if latitude < 180 else 0
    elif SCALED_PHI == 10:  # random thrashing
        def rotate(theta_i, phi_j):
            theta_i, phi_j = 2*theta_i/abs(cos(radians(phi_j))), 2*phi_j/cos(radians(theta_i))
            return Rx(phi_j)*Ry(theta_i)
        def weight(theta_i, phi_j, wi, wj):
            theta_i, phi_j = 2*theta_i/abs(cos(radians(phi_j))), 2*phi_j/cos(radians(theta_i))
            return wi*wj if abs(phi_j) < 180 else 0
    else:
        def rotate(theta_i, phi_j):
            return Rx(phi_j)*Ry(theta_i)
        def weight(theta_i, phi_j, wi, wj):
            return wi*wj*cos(radians(theta_i))

    # mesh in theta, phi formed by rotating z
    z = np.matrix([[0], [0], [radius]])
    points = np.hstack([rotate(theta_i, phi_j)*z
                        for theta_i in dtheta*t
                        for phi_j in dphi*t])
    # select just the active points (i.e., those with phi < 180
    w = np.array([weight(theta_i, phi_j, wi, wj)
                  for wi, theta_i in zip(weights, dtheta*t)
                  for wj, phi_j in zip(weights, dphi*t)])
    #print(max(w), min(w), min(w[w>0]))
    points = points[:, w>0]
    w = w[w>0]
    w /= max(w)

    if 0: # Kent distribution
        points = np.hstack([Rx(phi_j)*Ry(theta_i)*z for theta_i in 30*t for phi_j in 60*t])
        xp, yp, zp = [np.array(v).flatten() for v in points]
        kappa = max(1e6, radians(dtheta)/(2*pi))
        beta = 1/max(1e-6, radians(dphi)/(2*pi))/kappa
        w = exp(kappa*zp) #+ beta*(xp**2 + yp**2)
        print(kappa, dtheta, radians(dtheta), min(w), max(w), sum(w))
        #w /= abs(cos(radians(
        #w /= sum(w)

    # rotate relative to beam
    points = orient_relative_to_beam(view, points)

    x, y, z = [np.array(v).flatten() for v in points]
    #plt.figure(2); plt.clf(); plt.hist(z, bins=np.linspace(-1, 1, 51))
    ax.scatter(x, y, z, c=w, marker='o', vmin=0., vmax=1.)

def draw_labels(ax, view, jitter, text):
    """
    Draw text at a particular location.
    """
    labels, locations, orientations = zip(*text)
    px, py, pz = zip(*locations)
    dx, dy, dz = zip(*orientations)

    px, py, pz = transform_xyz(view, jitter, px, py, pz)
    dx, dy, dz = transform_xyz(view, jitter, dx, dy, dz)

    # TODO: zdir for labels is broken, and labels aren't appearing.
    for label, p, zdir in zip(labels, zip(px, py, pz), zip(dx, dy, dz)):
        zdir = np.asarray(zdir).flatten()
        ax.text(p[0], p[1], p[2], label, zdir=zdir)

# Definition of rotation matrices comes from wikipedia:
#    https://en.wikipedia.org/wiki/Rotation_matrix#Basic_rotations
def Rx(angle):
    """Construct a matrix to rotate points about *x* by *angle* degrees."""
    a = radians(angle)
    R = [[1, 0, 0],
         [0, +cos(a), -sin(a)],
         [0, +sin(a), +cos(a)]]
    return np.matrix(R)

def Ry(angle):
    """Construct a matrix to rotate points about *y* by *angle* degrees."""
    a = radians(angle)
    R = [[+cos(a), 0, +sin(a)],
         [0, 1, 0],
         [-sin(a), 0, +cos(a)]]
    return np.matrix(R)

def Rz(angle):
    """Construct a matrix to rotate points about *z* by *angle* degrees."""
    a = radians(angle)
    R = [[+cos(a), -sin(a), 0],
         [+sin(a), +cos(a), 0],
         [0, 0, 1]]
    return np.matrix(R)

def transform_xyz(view, jitter, x, y, z):
    """
    Send a set of (x,y,z) points through the jitter and view transforms.
    """
    x, y, z = [np.asarray(v) for v in (x, y, z)]
    shape = x.shape
    points = np.matrix([x.flatten(),y.flatten(),z.flatten()])
    points = apply_jitter(jitter, points)
    points = orient_relative_to_beam(view, points)
    x, y, z = [np.array(v).reshape(shape) for v in points]
    return x, y, z

def apply_jitter(jitter, points):
    """
    Apply the jitter transform to a set of points.

    Points are stored in a 3 x n numpy matrix, not a numpy array or tuple.
    """
    dtheta, dphi, dpsi = jitter
    points = Rx(dphi)*Ry(dtheta)*Rz(dpsi)*points
    return points

def orient_relative_to_beam(view, points):
    """
    Apply the view transform to a set of points.

    Points are stored in a 3 x n numpy matrix, not a numpy array or tuple.
    """
    theta, phi, psi = view
    points = Rz(phi)*Ry(theta)*Rz(psi)*points
    return points

# translate between number of dimension of dispersity and the number of
# points along each dimension.
PD_N_TABLE = {
    (0, 0, 0): (0, 0, 0),     # 0
    (1, 0, 0): (100, 0, 0),   # 100
    (0, 1, 0): (0, 100, 0),
    (0, 0, 1): (0, 0, 100),
    (1, 1, 0): (30, 30, 0),   # 900
    (1, 0, 1): (30, 0, 30),
    (0, 1, 1): (0, 30, 30),
    (1, 1, 1): (15, 15, 15),  # 3375
}

def clipped_range(data, portion=1.0, mode='central'):
    """
    Determine range from data.

    If *portion* is 1, use full range, otherwise use the center of the range
    or the top of the range, depending on whether *mode* is 'central' or 'top'.
    """
    if portion == 1.0:
        return data.min(), data.max()
    elif mode == 'central':
        data = np.sort(data.flatten())
        offset = int(portion*len(data)/2 + 0.5)
        return data[offset], data[-offset]
    elif mode == 'top':
        data = np.sort(data.flatten())
        offset = int(portion*len(data) + 0.5)
        return data[offset], data[-1]

def draw_scattering(calculator, ax, view, jitter, dist='gaussian'):
    """
    Plot the scattering for the particular view.

    *calculator* is returned from :func:`build_model`.  *ax* are the 3D axes
    on which the data will be plotted.  *view* and *jitter* are the current
    orientation and orientation dispersity.  *dist* is one of the sasmodels
    weight distributions.
    """
    ## Sasmodels use sqrt(3)*width for the rectangle range; scale to the
    ## proper width for comparison. Commented out since now using the
    ## sasmodels definition of width for rectangle.
    #scale = 1/sqrt(3) if dist == 'rectangle' else 1
    scale = 1

    # add the orientation parameters to the model parameters
    theta, phi, psi = view
    theta_pd, phi_pd, psi_pd = [scale*v for v in jitter]
    theta_pd_n, phi_pd_n, psi_pd_n = PD_N_TABLE[(theta_pd>0, phi_pd>0, psi_pd>0)]
    ## increase pd_n for testing jitter integration rather than simple viz
    #theta_pd_n, phi_pd_n, psi_pd_n = [5*v for v in (theta_pd_n, phi_pd_n, psi_pd_n)]

    pars = dict(
        theta=theta, theta_pd=theta_pd, theta_pd_type=dist, theta_pd_n=theta_pd_n,
        phi=phi, phi_pd=phi_pd, phi_pd_type=dist, phi_pd_n=phi_pd_n,
        psi=psi, psi_pd=psi_pd, psi_pd_type=dist, psi_pd_n=psi_pd_n,
    )
    pars.update(calculator.pars)

    # compute the pattern
    qx, qy = calculator._data.x_bins, calculator._data.y_bins
    Iqxy = calculator(**pars).reshape(len(qx), len(qy))

    # scale it and draw it
    Iqxy = np.log(Iqxy)
    if calculator.limits:
        # use limits from orientation (0,0,0)
        vmin, vmax = calculator.limits
    else:
        vmin, vmax = clipped_range(Iqxy, portion=0.95, mode='top')
    #print("range",(vmin,vmax))
    #qx, qy = np.meshgrid(qx, qy)
    if 0:
        level = np.asarray(255*(Iqxy - vmin)/(vmax - vmin), 'i')
        level[level<0] = 0
        colors = plt.get_cmap()(level)
        ax.plot_surface(qx, qy, -1.1, rstride=1, cstride=1, facecolors=colors)
    elif 1:
        ax.contourf(qx/qx.max(), qy/qy.max(), Iqxy, zdir='z', offset=-1.1,
                    levels=np.linspace(vmin, vmax, 24))
    else:
        ax.pcolormesh(qx, qy, Iqxy)

def build_model(model_name, n=150, qmax=0.5, **pars):
    """
    Build a calculator for the given shape.

    *model_name* is any sasmodels model.  *n* and *qmax* define an n x n mesh
    on which to evaluate the model.  The remaining parameters are stored in
    the returned calculator as *calculator.pars*.  They are used by
    :func:`draw_scattering` to set the non-orientation parameters in the
    calculation.

    Returns a *calculator* function which takes a dictionary or parameters and
    produces Iqxy.  The Iqxy value needs to be reshaped to an n x n matrix
    for plotting.  See the :class:`sasmodels.direct_model.DirectModel` class
    for details.
    """
    from sasmodels.core import load_model_info, build_model
    from sasmodels.data import empty_data2D
    from sasmodels.direct_model import DirectModel

    model_info = load_model_info(model_name)
    model = build_model(model_info) #, dtype='double!')
    q = np.linspace(-qmax, qmax, n)
    data = empty_data2D(q, q)
    calculator = DirectModel(data, model)

    # stuff the values for non-orientation parameters into the calculator
    calculator.pars = pars.copy()
    calculator.pars.setdefault('backgound', 1e-3)

    # fix the data limits so that we can see if the pattern fades
    # under rotation or angular dispersion
    Iqxy = calculator(theta=0, phi=0, psi=0, **calculator.pars)
    Iqxy = np.log(Iqxy)
    vmin, vmax = clipped_range(Iqxy, 0.95, mode='top')
    calculator.limits = vmin, vmax+1

    return calculator

def select_calculator(model_name, n=150, size=(10,40,100)):
    """
    Create a model calculator for the given shape.

    *model_name* is one of sphere, cylinder, ellipsoid, triaxial_ellipsoid,
    parallelepiped or bcc_paracrystal. *n* is the number of points to use
    in the q range.  *qmax* is chosen based on model parameters for the
    given model to show something intersting.

    Returns *calculator* and tuple *size* (a,b,c) giving minor and major
    equitorial axes and polar axis respectively.  See :func:`build_model`
    for details on the returned calculator.
    """
    a, b, c = size
    if model_name == 'sphere':
        calculator = build_model('sphere', n=n, radius=c)
        a = b = c
    elif model_name == 'bcc_paracrystal':
        calculator = build_model('bcc_paracrystal', n=n, dnn=c,
                                  d_factor=0.06, radius=40)
        a = b = c
    elif model_name == 'cylinder':
        calculator = build_model('cylinder', n=n, qmax=0.3, radius=b, length=c)
        a = b
    elif model_name == 'ellipsoid':
        calculator = build_model('ellipsoid', n=n, qmax=1.0,
                                 radius_polar=c, radius_equatorial=b)
        a = b
    elif model_name == 'triaxial_ellipsoid':
        calculator = build_model('triaxial_ellipsoid', n=n, qmax=0.5,
                                 radius_equat_minor=a,
                                 radius_equat_major=b,
                                 radius_polar=c)
    elif model_name == 'parallelepiped':
        calculator = build_model('parallelepiped', n=n, a=a, b=b, c=c)
    else:
        raise ValueError("unknown model %s"%model_name)

    return calculator, (a, b, c)

def main(model_name='parallelepiped', size=(10, 40, 100)):
    """
    Show an interactive orientation and jitter demo.

    *model_name* is one of the models available in :func:`select_model`.
    """
    # set up calculator
    calculator, size = select_calculator(model_name, n=150, size=size)

    ## uncomment to set an independent the colour range for every view
    ## If left commented, the colour range is fixed for all views
    calculator.limits = None

    ## use gaussian distribution unless testing integration
    dist = 'rectangle'
    #dist = 'gaussian'

    ## initial view
    #theta, dtheta = 70., 10.
    #phi, dphi = -45., 3.
    #psi, dpsi = -45., 3.
    theta, phi, psi = 0, 0, 0
    dtheta, dphi, dpsi = 0, 0, 0

    ## create the plot window
    #plt.hold(True)
    plt.set_cmap('gist_earth')
    plt.clf()
    #gs = gridspec.GridSpec(2,1,height_ratios=[4,1])
    #ax = plt.subplot(gs[0], projection='3d')
    ax = plt.axes([0.0, 0.2, 1.0, 0.8], projection='3d')
    try:  # CRUFT: not all versions of matplotlib accept 'square' 3d projection
        ax.axis('square')
    except Exception:
        pass

    axcolor = 'lightgoldenrodyellow'

    ## add control widgets to plot
    axtheta  = plt.axes([0.1, 0.15, 0.45, 0.04], axisbg=axcolor)
    axphi = plt.axes([0.1, 0.1, 0.45, 0.04], axisbg=axcolor)
    axpsi = plt.axes([0.1, 0.05, 0.45, 0.04], axisbg=axcolor)
    stheta = Slider(axtheta, 'Theta', -90, 90, valinit=theta)
    sphi = Slider(axphi, 'Phi', -180, 180, valinit=phi)
    spsi = Slider(axpsi, 'Psi', -180, 180, valinit=psi)

    axdtheta  = plt.axes([0.75, 0.15, 0.15, 0.04], axisbg=axcolor)
    axdphi = plt.axes([0.75, 0.1, 0.15, 0.04], axisbg=axcolor)
    axdpsi= plt.axes([0.75, 0.05, 0.15, 0.04], axisbg=axcolor)
    # Note: using ridiculous definition of rectangle distribution, whose width
    # in sasmodels is sqrt(3) times the given width.  Divide by sqrt(3) to keep
    # the maximum width to 90.
    dlimit = 30 if dist == 'gaussian' else 90/sqrt(3)
    sdtheta = Slider(axdtheta, 'dTheta', 0, 2*dlimit, valinit=dtheta)
    sdphi = Slider(axdphi, 'dPhi', 0, 2*dlimit, valinit=dphi)
    sdpsi = Slider(axdpsi, 'dPsi', 0, 2*dlimit, valinit=dpsi)

    ## callback to draw the new view
    def update(val, axis=None):
        view = stheta.val, sphi.val, spsi.val
        jitter = sdtheta.val, sdphi.val, sdpsi.val
        # set small jitter as 0 if multiple pd dims
        dims = sum(v > 0 for v in jitter)
        limit = [0, 0, 2, 5][dims]
        jitter = [0 if v < limit else v for v in jitter]
        ax.cla()
        draw_beam(ax, (0, 0))
        draw_jitter(ax, view, jitter, dist=dist, size=size)
        #draw_jitter(ax, view, (0,0,0))
        draw_mesh(ax, view, jitter, dist=dist, n=30)
        draw_scattering(calculator, ax, view, jitter, dist=dist)
        plt.gcf().canvas.draw()

    ## bind control widgets to view updater
    stheta.on_changed(lambda v: update(v,'theta'))
    sphi.on_changed(lambda v: update(v, 'phi'))
    spsi.on_changed(lambda v: update(v, 'psi'))
    sdtheta.on_changed(lambda v: update(v, 'dtheta'))
    sdphi.on_changed(lambda v: update(v, 'dphi'))
    sdpsi.on_changed(lambda v: update(v, 'dpsi'))

    ## initialize view
    update(None, 'phi')

    ## go interactive
    plt.show()

if __name__ == "__main__":
    model_name = sys.argv[1] if len(sys.argv) > 1 else 'parallelepiped'
    size = tuple(int(v) for v in sys.argv[2].split(',')) if len(sys.argv) > 2 else (10, 40, 100)
    main(model_name, size)
