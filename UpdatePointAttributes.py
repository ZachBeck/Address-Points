import arcpy
import os

sgid10 = r'C:\ZBECK\Addressing\SGID10.sde'


def addPolyAttributes(sgid10, pts, polyLyrDict):

    arcpy.env.workspace = os.path.dirname(pts)
    arcpy.env.overwriteOutput = True

    nearFLDS = ['IN_FID', 'NEAR_FID', 'NEAR_DIST']

    for lyr in polyLyrDict:

        polyFC = sgid10 + '\\' + polyLyrDict[lyr][0]
        print (polyFC)

        nearTBL = '{}_nearTbl'.format(lyr)

        arcpy.GenerateNearTable_analysis(pts, polyFC, nearTBL, '1 Meters', 'NO_LOCATION', 'NO_ANGLE', 'CLOSEST')

        pt2Poly_Dict = {}
        polyDict = {}

        polyLyrFLDS = ['OBJECTID', polyLyrDict[lyr][1]]

        with arcpy.da.SearchCursor(nearTBL, nearFLDS) as sCursor:
            for row in sCursor:
                pt2Poly_Dict[row[0]] = row[1]
                polyDict.setdefault(row[1])
        with arcpy.da.SearchCursor(polyFC, polyLyrFLDS) as sCursor:
            for row in sCursor:
                if row[0] in polyDict:
                    polyDict[row[0]] = row[1]

        ucursorFLDS = ['OBJECTID', lyr]
        ucursor = arcpy.da.UpdateCursor(pts, ucursorFLDS)
        for urow in ucursor:
            try:
                if pt2Poly_Dict[urow[0]] in polyDict:
                   urow[1] =  polyDict[pt2Poly_Dict[urow[0]]]
            except:
                urow[1] = ''

            ucursor.updateRow(urow)

        arcpy.Delete_management(nearTBL)


def updateAddPtID(inPts):
    flds = ['AddSystem', 'UTAddPtID', 'FullAdd']
    with arcpy.da.UpdateCursor(inPts, flds) as uCursor:
        for urow in uCursor:
            urow[1] = urow[0] + ' | ' + urow[2]
            uCursor.updateRow(urow)

    del uCursor
