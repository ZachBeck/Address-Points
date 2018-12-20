import arcpy
import datetime, time
from xxhash import xxh64

def truncateOldCountyPts(inPts):
    pointCount = int(arcpy.GetCount_management(inPts).getOutput(0))
    if pointCount > 0:
        arcpy.TruncateTable_management(inPts)
        print 'Deleted {} points in {}'.format(pointCount, inPts)
    else:
        print 'No points to delete'

agrcAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', \
               'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', \
               'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor', \
               'ModifyDate', 'StreetAlias', 'Notes', 'USNG', 'SHAPE@']

cadFLDS = ['NUMB', 'STREETNAME', 'STREETTYPE', 'SUFFIXDIR', 'PREFIXDIR', 'SHAPE@']

sgid10 = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde'
cadPTS = r'C:\ZBECK\Addressing\Washington\WashingtonCAD.gdb\WashingtonCADpts2'
agrcPTS = r'C:\ZBECK\Addressing\Washington\WashingtonCAD.gdb\agrcCADpts'

truncateOldCountyPts(agrcPTS)

iCursor = arcpy.da.InsertCursor(agrcPTS, agrcAddFLDS)
today = str(datetime.datetime.today().strftime("%m/%d/%Y"))

with arcpy.da.SearchCursor(cadPTS, cadFLDS) as sCursor:
    for row in sCursor:
        addNum = row[0].strip()
        preDir = row[4].strip()
        sName = row[1].strip()
        sufDir = row[3].strip()
        sType = row[2].strip()
        ptType = 'CAD'
        fulladd = '{} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType)
        fulladd = ' '.join(fulladd.split())
        shp = row[5]

        iCursor.insertRow(('', '', fulladd, addNum, '', preDir, sName, sType, sufDir, '', '', \
                           '', '', '', '', '49053', 'UT', '', 'CAD', '', '', 'Dispatch Points', today, \
                           'COMPLETE', '', None, '', '', '', shp))
del iCursor

inputDict = {
'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
}


def deleteDuplicatePts(inPts, inFlds):
    with arcpy.da.SearchCursor(inPts, inFlds) as sCursor:
        digestDict = {}
        duplicateLst = []
        dupAddressPrintLst = []
        for row in sCursor:
            if row[1] != None:
                hash = xxh64(str(row[0] + row[1]))
                digest = hash.hexdigest()
                if digest not in digestDict:
                    digestDict.setdefault(digest)
                else:
                    duplicateLst.append(row[2])
                    dupAddressPrintLst.append(row[0])
            if row[1] == None:
                duplicateLst.append(row[2])
                dupAddressPrintLst.append(row[0])

        print dupAddressPrintLst

    if len(duplicateLst) >= 1:
        sql = '"OBJECTID" IN ({})'.format(', '.join(str(d) for d in duplicateLst))
        duplicatePts_FL = arcpy.MakeFeatureLayer_management(inPts, 'duplicatePts_FL', sql)
        print 'Deleted {} records'.format(len(duplicateLst))
        arcpy.DeleteFeatures_management(duplicatePts_FL)
    else:
        print 'No Duplicates to Delete'

def addPolyAttributes(sgid10, agrcAddPts, polyDict):

    for input in polyDict:

        print 'Starting ' + polyDict[input][0]

        addPtFL = arcpy.MakeFeatureLayer_management(agrcAddPts)

        polyFC = sgid10 + '\\' + polyDict[input][0]
        polyFL = arcpy.MakeFeatureLayer_management(polyFC)
        polyFL = arcpy.SelectLayerByLocation_management(polyFL, 'INTERSECT', addPtFL, '', 'NEW_SELECTION')

        polyFLD = polyDict[input][1]
        ptFLD = [input]

        scursor = arcpy.da.SearchCursor(polyFL, polyFLD)

        for polys in sorted(set(scursor)):

            uniquePoly = ''.join(polys)
            sql = """"{}" = '{}'""".format(polyFLD, uniquePoly)

            arcpy.SelectLayerByAttribute_management(polyFL, "NEW_SELECTION", sql)
            arcpy.SelectLayerByLocation_management(addPtFL, 'WITHIN', polyFL, '', 'NEW_SELECTION')

            ucursor = arcpy.da.UpdateCursor(addPtFL, ptFLD)

            for urow in ucursor:
                urow[0] = uniquePoly

                ucursor.updateRow(urow)

            del ucursor
        del scursor
        del polyFL

    flds = ['AddSystem', 'UTAddPtID', 'FullAdd']
    with arcpy.da.UpdateCursor(agrcAddPts, flds) as uCursor:

        for urow in uCursor:
            urow[1] = urow[0] + ' | ' + urow[2]

            uCursor.updateRow(urow)

        del uCursor

addPolyAttributes(sgid10, agrcPTS, inputDict)
deleteDuplicatePts(agrcPTS, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])

