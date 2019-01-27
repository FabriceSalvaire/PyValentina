####################################################################################################
#
# Patro - A Python library to make patterns for fashion design
# Copyright (C) 2019 Fabrice Salvaire
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
####################################################################################################

"""Module to implement path.

"""

####################################################################################################

__all__ = [
    'LinearSegment',
    'QuadraticBezierSegment',
    'CubicBezierSegment',
    'Path2D',
    ]

####################################################################################################

import math

from .Primitive import Primitive1P, Primitive2DMixin
from .Bezier import QuadraticBezier2D, CubicBezier2D
from .Conic import Circle2D, AngularDomain
from .Segment import Segment2D
from .Vector import Vector2D

####################################################################################################

class PathPart:

    ##############################################

    def __init__(self, path, index):

        self._path = path
        self._index = index

    ##############################################

    def clone(self, path):
        raise NotImplementedError

    ##############################################

    def __repr__(self):
        return '{0}(@{1._index})'.format(self.__class__.__name__, self)

    ##############################################

    @property
    def path(self):
        return self._path

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = int(value)

    ##############################################

    @property
    def prev_part(self):
        return self._path[self._index -1]

    @property
    def next_part(self):
        return self._path[self._index +1]

    ##############################################

    @property
    def start_point(self):
        # Fixme: cache ???
        prev_part = self.prev_part
        if prev_part is not None:
            return prev_part.stop_point
        else:
            return self._path.p0

    ##############################################

    @property
    def stop_point(self):
        raise NotImplementedError

    @property
    def geometry(self):
        raise NotImplementedError

    ##############################################

    @property
    def bounding_box(self):
        return self.geometry.bounding_box

####################################################################################################

class OnePointMixin:

    ##############################################

    @property
    def point(self):
        return self._point

    @point.setter
    def point(self, value):
        self._point = Vector2D(value) # self._path.__vector_cls__

    ##############################################

    @property
    def stop_point(self):
        if self._absolute:
            return self._point
        else:
            return self._point + self.start_point

    ##############################################

    def apply_transformation(self, transformation):
        self._point = transformation * self._point

####################################################################################################

class TwoPointMixin:

    @property
    def point1(self):
        return self._point1

    @point1.setter
    def point1(self, value):
        self._point1 = Vector2D(value) # self._path.__vector_cls__

    @property
    def point2(self):
        return self._point2

    @point2.setter
    def point2(self, value):
        self._point2 = Vector2D(value)

    ##############################################

    def apply_transformation(self, transformation):
        self._point1 = transformation * self._point1
        self._point2 = transformation * self._point2

####################################################################################################

