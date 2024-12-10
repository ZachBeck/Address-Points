import arcpy
import os
from pathlib import Path

def findMissingPts(inCountySGID, compareCounty):

    ws = os.path.join(r'C:\ZBECK\Addressing', inCountySGID)
    arcpy.env.workspace = ws
    arcpy.env.overwriteOutput = True
    outShape = '{}_Changes.shp'.format(inCountySGID)
    proj = arcpy.Describe(compareCounty).SpatialReference

    outFlds = ['ADDRESS', 'NOTES', 'SHAPE@']

    arcpy.CreateFeatureclass_management(ws, outShape, 'POINT', '', '', '', proj)
    arcpy.AddField_management(outShape, outFlds[0], 'TEXT')
    arcpy.AddField_management(outShape, outFlds[1], 'TEXT')
    arcpy.DeleteField_management(outShape, 'Id')

    #addPts_sgid10 = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.LOCATION.AddressPoints'
    addPts_sgid = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde', 'SGID.LOCATION.AddressPoints'))

    fipsDict = {'Beaver': '49001', 'Box Elder': '49003', 'Cache': '49005', 'Carbon': '49007', 'Daggett': '49009', \
                'Davis': '49011', 'Duchesne': '49013', 'Emery': '49015', 'Garfield': '49017', 'Grand': '49019', \
                'Iron': '49021', 'Juab': '49023', 'Kane': '49025', 'Millard': '49027', 'Morgan': '49029', \
                'Piute': '49031', 'Rich': '49033', 'Salt Lake': '49035', 'San Juan': '49037', 'Sanpete': '49039', \
                'Sevier': '49041', 'Summit': '49043', 'Tooele': '49045', 'Uintah': '49047', 'Utah': '49049', \
                'Wasatch': '49051', 'Washington': '49053', 'Wayne': '49055', 'Weber': '49057'}

    sql = """"CountyID" = """ + "'" + fipsDict[inCountySGID] + "'"

    sgidCounty_FL = arcpy.MakeFeatureLayer_management(addPts_sgid, 'addPts_FL', sql)

    sgidPtDict = {}
    cntyPtDict = {}

    with arcpy.da.SearchCursor(sgidCounty_FL, ['UTAddPtID', 'SHAPE@']) as sCursor:
        for row in sCursor:
            address = row[0].replace('HIGHWAY', 'HWY').replace(' SR ', ' HWY ').replace(' US ', ' HWY ')
            if address not in sgidPtDict:
                sgidPtDict.update({address:row[1]})

    del sCursor

    iCursor = arcpy.da.InsertCursor(outShape, outFlds)

    with arcpy.da.SearchCursor(compareCounty, ['UTAddPtID', 'SHAPE@']) as sCursor:
        for row in sCursor:
            address = row[0]
            shp = row[1]
            if address not in cntyPtDict:
                cntyPtDict.update({address:shp})
            # if address not in sgidPtDict:
            #     notes = 'changed address or missing point 1'
            #     iCursor.insertRow((address, notes, shp))
    del sCursor

    for d in sgidPtDict:
        #print (d)
        if d not in cntyPtDict:
            notes = 'changed address or missing point 2'
            iCursor.insertRow((d, notes, sgidPtDict[d]))

