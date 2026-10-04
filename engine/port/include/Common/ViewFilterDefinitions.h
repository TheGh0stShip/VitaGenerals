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
enum FilterTypes
{
	FT_NULL_FILTER=0,
	// The following are screen filter shaders, that modify the rendered viewport after it is drawn.
	FT_VIEW_BW_FILTER,		//filter to apply a black & white filter to the screen.
	FT_VIEW_MOTION_BLUR_FILTER, //filter to apply motion blur filter to screen.
	FT_VIEW_CROSSFADE,				///<filter to apply a cross blend between previous/current views.
	FT_VIEW_DEFAULT,				///<default filter mode for default filter.
	FT_MAX
};
enum FilterModes
{
	FM_NULL_MODE = 0,

	// These apply to FT_VIEW_BW_FILTER
	FM_VIEW_BW_BLACK_AND_WHITE, // BW Filter to black & white
	FM_VIEW_BW_RED_AND_WHITE, // BW Filter to red & white
	FM_VIEW_BW_GREEN_AND_WHITE, // BW Filter to green & white

	// These apply to FT_VIEW_CROSSFADE
	FM_VIEW_CROSSFADE_CIRCLE,	// Fades from previous to current view using expanding circle.
	FM_VIEW_CROSSFADE_FB_MASK,	// Fades from previous to current using mask stored in framebuffer alpha.

	// These apply to FT_VIEW_MOTION_BLUR_FILTER
	FM_VIEW_MB_IN_AND_OUT_ALPHA, // Motion blur filter in and out alpha blur
	FM_VIEW_MB_IN_AND_OUT_SATURATE, // Motion blur filter in and out saturated blur
	FM_VIEW_MB_IN_ALPHA, // Motion blur filter in alpha blur
	FM_VIEW_MB_OUT_ALPHA, // Motion blur filter out alpha blur
	FM_VIEW_MB_IN_SATURATE, // Motion blur filter in saturated blur
	FM_VIEW_MB_OUT_SATURATE, // Motion blur filter out saturated blur
	FM_VIEW_MB_END_PAN_ALPHA, // Moton blur on screen pan (for camera tracks object mode)

	FM_VIEW_DEFAULT,	//Default filter that's enabled when all others are off.

	// NOTE: This has to be the last entry in this enum.
	// Add new entries before this one.  jba.
	FM_VIEW_MB_PAN_ALPHA, // Moton blur on screen pan (for camera tracks object mode)

};