class LinearSegment(PathPart):

    r"""

    Bulge

    Let `P0`, `P1`, `P2` the vertices and `R` the bulge radius.

    The deflection :math:`\theta = 2 \alpha` at the corner is

    .. math::

       D_1 \cdot D_0 = (P_2 - P_1) \cdot (P_1 - P_0) = \cos \theta

    The bisector direction is

    .. math::

       Bis = D_1 - D_0 = (P_2 - P_1) - (P_1 - P_0) = P_2 -2 P_1 + P_0

    Bulge Center is

    .. math::

        C = P_1 + Bis \times \frac{R}{\sin \alpha}

    Extremities are

        \prime P_1 = P_1 - d_0 \times \frac{R}{\tan \alpha}
        \prime P_1 = P_1 + d_1 \times \frac{R}{\tan \alpha}

    """

    # Fixme:
    #
    #    If two successive vertices share the same circle, then it should be merged to one.
    #

    ##############################################

    def __init__(self, path, index, radius, closing=False):

        super().__init__(path, index)

        self._bissector = None
        self._direction = None

        self._start_radius = False
        self._closing = bool(closing)
        self.radius = radius
        if self._radius is not None:
            if not isinstance(self.prev_part, LinearSegment):
                raise ValueError('Previous path segment must be linear')
            self._reset_cache()

    ##############################################

    def _reset_cache(self):

        self._bulge_angle = None
        self._bulge_center = None
        self._start_bulge_point = None
        self._stop_bulge_point = None

    ##############################################

    def close(self, radius):
        self.radius = radius
        self._reset_cache()
        self._start_radius = True
        print('set close', self, self.__dict__)

    ##############################################

    @property
    def prev_part(self):
        if self._start_radius:
            return self._path.stop_segment # or [-1] don't work
        else:
            # Fixme: super
            return self._path[self._index -1]

    @property
    def next_part(self):
        if self._closing:
            return self._path.start_segment # or [0]
        else:
            return self._path[self._index +1]

    ##############################################

    @property
    def points(self):

        if self._radius is not None:
            start_point = self.bulge_stop_point
        else:
            start_point = self.start_point

        next_part = self.next_part
        if isinstance(next_part, LinearSegment) and next_part.radius is not None:
            stop_point = next_part.bulge_start_point
        else:
            stop_point = self.stop_point

        return start_point, stop_point

    ##############################################

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value is not None:
            self._radius = float(value)
        else:
            self._radius = None

    ##############################################

    @property
    def direction(self):
        if self._direction is None:
            self._direction = (self.stop_point - self.start_point).normalise()
        return self._direction

    @property
    def bissector(self):
        if self._radius is None:
            return None
        else:
            if self._bissector is None:
                # self._bissector = (self.prev_part.direction + self.direction).normalise().normal
                self._bissector = (self.direction - self.prev_part.direction).normalise()
            return self._bissector

    ##############################################

    @property
    def bulge_angle_rad(self):
        if self._bulge_angle is None:
            angle = self.direction.orientation_with(self.prev_part.direction)
            self._bulge_angle = math.radians(angle)
        return self._bulge_angle

    @property
    def bulge_angle(self):
        return math.degrees(self.bulge_angle_rad)

    @property
    def half_bulge_angle(self):
        return abs(self.bulge_angle_rad / 2)

    ##############################################

    @property
    def bulge_center(self):
        if self._bulge_center is None:
            offset = self.bissector * self._radius / math.sin(self.half_bulge_angle)
            self._bulge_center = self.start_point + offset
        return self._bulge_center

    ##############################################

    @property
    def bulge_start_point(self):
        if self._start_bulge_point is None:
            offset = self.prev_part.direction * self._radius / math.tan(self.half_bulge_angle)
            self._start_bulge_point = self.start_point - offset
        return self._start_bulge_point

    @property
    def bulge_stop_point(self):
        if self._stop_bulge_point is None:
            offset = self.direction * self._radius / math.tan(self.half_bulge_angle)
            self._stop_bulge_point = self.start_point + offset
        return self._stop_bulge_point

    ##############################################

    @property
    def bulge_geometry(self):
        # Fixme: check start and stop are within segment
        arc = Circle2D(self.bulge_center, self._radius)
        start_angle, stop_angle = [arc.angle_for_point(point)
                                   for point in (self.bulge_start_point, self.bulge_stop_point)]
        if self.bulge_angle < 0:
            start_angle, stop_angle = stop_angle, start_angle
        arc.domain = AngularDomain(start_angle, stop_angle)
        return arc

####################################################################################################

class PathSegment(OnePointMixin, LinearSegment):

    ##############################################

    def __init__(self, path, index, point, radius=None, absolute=False, closing=False):
        super().__init__(path, index, radius, closing)
        self.point = point
        self._absolute = bool(absolute)

    ##############################################

    def clone(self, path):
        return self.__class__(path, self._index, self._point, self._radius, self._absolute)

    ##############################################

    def apply_transformation(self, transformation):
        OnePointMixin.apply_transformation(self, transformation)
        if self._radius is not None:
            self._radius = transformation * self._radius

    ##############################################

    @property
    def geometry(self):
        # Fixme: cache ???
        return Segment2D(*self.points)

####################################################################################################

class DirectionalSegment(LinearSegment):

    __angle__ = None

    ##############################################

    def __init__(self, path, index, length, radius=None):
        super().__init__(path, index, radius)
        self.length = length

    ##############################################

    def apply_transformation(self, transformation):
        # Since a rotation will change the direction
        # DirectionalSegment must be casted to PathSegment
        raise NotImplementedError

    ##############################################

    def clone(self, path):
        return self.__class__(path, self._index, self._length, self._radius)

    ##############################################

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        self._length = float(value)

    ##############################################

    @property
    def offset(self):
        # Fixme: cache ???
        return Vector2D.from_polar(self._length, self.__angle__)

    @property
    def stop_point(self):
        # Fixme: cache ???
        return self.start_point + self.offset

    ##############################################

    @property
    def geometry(self):
        # Fixme: cache ???
        return Segment2D(self.start_point, self.stop_point)

    ##############################################

    def to_path_segment(self):
        return PathSegment(self._path, self._index, self.offset, self._radius, absolute=False)

####################################################################################################

class HorizontalSegment(DirectionalSegment):
    __angle__ = 0

class VerticalSegment(DirectionalSegment):
    __angle__ = 90

class NorthSegment(DirectionalSegment):
    __angle__ = 90

class SouthSegment(DirectionalSegment):
    __angle__ = -90

class EastSegment(DirectionalSegment):
    __angle__ = 0

class WestSegment(DirectionalSegment):
    __angle__ = 180

