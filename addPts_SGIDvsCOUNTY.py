import arcpy

ptsSGID = r'C:\sde\SGID_internal\SGID_agrc.sde\SGID.LOCATION.AddressPoints'
sql = """"{}" = '{}'""".format('CountyID', '49043')
ptsSGID_fl = arcpy.MakeFeatureLayer_management(ptsSGID, 'ptsSGID_fl', sql)
ptsCOUNTY = r'C:\ZBECK\Addressing\Summit\Summit.gdb\AddressPoints_Summit'

pcAddList = []

#with arcpy.da.SearchCursor(ptsSGID_fl, ['UTAddPtID', 'City']) as sCursor:
with arcpy.da.SearchCursor(ptsCOUNTY, ['UTAddPtID', 'City']) as sCursor:
    for row in sCursor:
        if row[1].replace(' (SUMMIT CO)', '') == 'PARK CITY':
            pcAddList.append(row[0])

#with arcpy.da.SearchCursor(ptsCOUNTY, ['UTAddPtID', 'City']) as sCursor:
with arcpy.da.SearchCursor(ptsSGID_fl, ['UTAddPtID', 'City']) as sCursor:
    for row in sCursor:
        if row[1] == 'PARK CITY' and row[0].replace(' (SUMMIT CO)', '') not in pcAddList and '#' not in row[0]:
            print(row[0].replace(' (SUMMIT CO)', ''))


