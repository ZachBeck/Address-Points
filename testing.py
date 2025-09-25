# from sweeper.address_parser import Address
# test_address = Address('4036 S Deer Valley Dr N')
# print(test_address.street_direction)

import arcpy
import geopandas as gpd
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
from UpdatePointAttributes import addPolyAttributes
from pathlib import Path

# from arcpy import env
# from arcpy.sa import *
# arcpy.CheckOutExtension('spatial')
# env.workspace = r'C:\ZBECK\MISC_WORK\MiscMapRequests\GreatSaltLake\downloads\biowest1'
# #Define ranges for entire DEM
# newRange = RemapRange([[4214, 9771, 9771]])
# outRaster = Reclassify('gsldem_ft', 'Value', newRange)
# outRaster.save('gsldem_ft2.tif')
sgid = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde'))
intersectPolyDict = {'USNG': ['SGID.INDICES.NationalGrid', 'USNG', '']}
inpts = r'C:\ZBECK\Addressing\Sanpete\Sanpete.gdb\WebEditorSchema'
addPolyAttributes(sgid, inpts, intersectPolyDict)