class NorthEastSegment(DirectionalSegment):
    __angle__ = 45

class NorthWestSegment(DirectionalSegment):
    __angle__ = 180 - 45

class SouthEastSegment(DirectionalSegment):
    __angle__ = -45

class SouthWestSegment(DirectionalSegment):
    __angle__ = -180 + 45

####################################################################################################

class QuadraticBezierSegment(PathPart, TwoPointMixin):

    # Fixme: abs / inc

    ##############################################

    def __init__(self, path, index, point1, point2, absolute=False):

        PathPart.__init__(self, path, index)

        self.point1 = point1
        self.point2 = point2

    ##############################################

    def clone(self, path):
        return self.__class__(path, self._index, self._point1, self._point2)

    ##############################################

    @property
    def stop_point(self):
        return self._point2

    @property
    def points(self):
        return (self.start_point, self._point1, self._point2)

    ##############################################

    @property
    def geometry(self):
        # Fixme: cache ???
        return QuadraticBezier2D(self.start_point, self._point1, self._point2)

####################################################################################################

class CubicBezierSegment(PathPart, TwoPointMixin):

    ##############################################

    def __init__(self, path, index, point1, point2, point3, absolute=False):

        PathPart.__init__(self, path, index)

        self.point1 = point1
        self.point2 = point2
        self.point3 = point3

    ##############################################

    def clone(self, path):
        return self.__class__(path, self._index, self._point1, self._point2, self._point3)

    ##############################################

    def apply_transformation(self, transformation):
        TwoPointMixin.apply_transformation(self, transformation)
        self._point3 = transformation * self._point3

    ##############################################

    @property
    def point3(self):
        return self._point3

    @point3.setter
    def point3(self, value):
        self._point3 = Vector2D(value) # self._path.__vector_cls__

    ##############################################

    @property
    def stop_point(self):
        return self._point3

    @property
    def points(self):
        return (self.start_point, self._point1, self._point2, self._point3)

    ##############################################

    @property
    def geometry(self):
        # Fixme: cache ???
        return CubicBezier2D(self.start_point, self._point1, self._point2, self._point3)

####################################################################################################

class StringedQuadtraticBezierSegment(PathPart, TwoPointMixin):

    ##############################################

    def __init__(self, path, index, point1, absolute=False):

        PathPart.__init__(self, path, index)

        self.point1 = point1

    ##############################################

    def clone(self, path):
        return self.__class__(path, self._index, self._point1)

    ##############################################

    @property
    def geometry(self):
        # Fixme: cache ???
        # Fixme: !!!
        return Segment2D(self.start_point, self._point2)
        # return CubicBezier2D(self.start_point, self._point1, self._point2, self._point3)

####################################################################################################

class StringedCubicBezierSegment(PathPart, TwoPointMixin):

    ##############################################

    def __init__(self, path, index, point1, point2, absolute=False):

        PathPart.__init__(self, path, index)

        # self.point1 = point1

    ##############################################

    def clone(self, path):
        return self.__class__(path, self._index, self._point1, self._point2)

    ##############################################

    @property
    def geometry(self):
        # Fixme: cache ???
        # Fixme: !!!
        return Segment2D(self.start_point, self._point2)
        # return CubicBezier2D(self.start_point, self._point1, self._point2, self._point3)

####################################################################################################

class ArcSegment(OnePointMixin, PathPart):

    ##############################################

    def __init__(self, path, index, point, radius_x, radius_y, angle, large_arc, sweep, absolute=False):

        PathPart.__init__(self, path, index)

        self.point = point
        self._absolute = bool(absolute)

        self._large_arc = bool(large_arc)
        self._sweep = bool(sweep)
        self._radius_x = radius_x
        self._radius_y = radius_y
        self._angle = angle

    ##############################################

    def clone(self, path):
        return self.__class__(
            path,
            self._index,
            self._point,
            self._large_arc, self._sweep,
            self._radius_x, self._radius_y,
            self._angle
        )

    ##############################################

    @property
    def points(self):
        return self.start_point, self.stop_point

    ##############################################

    @property
    def geometry(self):
        # Fixme: !!!
        return Segment2D(self.start_point, self.stop_point)

####################################################################################################

