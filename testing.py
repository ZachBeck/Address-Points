# from sweeper.address_parser import Address
# test_address = Address('4036 S Deer Valley Dr N')
# print(test_address.street_direction)

# import arcpy
# import geopandas as gpd
# sanpete_ugrc = r'C:\ZBECK\Addressing\Sanpete\Sanpete.gdb\AddressPoints_Sanpete'
# sanpete_vista = r'C:\ZBECK\Addressing\Sanpete\Sanpete.gdb\AddressPoints_SanpeteVista'

# vista_flds = ['UTAddPtID']
# ugrc_flds = ['UTAddPtID', 'found_vista']

# vista_dict = {}

# with arcpy.da.SearchCursor(sanpete_vista, vista_flds) as scursor:
#     for row in scursor:
#         vista_dict.setdefault(row[0])
# with arcpy.da.UpdateCursor(sanpete_ugrc, ugrc_flds) as ucursor:
#     for row in ucursor:
#         if row[0] in vista_dict:
#             row[1] = 1
#         else:
#             row[1] = 0

#         ucursor.updateRow(row)
import arcpy
# from UpdatePointAttributes import addPolyAttributes
# from pathlib import Path

# from arcpy import env
# from arcpy.sa import *
# arcpy.CheckOutExtension('spatial')
# env.workspace = r'C:\ZBECK\MISC_WORK\MiscMapRequests\GreatSaltLake\downloads\biowest1'
# #Define ranges for entire DEM
# newRange = RemapRange([[4214, 9771, 9771]])
# outRaster = Reclassify('gsldem_ft', 'Value', newRange)
# outRaster.save('gsldem_ft2.tif')

# sgid = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde'))
# intersectPolyDict = {'USNG': ['SGID.INDICES.NationalGrid', 'USNG', '']}
# inpts = r'C:\ZBECK\Addressing\Sanpete\Sanpete.gdb\WebEditorSchema'
# addPolyAttributes(sgid, inpts, intersectPolyDict)

# import os
# import arcpy, pprint

# old_ubm_data = r'C:\Cache\MapData\UtahBaseMap-Data_WGS.gdb'
# old_sgid10 = r'C:\Cache\MapData\SGID10_WGS.gdb'
# old_hillshade = r'C:\Cache\MapData\HillshadePolygons.gdb'

# new_ubm_data = r'L:\caching\Data\UtahBaseMap-Data_WGS.gdb'
# new_sgid10 = r'L:\caching\Data\Backups\SGID10_WGS.gdb'
# new_hillshade = r'L:\caching\Data\HillshadePolygons.gdb'


# p = arcpy.mp.ArcGISProject(r'C:\TEMP\Hank\Basemap.aprx')
# m = p.listMaps('Lite')[0]
# for lyr in m.listLayers():
#     if lyr.isBroken:
#         print(lyr.name)
#         if lyr.supports('DATASOURCE'):
#             current_path = os.path.dirname(lyr.dataSource)
#             lyr_name = lyr.name
            
#             # if lyr.dataSource == os.path.join(old_ubm_data, lyr_name):
#             #     lyr.updateConnectionProperties(old_ubm_data, new_ubm_data)
#             #     print(os.path.join(new_ubm_data, lyr_name))
            
#             if lyr.dataSource == os.path.join(old_sgid10, lyr_name):
#                 print(lyr.dataSource)
#                 lyr.updateConnectionProperties(old_sgid10, new_sgid10)

#             # if lyr.dataSource == os.path.join(old_hillshade, lyr_name):
#             #     lyr.updateConnectionProperties(old_hillshade, new_hillshade)
# p.save()

import arcpy

# Set environment settings
arcpy.env.overwriteOutput = True

def find_nearby_points(input_fc, output_fc, search_radius="1 Meters"):
    """
    Identifies points within a specified distance of each other.
    """
    try:
        print(f"Analyzing {input_fc}...")

        # Perform a Spatial Join on itself
        # We use 'CLOSEST' and a search radius to find neighbors
        arcpy.analysis.SpatialJoin(
            target_features=input_fc,
            join_features=input_fc,
            out_feature_class=output_fc,
            join_operation="JOIN_ONE_TO_MANY",
            join_type="KEEP_COMMON",
            match_option="WITHIN_A_DISTANCE",
            search_radius=search_radius
        )

        # The spatial join will match a point to itself. 
        # We need to filter out records where TARGET_FID == JOIN_FID.
        # We also filter out duplicates (e.g., A matches B and B matches A) 
        # by using the 'less than' operator.
        
        layer_name = "joined_points_layer"
        arcpy.management.MakeFeatureLayer(output_fc, layer_name)
        
        query = "TARGET_FID <> JOIN_FID AND TARGET_FID < JOIN_FID"
        arcpy.management.SelectLayerByAttribute(layer_name, "NEW_SELECTION", query)

        # Export the final result of just the nearby pairs
        final_output = output_fc + "_Filtered"
        arcpy.management.CopyFeatures(layer_name, final_output)

        print(f"Success! Nearby points saved to: {final_output}")
        
    except arcpy.ExecuteError:
        print(arcpy.GetMessages(2))

if __name__ == "__main__":
    # Update these paths to your local data
    input_data = r"C:\ZBECK\SGID\incoming\Parks\Parks.gdb\Parks_UGRC_OSM_FeatureToPoint"
    output_data = r"C:\ZBECK\SGID\incoming\Parks\Parks.gdb\Parks_UGRC_OSM_Nearby"
    
    find_nearby_points(input_data, output_data)

