import arcpy
from UpdatePointAttributes import addPolyAttributes

sgid = r'C:\sde\SGID_internal\SGID_agrc.sde'
dirs = {'N': ['N', 'NORTH', 'NO'], 'S': ['S', 'SOUTH', 'SO'], 'E': ['E', 'EAST', 'EA'], 'W': ['W', 'WEST', 'WE']}
sTypeDir = {'ALY':'ALLEY', 'AVE':'AVENUE', 'BAY':'BAY', 'BND':'BEND', 'BLVD':'BOULEVARD', 'CYN':'CANYON', \
            'CTR':'CENTER', 'CIR':'CIRCLE', 'COR':'CORNER', 'CT':'COURT', 'CV':'COVE', 'CRK':'CREEK', \
            'CRES':'CRESCENT', 'XING':'CROSSING', 'DR':'DRIVE', 'EST':'ESTATE', 'ESTS':'ESTATES', \
            'EXPY':'EXPRESSWAY', 'FLT':'FLAT', 'FRK':'FORK', 'FWY':'FREEWAY', 'GLN':'GLEN', 'GRV':'GROVE', \
            'HTS':'HEIGHTS','HWY':'HIGHWAY', 'HL':'HILL', 'HOLW':'HOLLOW', 'JCT':'JUNCTION', 'LN':'LANE', \
            'LNDG':'LANDING', 'LOOP':'LOOP', 'MNR':'MANOR','MDW':'MEADOW', 'MDWS':'MEADOWS', 'PARK':'PARK', 'PKWY':'PARKWAY', \
            'PASS':'PASS', 'PL':'PLACE', 'PLZ':'PLAZA', 'PT':['POINT', 'POINTE'], 'RAMP':'RAMP', 'RNCH':'RANCH', 'RDG':'RIDGE', \
            'RD':'ROAD', 'RST':'REST', 'RTE':'ROUTE', 'ROW':'ROW', 'RUN':'RUN', 'SQ':'SQUARE', 'ST':'STREET', \
            'TER':'TERRACE', 'TRCE':'TRACE', 'TRL':'TRAIL', 'VW':'VIEW', 'VLG':'VILLAGE', 'WAY':['WY','WAY']}


def returnKey(word, d):
    if word == None:
        word = ''
    for key, value in d.items():
        if word == '':
            return ''
        if word == key:
            return key
        if type(value) is str:
            if word == value:
                return key
        else:
            for v in value:
                if word == v:
                    return key
    return ''


def ParkCity():
    PCandCounty_points = r'C:\ZBECK\Addressing\Summit\SummitCounty.gdb\SummitCoAddrs'
    agrcAddPts_PC = r'C:\ZBECK\Addressing\Summit\Summit.gdb\AddressPoints_ParkCity'

    truncateOldCountyPts(agrcAddPts_PC)

    PCandCounty_FLDS = ['ADDR_HN', 'ADDR_PD', 'ADDR_PT', 'ADDR_SN', 'ADDR_ST', 'ADDR_SD', 'SERIAL', 'CITY', 'Unit', \
                        'SHAPE@', 'ZIP', 'CODE']

    pcDict = {
        'SERIAL': ['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
        'CITY': ['SGID.BOUNDARIES.Municipalities', 'NAME'],
        'ZIP': ['SGID.BOUNDARIES.ZipCodes', 'ZIP5'],
        'CODE': ['SGID.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid, PCandCounty_points, pcDict)
    print('updated Park City polygon attributes')

    hwyList = ['STATE ROAD', 'STATE RD', 'STATE HWY', 'STATE  RD', 'STATE   RD', 'STATE   HWY', 'SR', 'HWY',
               'HIGHWAY']

    with arcpy.da.SearchCursor(PCandCounty_points, PCandCounty_FLDS) as sCursor, \
            arcpy.da.InsertCursor(agrcAddPts_PC, agrcAddFLDS) as iCursor:
        for row in sCursor:
            if row[7] == 'Park City' and row[0] != '':
                addNum = row[0]
                if row[2] not in hwyList:
                    pre_street = ' '.join(row[2].split())
                else:
                    pre_street = 'HWY'

                preDir = returnKey(row[1], dirs)

                sName = f'{pre_street} {row[3]}'.strip()
                if sName.startswith('1/2'):
                    sName = sName.strip('1/2')
                    addNumSuf = '1/2'
                else:
                    addNumSuf = ''

                if ' ' in row[4] and len(row[4]) > 2:
                    sName = f'{sName} {row[4].split()[1]}'
                    sType = returnKey(row[4].split()[0], sTypeDir)
                else:
                    sType = returnKey(row[4], sTypeDir)

                sufDir = returnKey(row[5], dirs)

                unitID = row[8]

                if unitID != '':
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir} # {unitID}'
                else:
                    fullAdd = f'{addNum} {addNumSuf} {preDir} {sName} {sType} {sufDir}'

                addSys = row[6]
                utahAddID = f'{addSys} | {fullAdd}'
                zip = row[10]
                usng = row[11]
                parcelID = removeBadValues(row[6], errorList)
                loadDate = None
                shp = row[9]

                iCursor.insertRow(
                    (addSys, utahAddID, fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', '', \
                     '', unitID, 'PARK CITY (SUMMIT CO)', zip, '49043', 'UT', '', '', '', '', 'PARK CITY',
                     loadDate, 'COMPLETE', '', None, '', '', usng, shp))


ParkCity()