class Path2D(Primitive2DMixin, Primitive1P):

    """Class to implements 2D Path."""

    ##############################################

    def __init__(self, start_point):

        Primitive1P.__init__(self, start_point)

        self._parts = [] # Fixme: segment ???
        self._is_closed = False

    ##############################################

    def clone(self):

        obj = self.__class__(self._p0)

        # parts must be added sequentially to the path for bulge check
        parts = obj._parts
        for part in self._parts:
            parts.append(part.clone(obj))

        return obj

    ##############################################

    def __len__(self):
        return len(self._parts)

    def __iter__(self):
        return iter(self._parts)

    def __getitem__(self, index):
        # try:
        #     return self._parts[slice_]
        # except IndexError:
        #     return None
        index = int(index)
        number_of_parts = len(self._parts)
        if 0 <= index < number_of_parts:
            return self._parts[index]
        # elif self._is_closed:
        #     if index == -1:
        #         return self.start_segment
        #     elif index == number_of_parts:
        #         return self.stop_segment
        return None

    ##############################################

    @property
    def start_segment(self):
        # Fixme: start_part ???
        return self._parts[0]

    @property
    def stop_segment(self):
        return self._parts[-1]

    ##############################################

    @property
    def is_closed(self):
        return self._is_closed

    ##############################################

    def _add_part(self, part_cls, *args, **kwargs):
        obj = part_cls(self, len(self._parts), *args, **kwargs)
        self._parts.append(obj)
        return obj

    ##############################################

    def apply_transformation(self, transformation):

        self._p0 = transformation * self._p0

        for i, part in enumerate(self._parts):
            if isinstance(part, PathSegment):
                part._reset_cache()
            if isinstance(part, DirectionalSegment):
                # Since a rotation will change the direction
                # DirectionalSegment must be casted to PathSegment
                part = part.to_path_segment()
                self._parts[i] = part
            part.apply_transformation(transformation)

    ##############################################

    @property
    def bounding_box(self):

        # Fixme: cache
        bounding_box = None
        for item in self._parts:
            interval = item.geometry.bounding_box
            if bounding_box is None:
                bounding_box = interval
            else:
                bounding_box |= interval
        return bounding_box

    ##############################################

    def move_to(self, point):
        self.p0 = point

    ##############################################

    def horizontal_to(self, distance, radius=None, absolute=False):
        if absolute:
            return self._add_part(PathSegment, self.__vector_cls__(distance, 0), radius,
                                  absolute=True)
        else:
            return self._add_part(HorizontalSegment, distance, radius)

    ##############################################

    def vertical_to(self, distance, radius=None, absolute=False):
        if absolute:
            return self._add_part(PathSegment, self.__vector_cls__(0, distance), radius,
                                  absolute=True)
        else:
            return self._add_part(VerticalSegment, distance, radius)

    ##############################################

    def north_to(self, distance, radius=None):
        return self._add_part(NorthSegment, distance, radius)

    def south_to(self, distance, radius=None):
        return self._add_part(SouthSegment, distance, radius)

    def west_to(self, distance, radius=None):
        return self._add_part(WestSegment, distance, radius)

    def east_to(self, distance, radius=None):
        return self._add_part(EastSegment, distance, radius)

    def north_east_to(self, distance, radius=None):
        return self._add_part(NorthEastSegment, distance, radius)

    def south_east_to(self, distance, radius=None):
        return self._add_part(SouthEastSegment, distance, radius)

    def north_west_to(self, distance, radius=None):
        return self._add_part(NorthWestSegment, distance, radius)

    def south_west_to(self, distance, radius=None):
        return self._add_part(SouthWestSegment, distance, radius)

    ##############################################

    def line_to(self, point, radius=None, absolute=False):
        return self._add_part(PathSegment, point, radius, absolute=absolute)

    ##############################################

    def close(self, radius=None, close_radius=None):
        # Fixme: identify as close for SVG export <-- meaning ???
        # Fixme: radius must apply to start and stop
        closing = close_radius is not None
        segment = self._add_part(PathSegment, self._p0, radius, absolute=True, closing=closing)
        if closing:
            self.start_segment.close(close_radius)
        self._is_closed = True
        return segment

    ##############################################

    def quadratic_to(self, point1, point2, absolute=True):
        return self._add_part(QuadraticBezierSegment, point1, point2, absolute=absolute)

    ##############################################

    def cubic_to(self, point1, point2, point3, absolute=True):
        return self._add_part(CubicBezierSegment, point1, point2, point3, absolute=absolute)

    ##############################################

    def stringed_quadratic_to(self, point, absolute=True):
        return self._add_part(StringedQuadraticBezierSegment, point, absolute=absolute)

    ##############################################

    def stringed_cubic_to(self, point1, point2, absolute=True):
        return self._add_part(StringedCubicBezierSegment, point1, point2, absolute=absolute)

    ##############################################

    def arc_to(self, point, radius_x, radius_y, angle, large_arc, sweep, absolute=True):
        return self._add_part(ArcSegment, point, radius_x, radius_y, angle, large_arc, sweep,
                              absolute=absolute)
