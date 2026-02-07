# -*- coding: utf-8 -*-
"""
Difference of DEMs (DoD) processing workflow
--------------------------------------------
This script was originally generated using ArcGIS ModelBuilder and
subsequently cleaned and documented for reproducibility.

Purpose:
- Compute DEM of Difference (DoD)
- Apply a minimum Level of Detection (mLoD) threshold
- Isolate erosion signals
- Estimate erosion volume using zonal statistics

Author: Charles Ghartey
Generated: 2024-07-05
"""

import arcpy
from arcpy.sa import *     # Spatial Analyst tools
from arcpy.ia import *     # Image Analyst tools
from sys import argv


def DoDfin(
    dem_later="August_2019.tif",
    dem_earlier="May_2019.tif",
    mLoD=0.2,
    dod_raw="Aug_May2019",
    dod_threshold_mask="thres2019",
    dod_reclass="Reclass_thre2019",
    dod_thresholded="thres_fin2019",
    erosion_mask="ero2019",
    erosion_stats="ZonalSt_ero2019"
):
    """
    Computes a thresholded Difference of DEMs (DoD) and estimates erosion volume.

    Parameters
    ----------
    dem_later : str
        Later DEM (e.g., August 2019)
    dem_earlier : str
        Earlier DEM (e.g., May 2019)
    mLoD : float
        Minimum Level of Detection (vertical uncertainty threshold, meters)
    """

    # Allow overwriting outputs if rerunning
    arcpy.env.overwriteOutput = True

    # Check out required licenses
    arcpy.CheckOutExtension("Spatial")
    arcpy.CheckOutExtension("ImageAnalyst")
    arcpy.CheckOutExtension("3D")

    # ------------------------------------------------------------------
    # Step 1: Compute raw DoD (Later DEM - Earlier DEM)
    # ------------------------------------------------------------------
    dod = Raster(dem_later) - Raster(dem_earlier)
    dod.save(dod_raw)

    # ------------------------------------------------------------------
    # Step 2: Apply minimum Level of Detection (mLoD)
    # Retain only cells exceeding ±mLoD
    # ------------------------------------------------------------------
    dod_mask = (dod > float(mLoD)) | (dod < -float(mLoD))
    dod_mask.save(dod_threshold_mask)

    # ------------------------------------------------------------------
    # Step 3: Reclassify threshold mask to binary (1 = significant change)
    # ------------------------------------------------------------------
    dod_binary = Reclassify(
        dod_mask,
        "Value",
        RemapValue([[0, "NODATA"], [1, 1]])
    )
    dod_binary.save(dod_reclass)

    # ------------------------------------------------------------------
    # Step 4: Apply threshold mask to DoD
    # Removes changes below detection limit
    # ------------------------------------------------------------------
    dod_filtered = dod_binary * dod
    dod_filtered.save(dod_thresholded)

    # ------------------------------------------------------------------
    # Step 5: Identify erosion cells (negative elevation change)
    # ------------------------------------------------------------------
    erosion = Con(dod_filtered < 0, 1, 0)
    erosion.save(erosion_mask)

    # ------------------------------------------------------------------
    # Step 6: Zonal statistics for erosion
    # Used to compute erosion volume
    # ------------------------------------------------------------------
    arcpy.ia.ZonalStatisticsAsTable(
        in_zone_data=erosion,
        zone_field="Value",
        in_value_raster=dod_filtered,
        out_table=erosion_stats,
        ignore_nodata="DATA",
        statistics_type="ALL"
    )

    # ------------------------------------------------------------------
    # Step 7: Compute erosion volume (Area × Median elevation change)
    # ------------------------------------------------------------------
    arcpy.management.AddField(
        in_table=erosion_stats,
        field_name="Volume",
        field_type="DOUBLE"
    )

    arcpy.management.CalculateField(
        in_table=erosion_stats,
        field="Volume",
        expression="!AREA! * !MEDIAN!",
        expression_type="PYTHON3"
    )


if __name__ == "__main__":
    # Workspace environment
    with arcpy.EnvManager(
        workspace=r"Y:\GHARTEY\AkyemData\Backup\August_All_min\DOD_fin_arc\Default.gdb",
        scratchWorkspace=r"Y:\GHARTEY\AkyemData\Backup\August_All_min\DOD_fin_arc\Default.gdb"
    ):
        DoDfin(*argv[1:])
