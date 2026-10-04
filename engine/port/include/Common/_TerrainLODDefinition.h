/*
**	Command & Conquer Generals Zero Hour(tm)
**	Copyright 2025 Electronic Arts Inc.
**
**	This program is free software: you can redistribute it and/or modify
**	it under the terms of the GNU General Public License as published by
**	the Free Software Foundation, either version 3 of the License, or
**	(at your option) any later version.
**
**	This program is distributed in the hope that it will be useful,
**	but WITHOUT ANY WARRANTY; without even the implied warranty of
**	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
**	GNU General Public License for more details.
**
**	You should have received a copy of the GNU General Public License
**	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
#pragma once
typedef enum _TerrainLOD
{
	TERRAIN_LOD_INVALID								= 0,
	TERRAIN_LOD_MIN										= 1,  // note that this is less than max
	TERRAIN_LOD_STRETCH_NO_CLOUDS			= 2,
	TERRAIN_LOD_HALF_CLOUDS						= 3,
	TERRAIN_LOD_NO_CLOUDS							= 4,
	TERRAIN_LOD_STRETCH_CLOUDS				= 5,
	TERRAIN_LOD_NO_WATER							= 6,
	TERRAIN_LOD_MAX										= 7,  // note that this is larger than min
	TERRAIN_LOD_AUTOMATIC							= 8,
	TERRAIN_LOD_DISABLE								= 9,

	TERRAIN_LOD_NUM_TYPES								// keep this last

} TerrainLOD;
