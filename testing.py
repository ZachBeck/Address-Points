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
import re
pattern = r'\s*\([^)]*[\)]?'

s_list = ['The Ranches Road (250 N)', 'S Wasatchback Drive (6600 N(', 'S Shoreline Drive (pending)', 'W Zion Rd', 'North Village Lane (3525 N', 'North Village Road (5500 W)', 'Upper Townhome Lane (5550 W)', 'W Wasatchback Drive (6600 N)']
for s in s_list:
    cleaned_s = re.sub(pattern, '', s)
    print(cleaned_s)