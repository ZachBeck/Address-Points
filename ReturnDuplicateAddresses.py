import arcpy

#fldList should be the field with duplicates to find and the Shape field
def returnDuplicateAddresses(inPts, fldList):

    if 'OBJECTID' not in fldList:
        fldList.append('OBJECTID')

    seenDict = {}
    dupList = []
    duplicates = {}

    with arcpy.da.SearchCursor(inPts, fldList) as sCursor:
        for row in sCursor:
            if row[0] not in seenDict:
                seenDict.setdefault(row[0])
            else:
                dupList.append(row[0])

        sCursor.reset()

        for row in sCursor:
            if row[0] in dupList:
                dupes = duplicates.setdefault(row[-1], [])
                dupes.extend([row[0], row[1]])

        return duplicates


def updateErrorPts(updatePts, errorFlds, duplicateDictionary):

    iCursor = arcpy.da.InsertCursor(updatePts, errorFlds)

    for d in duplicateDictionary:
        add = duplicateDictionary[d][0]
        note = 'duplicate address'
        shp = duplicateDictionary[d][1]

        iCursor.insertRow((add, note, shp))