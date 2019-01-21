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

"""Module to define graphic styles like colours and stroke styles.

This module import :class:`Color.Colors`.

"""

####################################################################################################

__all__ = ['Colors', 'StrokeStyle']

####################################################################################################

from enum import Enum, auto

#: Colour Database Singleton as an instance of :class:`ColorDataBase`
from .Color import Colors

####################################################################################################

class StrokeStyle(Enum):

     """Enum class to define stroke styles"""

     NoPen = auto()
     SolidLine = auto()
     DashLine =	auto()
     DotLine = auto()
     DashDotLine = auto()
     DashDotDotLine = auto()
