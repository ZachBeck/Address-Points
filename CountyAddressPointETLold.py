import arcpy
import datetime, time
import sys
import agrc

from arcpy import env
from agrc import parse_address

global sgid10, agrcAddFLDS, errorList

sgid10 = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde'

today = str(datetime.datetime.today().strftime("%m/%d/%Y"))

agrcAddFLDS = ['AddSystem', 'UTAddPtID', 'FullAdd', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', \
               'SuffixDir', 'LandmarkName', 'Building', 'UnitType', 'UnitID', 'City', 'ZipCode', 'CountyID', 'State', \
               'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'LoadDate', 'Status', 'Editor', \
               'ModifyDate', 'StreetAlias', 'Notes', 'USNG', 'SHAPE@']

dirs = {'N': ['N', 'NORTH', 'NO'], 'S': ['S', 'SOUTH', 'SO'], 'E': ['E', 'EAST', 'EA'], 'W': ['W', 'WEST', 'WE']}

sTypeDir = {'ALY':'ALLEY', 'AVE':'AVENUE', 'BAY':'BAY', 'BND':'BEND', 'BLVD':'BOULEVARD', 'CYN':'CANYON', \
            'CTR':'CENTER', 'CIR':'CIRCLE', 'COR':'CORNER', 'CT':'COURT', 'CV':'COVE', 'CRK':'CREEK', \
            'CRES':'CRESCENT', 'XING':'CROSSING', 'DR':'DRIVE', 'EST':'ESTATE', 'ESTS':'ESTATES', \
            'EXPY':'EXPRESSWAY', 'FLT':'FLAT', 'FRK':'FORK', 'FWY':'FREEWAY', 'GLN':'GLEN', 'GRV':'GROVE', \
            'HTS':'HEIGHTS','HWY':'HIGHWAY', 'HL':'HILL', 'HOLW':'HOLLOW', 'JCT':'JUNCTION', 'LN':'LANE', \
            'LNDG':'LANDING', 'LOOP':'LOOP', 'MNR':'MANOR','MDW':'MEADOW', 'PARK':'PARK', 'PKWY':'PARKWAY', \
            'PASS':'PASS', 'PL':'PLACE', 'PLZ':'PLAZA', 'PT':'POINT', 'RAMP':'RAMP', 'RNCH':'RANCH', 'RDG':'RIDGE', \
            'RD':'ROAD', 'RTE':'ROUTE', 'ROW':'ROW', 'RUN':'RUN', 'SQ':'SQUARE', 'ST':'STREET', \
            'TER':'TERRACE', 'TRCE':'TRACE', 'TRL':'TRAIL', 'VW':'VIEW', 'VLG':'VILLAGE', 'WAY':'WAY', 'WY':'WAY'}

addNumSufList = ['1/8', '1/4', '1/3', '1/2', '2/3,' '3/4', 'A', 'B', 'C']

unitTypeDir = {'APT':'APARTMENT', 'BSMT':'BASEMENT', 'BLDG':'BUILDING', 'DEPT':'DEPARTMENT', 'FL':'FLOOR', 'FLR':'FLOOR',\
               'FRNT':'FRONT', 'HNGR':'HANGAR', 'LBBY':'LOBBY', 'LOT':'LOT', 'LOWR':'LOWER', 'OFC':'OFFICE', \
               'PH':'PENTHOUSE', 'PIER':'PIER', 'REAR':'REAR', 'RM':'ROOM', 'SIDE':'SIDE', 'SLIP':'SLIP', \
               'SPC':'SPACE', 'STOP':'STOP', 'STE':'SUITE', 'TRLR':'TRAILER', 'UNIT':'UNIT', 'UPPR':'UPPER'}

errorList = [None, False, 'None', '', ' ', '#', '?', '0', '*', '<Null>']


def checkWord(word, d):
    for key, value in d.iteritems():
        if word in value:
            return key
    # if nothing is found
    return ''

def removeBadValues(word, badVals):
    if word in badVals:
        word = ''
    return word.upper().strip()

def addNone(word, badVals):
    if word in badVals:
        word = None
    return word

def formatValues(word, inValues):
    removeBadValues(word, errorList)
    if word != None:
        if word.upper().strip() in inValues:
            return word.upper().strip()
        return ''
    return ''

def formatUnitID(unitID):
    unitID = unitID.strip()
    if unitID.startswith('#') is True:
        if unitID[1] != ' ':
            return '{} {}'.format(unitID[0], unitID.strip('#')).upper()
        return unitID
    elif unitID.startswith('#') is False:
        if unitID not in errorList:
            return '# ' + unitID.upper()
        return unitID

def formatAddressNumber(addNum):
    addNum.strip()
    if addNum.startswith('0'):
        addNum = addNum.lstrip('0')
    return addNum

def removeDuplicateWords(words):
  slist = words.split()
  return " ".join(sorted(set(slist), key=slist.index))

def beaverCounty():
    beaverCoAddPts = r'C:\ZBECK\Addressing\Beaver\Address_pts.shp'
    agrcAddPts_beaverCo = r'C:\ZBECK\Addressing\Beaver\Beaver.gdb\AddressPoints_Beaver'

    beaverCoAddFLDS = ['Address_', 'Prefix', 'St_Name', 'Dir_Type', 'Unit_Num', 'Grid', 'SHAPE@']

    checkRequiredFields(beaverCoAddPts, beaverCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_beaverCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(beaverCoAddPts, beaverCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] and row[1] not in errorList:
                addNum = row[0]
                preDir = formatValues(row[1], dirs)
                sName = row[2].upper().replace('HIGHWAY', 'HWY')
                sufDir = formatValues(row[3], dirs)
                sType = formatValues(row[3], sTypeDir)

                unitID = removeBadValues(row[4], errorList)
                if unitID != '':
                    unitID_hash = '# ' + unitID
                else:
                    unitID_hash = ''

                addSys = row[5].upper()
                shp = row[6]

                fullAdd = '{} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitID_hash)
                fullAdd = ' '.join(fullAdd.split())

                utPtID = '{} | {}'.format(addSys, fullAdd)

                iCursor.insertRow((addSys, utPtID, fullAdd, addNum, '', preDir, sName, sType, sufDir, '', '',\
                                   '', unitID, '', '', '49001', 'UT', '', '', '', '', 'BEAVER COUNTY', today,\
                                   'COMPLETE', '', None, shp))

    del iCursor

    intersectPolyDict = {'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
                         'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']}

    addPolyAttributes(sgid10, agrcAddPts_beaverCo, intersectPolyDict)


def boxElderCounty():
    boxelderCoAddPts = r'C:\ZBECK\Addressing\BoxElder\Address_December13th2016.gdb\Address_Pts'
    agrcAddPts_boxelderCo = r'C:\ZBECK\Addressing\BoxElder\BoxElder.gdb\AddressPoints_BoxElder'

    boxelderCoAddFLDS = ['FullAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', 'UnitNumber', 'UnitType', 'City', \
                         'ZipCode', 'Parcel_ID', 'Structure', 'COMPLEX_NA', 'Use_Classi', 'last_edi_1', 'SHAPE@']

    useDict = {'AGR':'Agricultural', 'COM':'Commercial', 'EDU':'Education', 'GOV':'Government', 'MED':'Other', 'RES':'Residential',\
              'MHU':'Residential', 'MOB':'Residential', 'REL':'Other', 'VAC':'Vacant'}

    excludeUnit = ['UPSTAIRS', 'UP', 'OFFICE', 'MANAGER', 'DOWNSTAIRS', 'DOWN', 'CLUB', 'BASEMENT']

    checkRequiredFields(boxelderCoAddPts, boxelderCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_boxelderCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(boxelderCoAddPts, boxelderCoAddFLDS) as sCursor:
        for row in sCursor:
            addSys = ''
            addNum = row[1]

            if ' ' in addNum:
                addNumSuf = addNum.split()[1]
                addNum = addNum.split()[0]
            else:
                addNumSuf = ''

            preDir = removeBadValues(row[2], errorList)
            sName = row[3]

            if row[4] in errorList:
                sType = ''
            else:
                sType = row[4]

            sufDir = removeBadValues(row[5], errorList)
            if sType != '':
                sufDir = ''

            if row[6] not in errorList:
                unitNum = row[6].strip().upper()
                if unitNum not in excludeUnit:
                    fullAddUnitNum = unitNum
            else:
                unitNum = ''
                fullAddUnitNum = ''

            if row[7] not in errorList:
                unitType = unitTypeDir[row[7]]
                unitTypeAbrv = row[7]
            else:
                unitType = ''
                unitTypeAbrv = ''

            if fullAddUnitNum != '' and unitType == '':
                fullAddUnitNum = ''

            city = row[8]
            zip = row[9]
            parcelID = row[10]
            structure = removeBadValues(row[11], errorList)
            building = removeBadValues(row[12], errorList)

            if row[13] in useDict:
                ptType = useDict[row[13]]
            elif row[13] in errorList:
                ptType = ''
            else:
                ptType = row[13]

            addSource = 'BOX ELDER COUNTY'
            modDate = row[14]
            loadDate = today
            shp = row[15]

            fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sType, sufDir, unitTypeAbrv, fullAddUnitNum)
            fullAdd = ' '.join(fullAdd.split())

            iCursor.insertRow((addSys, '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', building, unitType,\
                               unitNum, city, zip, '49003', 'UT', '', ptType, structure, parcelID, addSource, loadDate, \
                               'COMPLETE', '', modDate, '', '', '', shp))

    del iCursor
    del sCursor


    inputDict = {'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
                 'USNG':['SGID10.INDICES.NationalGrid', 'USNG']}

    addPolyAttributes(sgid10, agrcAddPts_boxelderCo, inputDict)


def cacheCounty():
    cacheCoAddPts = r'C:\ZBECK\Addressing\Cache\cache_MAL.gdb\cache_MAL_7_6_2016'
    agrcAddPts_cacheCo = r'C:\ZBECK\Addressing\Cache\Cache.gdb\AddressPoints_Cache'

    cacheCoAddFLDS = ['addsystem', 'fulladd', 'addnum', 'addnumsuffix', 'prefixdir', 'streetname', 'streettype', 'suffixdir', \
                      'landmarkname', 'building', 'unittype', 'unitid', 'ptlocation', 'pttype', 'structure', 'parcelid', \
                      'addsource', 'last_edited_date', 'objectid', 'AGRC_FLAG', 'last_edited_user', 'SHAPE@']


    checkRequiredFields(cacheCoAddPts, cacheCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_cacheCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(cacheCoAddPts, cacheCoAddFLDS) as sCursor:
        for row in sCursor:
            fulladd = removeBadValues(row[1], errorList)
            addnum = removeBadValues(row[2], errorList)
            addnumsuf = removeBadValues(row[3], errorList)
            predir = formatValues(row[4], dirs)
            sName = removeBadValues(row[5], errorList)
            sType = formatValues(row[6], sTypeDir)
            sufdir = formatValues(row[7], dirs)
            landName = removeBadValues(row[8], errorList)
            building = removeBadValues(row[9], errorList)
            unitType = formatValues(row[10], unitTypeDir)
            unitId = removeBadValues(row[11], errorList)
            parcelId = removeBadValues(row[15], errorList)
            addSrc = removeBadValues(row[16], errorList)
            modDate = removeBadValues(row[17], errorList)
            loadDate = today
            oId = row[18]
            agrcFlag = row[19]
            editor = removeBadValues(row[20], errorList)
            shp = row[21]

            if addnum != '':
                if '[Bad pre/suf direction]' not in agrcFlag:

                    for a in addNumSufList:
                        if a in addnum:
                            addnumsuf = addnum.split()[1]
                            addnum = addnum.split()[0]
                    if '.5' in addnum:
                        addnumsuf = '1/2'
                        addnum = addnum.split('.')[0]

                    zAdd = '{} {} {} {} {} {} {} {}'.format(addnum, addnumsuf, predir, sName, sType, sufdir, unitType, unitId)
                    zAdd = ' '.join(zAdd.split())

                    iCursor.insertRow(('', '', zAdd, addnum, addnumsuf, predir, sName, sType, sufdir, landName, building, unitType, unitId, '',\
                                       '', '49005', 'UT', '', '', '', parcelId, 'Cache County', loadDate, 'COMPLETE', editor, modDate, shp))

    del sCursor
    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']
    }

    addPolyAttributes(sgid10, agrcAddPts_cacheCo, inputDict)


def carbonCounty():
    carbonCoAddPts = r'C:\ZBECK\Addressing\Carbon\CarbonUpdates.gdb\SOURCE\CarbonCoUpdates_03202015'
    agrcAddPts_carbonCo = r'C:\ZBECK\Addressing\Carbon\CarbonUpdates.gdb\AddressPoints_Carbon'
    carbonErrorPts = r'C:\ZBECK\Addressing\Carbon\CarbonAddressErrors.gdb\CarbonErrorPts'

    carbonCoAddFLDS = ['NAME', 'BUILD_TYPE', 'WHOLE_ADD', 'INDIC_ADDR', 'PRE_DIR', 'ST_NAME', 'ST_TYPE', 'SUF_DIR', 'UNIT_NUM', \
                       'BLDG_NUM', 'PARCEL_NUM', 'GPS_DATE', 'SHAPE@']

    badVals = [None, '', ' ', '--', '?']

    type = {
    'other' : ['GOVERMENT', 'EDUCATIONAL', 'FIRE HYDRANT', 'MISSING', 'OTHER', 'OUTBUILDING', 'OUT BUILDING', 'PUBLIC', 'PUBLIC WATER TANK', 'RELIGIOUS', 'STREET SIGN', 'TRAIN', 'WATER TANK'],
    'residential' : ['RESIDENTIAL', 'RESIDEENTIAL', 'RESIDENTIAL/COMMERCI'],
    'commercial' : ['COMMERCIAL', 'GARAGE', 'HELPER GUN CLUB', ''],
    'industrial': ['UTILITY']
    }

    units = {'APT' : ['APT.'], 'STE' : ['STE.', 'SUITE']}

    checkRequiredFields(carbonCoAddPts, carbonCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_carbonCo, agrcAddFLDS)
    iErrorCursor = arcpy.da.InsertCursor(carbonErrorPts, carbonCoAddFLDS)

    with arcpy.da.SearchCursor(carbonCoAddPts, carbonCoAddFLDS) as sCursor_carbon:
        for row in sCursor_carbon:

            fullAdd = row[2]
            if fullAdd not in badVals and fullAdd[0].isdigit():
                address = parse_address.parse(fullAdd)

                if row[8] not in badVals:
                    unitId = row[8].replace('.', '').replace('SUITE', 'STE')
                    if unitId.isdigit():
                        unitId = '#' + row[8]
                    fullAdd = fullAdd + ' ' + unitId
                else:
                    unitId = ''

                addNum = address.houseNumber
                streetName = address.streetName
                preDir = address.prefixDirection

                #if preDir == None and

                sufDir = address.suffixDirection

                streetType = address.suffixType
                if streetType == None and sufDir == None and [6] not in badVals:
                    streetType = checkWord(row[6], parse_address.sTypes)
                    fullAdd = fullAdd + ' ' + streetType

                if row[0] not in badVals:
                    landmark = row[0]
                else:
                    landmark = ''

                building = row[9]
                parcel = row[10]
                unitType = row[1]

                ptType = checkWord(unitType, type)
                if ptType == False:
                    ptType = ''

                addSys = ''
                utAddId = ''
                addNumSuf = ''
                city = ''
                zip = ''
                fips = '49007'
                state = 'UT'
                ptLocation = ''
                structure = ''
                parcel = row[10]
                addSource = 'CARBON COUNTY'
                loadDate = today
                status = 'COMPLETE'
                editor = ''
                #modified = row[11]
                shp = row[12]


            elif fullAdd and row[5] not in badVals and row[3].isdigit():

                if '#' in row[3]:
                    addNum = row[3].split()[0]
                if len(row[3]) <= 4:
                    addNum = row[3]
                else:
                    continue

                addNum = row[3]
                preDir = checkWord(row[4], dirs)
                streetName = row[5]
                streetType = checkWord(row[6], parse_address.sTypes)
                sufDir = checkWord(row[7], dirs)

                if row[8] not in badVals:
                    unitId = row[8].replace('.', '').replace('SUITE', 'STE')
                    if unitId.isdigit():
                        unitId = '#' + row[8]
                else:
                    unitId = ''

                if streetType == '' or streetType == ' ':
                    fullAdd = '{0} {1} {2} {3} {4}'.format(addNum, preDir, streetName, sufDir, unitId)
                    fullAdd = ' '.join(fullAdd.split())

                else:
                    fullAdd = '{0} {1} {2} {3} {4}'.format(addNum, preDir, streetName, streetType, unitId)
                    fullAdd = ' '.join(fullAdd.split())


                if row[0] not in badVals:
                    landmark = row[0]
                else:
                    landmark = ''

                building = row[9]
                parcel = row[10]
                unitType = row[1]

                ptType = checkWord(unitType, type)
                if ptType == False:
                    ptType = ''

                addSys = ''
                utAddId = ''
                addNumSuf = ''
                city = ''
                zip = ''
                fips = '49007'
                state = 'UT'
                ptLocation = ''
                structure = ''
                parcel = row[10]
                addSource = 'CARBON COUNTY'
                loadDate = today
                status = 'COMPLETE'
                editor = ''
                #modified = row[11]
                shp = row[12]

            else:
                continue


            iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                               unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                               status, editor, '9/9/1973', shp))


def davisCounty():
    davisCoAddPts = r'C:\ZBECK\Addressing\Davis\Davis.gdb\AddressPoints_DavisUpdates'
    agrcAddPts_davisCo = r'C:\ZBECK\Addressing\Davis\Davis.gdb\AddressPoints_Davis'

    davisCoAddFLDS = ['AddressNum', 'AddressN_1', 'UnitType', 'UnitNumber', 'RoadPrefix', 'RoadName', 'RoadNameTy', 'RoadPostDi', \
                      'FullAddres', 'ParcelID', 'LastUpdate', 'LastEditor', 'SHAPE@']

    checkRequiredFields(davisCoAddPts, davisCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_davisCo, agrcAddFLDS)


    with arcpy.da.SearchCursor(davisCoAddPts, davisCoAddFLDS) as sCursor_davis:
        for row in sCursor_davis:

            if row[0] == 0 and row[5] != 'Freeport Center':
                continue

            elif row[0] not in errorList or row[5] not in errorList:

                addNum = row[0]
                addNumSuf = formatValues(row[1], addNumSufList)

                unitType = formatValues(row[2], unitTypeDir).upper()
                if unitType != '':
                    unitTypeLong = unitTypeDir[unitType]
                else:
                    unitTypeLong = ''

                unitId = removeBadValues(row[3], errorList).upper()
                preDir = formatValues(row[4], dirs)

                streetName = removeBadValues(row[5], errorList).upper()
                for type in sTypeDir:
                    if streetName != 'FREEPORT CENTER':
                        if streetName.endswith(' ' + type):
                            streetName = streetName.strip(type).strip()
                        elif 'HIGHWAY' in streetName:
                            streetName = streetName.replace('HIGHWAY', 'HWY')


                streetType = parse_address.checkWord(row[6].upper(), parse_address.sTypes)
                streetType = removeBadValues(streetType, errorList)

                sufDir = formatValues(row[7], dirs)
                parcel = removeBadValues(row[9], errorList)

                if streetName == 'FREEPORT CENTER':
                    fullAdd = '{} {} {}'.format(streetName, unitType, unitId)
                    addNum = ''
                elif addNumSuf in addNumSufList:
                    fullAdd = '{} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, sufDir, streetType)
                    fullAdd = ' '.join(fullAdd.split())
                    fullAdd = removeDuplicateWords(fullAdd)
                else:
                    #fullAdd = removeDuplicateWords(row[8].split(',')[0].upper())
                    fullAdd = '{} {} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, streetName, sufDir, streetType, unitType, unitId)
                    fullAdd = ' '.join(fullAdd.split())
                    fullAdd = removeDuplicateWords(fullAdd)



                addSys = ''
                utAddId = ''
                landmark = ''
                building = ''
                city = ''
                zip = ''
                fips = '49011'
                state = 'UT'
                ptLocation = 'Unknown'
                ptType = 'Unknown'
                structure = 'Unknown'
                addSource = 'DAVIS COUNTY'
                loadDate = today
                status = 'COMPLETE'
                modified = row[10]
                editor = row[11]
                shp = row[12]


                iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                    unitTypeLong, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                    status, editor, modified, '', '', '', shp))

    del iCursor
    del sCursor_davis

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_davisCo, inputDict)


def juabCounty():
    juabCoAddPts = r'C:\ZBECK\Addressing\Juab\JuabAddressPointUpdates.gdb\JuabUpdates_10122016'
    agrcAddPts_juabCo = r'C:\ZBECK\Addressing\Juab\Juab.gdb\AddressPoints_Juab'

    juabCoAddFLDS = ['FullAdd', 'AddNum', 'AddNumSuff', 'PrefixDir', 'StreetName', 'StreetType', 'LandmarkNa', 'Building', \
                     'UnitType', 'UnitID', 'PtLocation', 'PtType', 'Structure', 'ParcelID', 'AddSource', 'SHAPE@']

    checkRequiredFields(juabCoAddPts, juabCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_juabCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(juabCoAddPts, juabCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[0] not in errorList:
                address = parse_address.parse(row[0])
                addNum = address.houseNumber.replace('*', '')
                addNumSuf = formatValues(row[2], addNumSufList)
                preDir = address.prefixDirection
                sName = address.streetName
                sufDir = removeBadValues(address.suffixDirection, errorList)

                if address.suffixType != None:
                    sType = address.suffixType
                else:
                    sType = row[5]

                landmark = removeBadValues(row[6], errorList)
                building = removeBadValues(row[7], errorList)
                unitType = removeBadValues(row[8], errorList)
                unitId_hash = formatUnitID(row[9])
                unitId = unitId_hash.strip('# ')
                ptLocation = row[10]
                ptType = row[11]
                structure = row[12]
                parcel = row[13]
                source = 'JUAB COUNTY'
                loadDate = today
                modDate = None

                fulladd = '{} {} {} {} {} {} {}'.format(addNum, addNumSuf, preDir, sName, sufDir, sType, unitId_hash)
                fulladd = ' '.join(fulladd.split())

                shp = row[15]

                iCursor.insertRow(('', '', fulladd, addNum, addNumSuf, preDir, sName, sType, sufDir, landmark, building, \
                                   unitType, unitId, '', '', '49023', 'UT', ptLocation, ptType, structure, parcel, \
                                   source, loadDate, 'COMPLETE', '', modDate, '', shp))

    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_juabCo, inputDict)


def kaneCounty():
    #addressAppPts = r'C:\ZBECK\Addressing\Kane\Kane.gdb\ADDRESSADMIN_AddressPointsBKUP'
    addressAppPts = r'Database Connections\DC_AddressAdmin@AddressPointEditing@itdb104sp.sde\AddressPointEditing.ADDRESSADMIN.AddressPoints'
    countyBoundaries = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde\SGID10.BOUNDARIES.Counties'

    sql = """"{}" = '{}'""".format('NAME', 'KANE')
    kaneBoundaryFL = arcpy.MakeFeatureLayer_management(countyBoundaries, 'kaneBoundaryFL', sql)
    addressAppPtsFL = arcpy.MakeFeatureLayer_management(addressAppPts, 'addressAppPtsFL')

    kaneCoAddPts = arcpy.SelectLayerByLocation_management(addressAppPtsFL, 'WITHIN', kaneBoundaryFL, '', 'NEW_SELECTION')

    #kaneCoAddPts = r'C:\ZBECK\Addressing\Kane\Kane.gdb\AddressAppCountyUpdates_Kane'  #Change to AddressAdmin pts
    agrcAddPts_kaneCo = r'C:\ZBECK\Addressing\Kane\Kane.gdb\AddressPoints_Kane'

    kaneCoAddFLDS = agrcAddFLDS

    iCursor = arcpy.da.InsertCursor(agrcAddPts_kaneCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(kaneCoAddPts, kaneCoAddFLDS) as sCursor_kane:
        for row in sCursor_kane:

            addNum = row[3]
            streetName = row[6]

            if row[2] not in errorList:
                fullAdd = row[2]
                addNum = row[3]
                preDir = removeBadValues(row[5], errorList)
                streetName = removeBadValues(row[6], errorList)
                streetType = removeBadValues(row[7], errorList)
                sufDir = removeBadValues(row[8], errorList)
                landmark = removeBadValues(row[9], errorList)
                building = removeBadValues(row[10], errorList)
                unitType = removeBadValues(row[11], errorList)
                unitId = removeBadValues(row[12], errorList)
                ptLocation = removeBadValues(row[17], errorList)
                ptType = removeBadValues(row[18], errorList)
                structure = removeBadValues(row[19], errorList)
                parcel = removeBadValues(row[20], errorList)

            if addNum and streetName not in errorList:
                addNum = row[3]
                preDir = removeBadValues(row[5], errorList)
                streetName = removeBadValues(row[6], errorList)
                streetType = removeBadValues(row[7], errorList)
                sufDir = removeBadValues(row[8], errorList)
                landmark = removeBadValues(row[9], errorList)
                building = removeBadValues(row[10], errorList)
                unitType = removeBadValues(row[11], errorList)
                unitId = removeBadValues(row[12], errorList)
                ptLocation = removeBadValues(row[17], errorList)
                ptType = removeBadValues(row[18], errorList)
                structure = removeBadValues(row[19], errorList)
                parcel = removeBadValues(row[20], errorList)

                dirtyAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, streetName, sufDir, streetType, unitType, unitId)
                fullAdd = ' '.join(dirtyAdd.split())

            else:
                continue

            addNumSuf = ''
            addSys = ''
            utAddId = ''
            city = ''
            zip = ''
            fips = '49025'
            state = 'UT'
            addSource = 'KANE COUNTY'
            status = 'COMPLETE'
            loadDate = today
            editor = removeBadValues(row[24], errorList)
            shp = row[26]


            iCursor.insertRow((addSys, utAddId, fullAdd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                status, editor, None, shp))

    del iCursor

    addPolyAttributes(sgid10, agrcAddPts_kaneCo)


def millardCounty():
    millardCoAddPts = r'C:\ZBECK\Addressing\Millard\Addresses_Rooftops.shp'
    agrcAddPts_millardCo = r'C:\ZBECK\Addressing\Millard\Millard.gdb\AddressPoints_Millard'

    millardCoAddFLDS = ['OBJECTID', 'PREFIX', 'ROAD_NAME', 'ROAD_TYPE', 'HOUSE_NO', 'SHAPE@']

    longDirs = ['NORTH', 'SOUTH', 'EAST', 'WEST']
    millardTypes = ['AVE', 'RD', 'LN', 'ST']

    checkRequiredFields(millardCoAddPts, millardCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_millardCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(millardCoAddPts, millardCoAddFLDS) as sCursor_millardCo:
        for row in sCursor_millardCo:
            if row[4] not in errorList:

                if row[4].isdigit():
                    addNum = row[4]

                preDir = formatValues(row[1], dirs)

                if ' ' in row[2]:
                    if row[2].split()[-1] in millardTypes:
                        print row[2]
                        sName = row[2].split()[:-1]
                        sName = ' '.join(sName)
                        sType = checkWord(row[3], parse_address.sTypes)
                        sufDir = ''
                    elif row[2].split()[-1] in longDirs:
                        sName = row[2].split()[:-1]
                        sName = ' '.join(sName)
                        sufDir = row[2].split()[-1][0]
                        sType = ''
                    elif row[2].endswith('HIGHWAY'):
                        sName = row[2].split(' HIGHWAY')[0]
                        sType = 'HWY'
                        sufDir = ''
                    elif row[2].endswith(')'):
                        if row[2][0].isdigit():
                            sName = row[2].split('(')[1][:-1]
                            sType = checkWord(row[3], parse_address.sTypes)
                            sufDir = ''
                        else:
                            sName = row[2].split('(')[0]
                            sType = checkWord(row[3], parse_address.sTypes)
                            sufDir = ''

                            if sName.endswith('DR '):
                                sName = sName.replace(' DR', '')
                                sType = 'DR'
                    else:
                        sName = row[2]
                        sType = checkWord(row[3], parse_address.sTypes)
                        sufDir = ''

                elif ' ' not in row[2]:
                    if row[2][0].isdigit() and row[2][-1].isdigit() == False:
                        sName = row[2][:-1]
                        sufDir = row[2][-1:]
                        sType = ''
                    else:
                        sName = row[2]
                        sType = checkWord(row[3], parse_address.sTypes)
                        sufDir = ''

                if row[3] in sTypeDir and sName.isdigit == False:
                    sType = checkWord(row[3], parse_address.sTypes)
                if row[3].startswith('#'):
                    unitId = row[3][1:]
                    unitId_hash = '{} {}'.format('#', unitId)
                    sType = 'ST'

                else:
                    unitId = ''
                    unitId_hash = ''


                fulladd = '{} {} {} {} {} {}'.format(addNum, preDir, sName, sufDir, sType, unitId_hash)
                fulladd = ' '.join(fulladd.split())

                shp = row[5]

                iCursor.insertRow(('', '', fulladd, addNum, '', preDir, sName, sType, sufDir, '', '', '',\
                                   unitId, '', '', '49027', 'UT', '', '', '', '', 'MILLARD COUNTY', today, \
                                   'COMPLETE', '', None, shp))

    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']
    }

    addPolyAttributes(sgid10, agrcAddPts_millardCo, inputDict)


def saltLakeCounty():

    slcoAddPts = r'C:\ZBECK\Addressing\SaltLake\SLCounty\SaltLakeCounty.gdb\ADDRESS_POINTS'
    agrcAddPts_SLCO = r'C:\ZBECK\Addressing\SaltLake\SaltLake.gdb\AddressPoints_SaltLake'

    slcoAddFLDS = ['PARCEL', 'ADDRESS', 'UNIT_DESIG', 'IDENTIFY', 'BLDG_DESIG', 'ADDR_LABEL', 'DEVELOPMENT', 'BUSINESS_NAME', \
                   'ADDR_TYPE', 'UPDATED', 'MODIFIED_DATE', 'PRE_DIR', 'SHAPE@', 'ZIP_CODE']

    fixDict = {'SOUTHTEMPLE':'SOUTH TEMPLE', 'NORTHTEMPLE':'NORTH TEMPLE','WESTTEMPLE':'WEST TEMPLE', 'EASTCAPITOL':'EAST CAPITOL',\
               'SOUTHJORDAN':'SOUTH JORDAN', 'SOUTHJRDN':'SOUTH JORDAN', 'SOUTHPOINTE':'SOUTH POINTE', 'SOUTHSAMUEL':'SOUTH SAMUEL', \
               'NORTHBOROUGH':'NORTH BOROUGH'}

    aveDict = {'FIRST':'1ST', 'SECOND':'2ND', 'THIRD':'3RD', 'FOURTH':'4TH', 'FIFTH':'5TH', 'SIXTH':'6TH', \
               'SEVENTH':'7TH', 'EIGHTH':'8TH', 'NINTH':'9TH', 'TENTH':'10TH', 'ELEVENTH':'11TH', 'TWELFTH':'12TH', 'THIRTEENTH':'13TH', \
               'FOURTEENTH':'14TH', 'FIFTEENTH':'15TH', 'SIXTEENTH':'16TH', 'SEVENTEENTH':'17TH', 'EIGHTEENTH':'18TH'}

    other = ['AIRPORT', 'CEMETERY', 'CHURCH', 'CIVIC', 'COORDINATE', 'FIRE STATION', 'GOLF COURSE', 'HOSPITAL', 'JAIL', 'LIBRARY', 'MAILBOX', 'PARK', \
             'OPEN SPACE', 'PARKING', 'POLICE', 'POOL', 'POST OFFICE', 'PRISON', 'SCHOOL', 'SLCC', 'TEMPLE', 'TRAX', 'U CAMPUS', 'WESTMINSTER', 'ZOO']
    residential = ['RES', 'APT', 'CONDO', 'CONDO APT', 'HOA', 'MOBILEHOME', 'MULTI', 'PUD', 'TOWNHOME']
    commercial = ['BUS CONDO', 'BUS PUD', 'BUSINESS', 'MORTUARY']
    industrial = ['UTILITY']

    checkRequiredFields(slcoAddPts, slcoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_SLCO, agrcAddFLDS)

    with arcpy.da.SearchCursor(slcoAddPts, slcoAddFLDS) as sCursor_slco:
        for row in sCursor_slco:
            if row[1] not in errorList:
                address = parse_address.parse(row[1])

                addSys = ''
                utAddId = ''

                addNum = address.houseNumber
                if '-' in addNum:
                    addNum = addNum.split('-')[0]

                    addNumSuf = row[5].split()[1]
                else:
                    addNumSuf = ''

                preDir = address.prefixDirection
                streetType = address.suffixType
                sufDir = address.suffixDirection
                landmark = row[6]
                building = row[7]

                unitType = row[8]

                if unitType in other:
                    ptType = 'Other'
                elif unitType in residential:
                    ptType = 'Residential'
                elif unitType in commercial:
                    ptType = 'Commercial'
                elif unitType in industrial:
                    ptType = 'Industrial'
                else:
                    ptType = ''

                zip = row[13]

                streetName = address.streetName

                if streetName in fixDict:
                    fulladd = row[1].replace(streetName, fixDict[streetName])
                    fulladd = ' '.join(fulladd.split()).strip()
                    streetName = fixDict[streetName]
                if streetName in aveDict and zip == 84103:
                    fulladd = row[1].replace(streetName, aveDict[streetName])
                    fulladd = ' '.join(fulladd.split()).strip()
                    streetName = aveDict[streetName]
                    print streetName
                else:
                    fulladd = row[1].strip()
                    fulladd = ' '.join(fulladd.split())

                if row[2] not in errorList:
                    unitId = row[2]
                    fulladd = fulladd + ' # ' + unitId
                    fulladd = ' '.join(fulladd.split())
                else:
                    unitId = ''

                city = ''
                fips = '49035'
                state = 'UT'
                ptLocation = 'Unknown'
                #ptType = ''
                structure = 'Unknown'
                parcel = row[0]
                addSource = 'SALT LAKE COUNTY'
                loadDate = today
                status = 'COMPLETE'
                editor = row[9]
                modified = row[10]
                shp = row[12]

                iCursor.insertRow((addSys, utAddId, fulladd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                                   unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                                   status, editor, modified, '', '', '', shp))

    del iCursor
    del sCursor_slco

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_SLCO, inputDict)


def summitCounty():
    summitCoAddPts = r'C:\ZBECK\Addressing\Summit\AddressPoints_16_09.shp'
    agrcAddPts_summitCo = r'C:\ZBECK\Addressing\Summit\Summit.gdb\AddressPoints_Summit'

    summitCoAddFLDS = ['ADDRNUM', 'ADDRNUMSUF', 'APARTMENT', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE', 'ROADPOSTDI',\
                       'FULLADDR', 'PLACENAME', 'POINTTYPE', 'LASTUPDATE', 'USNGCOORD', 'SHAPE@']

    checkRequiredFields(summitCoAddPts, summitCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_summitCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(summitCoAddPts, summitCoAddFLDS) as sCursor_summit:
        for row in sCursor_summit:

            if row[0] in errorList or row[4] in errorList:
                continue

            addNum = row[0].strip()
            addNumSuf = removeBadValues(row[1], errorList)
            preDir = checkWord(row[3], dirs)
            sName = removeBadValues(row[4], errorList).upper()
            sType = removeBadValues(row[5], sTypeDir).upper()
            sufDir = checkWord(row[6], dirs)

            unitNum = formatUnitID(row[2])

            fullAdd = '{} {} {} {} {} {}'.format(addNum, preDir, sName, sType, sufDir, unitNum)
            fullAdd = ' '.join(fullAdd.split())

            if row[9] == 'Condo or Unit':
                ptType = 'Residential'
            elif row[9] == 'Office or Suite':
                ptType = 'Commercial'
            else:
                ptType = 'Other'

            building = removeBadValues(row[8], errorList)
            modified = row[10]
            parcelID = row[11]
            loadDate = today
            shp = row[12]

            iCursor.insertRow(('', '', fullAdd, addNum, addNumSuf, preDir, sName, sType, sufDir, '', building, \
                              '', unitNum.strip('# '), '', '', '49043', 'UT', '', ptType, '', parcelID, 'Summit County', loadDate, \
                              'COMPLETE', '', modified, shp))


    del iCursor

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']
    }

    addPolyAttributes(sgid10, agrcAddPts_summitCo, inputDict)


def tooeleCounty():

    def formatRoute(word, d):
        for key, value in d.iteritems():
            if word in value:
                return key
        # if nothing is found
        return word

    tooeleCoAddPts = r'C:\ZBECK\Addressing\Tooele\Tooele.gdb\TC_AddressPts'
    agrcAddPts_tooeleCo = r'C:\ZBECK\Addressing\Tooele\Tooele.gdb\AddressPoints_Tooele'

    tooeleCoAddFLDS = ['HouseAddr', 'FullAddr', 'HouseNum', 'PreDir', 'StreetName', 'StreetType', 'SufDir', \
                       'SHAPE@', 'OBJECTID']

    checkRequiredFields(tooeleCoAddPts, tooeleCoAddFLDS)

    routeDict = {'HWY 36':['STATE HWY 36', 'STATE RTE 36', 'SR 36', 'SR36'], 'HWY 138':['SR-138 HWY', 'STATE HWY 138', 'SR-138'], \
                'LINCOLN HWY':['LINCOLN HWY RTE 1913', 'LINCOLN HWY RTE 1919'], 'HWY 112':['SR 112', 'STATHWY 112'], 'HWY 199':['SR199'], \
                'HWY 73':['SR73']}

    iCursor = arcpy.da.InsertCursor(agrcAddPts_tooeleCo, agrcAddFLDS)

    cnt = 0
    with arcpy.da.SearchCursor(tooeleCoAddPts, tooeleCoAddFLDS) as sCursor:
        for row in sCursor:
            if row[4] not in errorList and row[2][:1].isdigit:
                preDir = formatValues(row[3], dirs)
                if row[4][:1].isdigit() and ' ' in row[4]:
                    sName = formatAddressNumber(row[4].split()[0])
                    sufDir = checkWord(row[4].split()[1], dirs)
                else:
                    sName = formatRoute(row[4], routeDict)

                sType = formatValues(row[5], sTypeDir)
                print sType
            # if row[0] not in errorList:
            #     pAddress = parse_address.parse(row[0])
            #     addNum = pAddress.houseNumber
            #     preDir = pAddress.prefixDirection
            #     sName = pAddress.streetName
            #     sName2 = row[4]
            #     if row[4] not in errorList:
            #         if row[4][:1].isdigit() == False:
            #             sName2 = row[4].strip()
            #             if sName != sName2:
            #                 cnt = cnt + 1
            #                 print '{} - {}, {}'.format(row[8], sName, sName2)


def utahCounty():

    utahCoAddPts = r'C:\ZBECK\Addressing\Utah\Address.gdb\Address\AddressPoint'
    #utahCoAddPts = r'C:\ZBECK\Addressing\Utah\Address.gdb\AddressPoints2'
    agrcAddPts_utahCo = r'C:\ZBECK\Addressing\Utah\Utah.gdb\AddressPoints_Utah'

    utahCoAddFLDS = ['ADDRNUM', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE', 'ROADPOSTDIR', 'ADDRTYPE', \
                     'UNITTYPE', 'UNITID', 'LASTUPDATE', 'SHAPE@', 'LASTEDITOR', 'FULLADDR', 'OBJECTID']

    checkRequiredFields(utahCoAddPts, utahCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_utahCo, agrcAddFLDS)

    #badVals = [None, '', ' ', '0']
    badType = {'AV':'AVE', 'LA':'LN', 'PKY':'PKWY', 'WY':'WAY'}
    addType = {'Building':'Rooftop', 'Parcel':'Parcel Centroid', 'Building Entrance':'Primary Structure Entrance', \
              'Driveway Turn-off':'Driveway Entrance', 'Unit, Condo or Suite':'Residential', 'Other':'Other', 'Unknown':'Unknown'}
    dirList = ['NORTH', 'SOUTH', 'EAST', 'WEST']

    with arcpy.da.SearchCursor(utahCoAddPts, utahCoAddFLDS) as sCursor_utah:
        for row in sCursor_utah:

            unitId = ''
            sType = ''
            sufDir = ''

            if row[0] not in errorList:
                if row[1] not in errorList:
                    addNum = row[0]

                if row[2] not in errorList:

                    if ' ' in row[2]:
                        street = ' '.join(row[2].split()).upper()

                        if row[3] not in errorList:
                            if row[3] in badType:
                                sType = badType[row[3]]
                            else:
                                sType = row[3]

                        if street.split()[0].isdigit() and street.split()[0] != '0':
                            street = street.split()[0]

                            if row[2].split()[-1] in dirList:
                                sufDir = row[2].split()[-1][:1]

                                if street.isdigit() == True:
                                    sType = ''

                            else:
                                if row[2].split()[-1][:1] in dirs:
                                    sufDir = row[2].split()[-1][:1]
                                else:
                                    sufDir = ''

                        elif street.split()[0].isdigit() == False:
                                street = street
                                sufDir = ''

                        # else:
                        #     continue

                        if '#' in street:
                            street = street.split()[0]
                            if street == 'STATE':
                                sType = 'ST'
                            unitId = '# ' + row[2].split('#')[-1]
                            unitId = ' '.join(unitId.split())

                    else:
                        street = row[2]
                        sufDir = ''
                        if row[3] not in errorList:
                            if row[3] in badType:
                                sType = badType[row[3]]
                            else:
                                sType = row[3]

                    if row[1] in dirs:
                        preDir = row[1]
                    else:
                        preDir = ''

                    if row[4] not in errorList:
                        sufDir = row[4]
                        if ' {} '.format(sufDir) not in row[11]:
                            sufDir = ''

                    if row[5] not in errorList:
                        ptLocation = addType[row[5]]
                    else:
                        ptLocation = ''

                    if row[6] not in errorList:
                        if row[6].upper() in unitTypeDir:
                            unitType = unitTypeDir[row[6].upper()]
                            unitType_Abbrv = row[6].upper()
                        else:
                            unitType = row[6].upper()
                            unitType_Abbrv = ''
                    else:
                        unitType = ''
                        unitType_Abbrv = ''

                    if row[7] not in errorList:
                        unitId = row[7]

                    loadDate = today
                    status = 'COMPLETE'

                    if row[10] not in errorList:
                        editor = row[10]
                    else:
                        editor = ''

                    modDate = row[8]

                    dirtyAdd = '{} {} {} {} {} {} {}'.format(addNum, preDir, street, sufDir, sType, unitType_Abbrv, unitId)
                    fullAdd = ' '.join(dirtyAdd.split())

                    shp = row[9]

                    iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, street, sType, sufDir, '', '', unitType, unitId, '', '', '49049', \
                                       'UT', ptLocation, '', '', '', 'UTAH COUNTY', loadDate, status, editor, modDate, '', '', '', shp))


    del iCursor
    del sCursor_utah

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5'],
    'USNG':['SGID10.INDICES.NationalGrid', 'USNG']
    }

    addPolyAttributes(sgid10, agrcAddPts_utahCo, inputDict)


def wasatchCounty():

    wasatchCoAddPts = r'C:\ZBECK\Addressing\Wasatch\WC_AddressPoints_Aug2016.shp'
    agrcAddPts_wasatchCo = r'C:\ZBECK\Addressing\Wasatch\Wasatch.gdb\AddressPoints_Wasatch'

    wasatchCoAddFLDS = ['SiteAddID', 'FullAdd', 'AddrNum', 'AddrNumSuf', 'StreetName', 'StreetType', 'SuffixDir', 'Structure', \
                        'CreateDate', 'PlaceName', 'SHAPE@']

    checkRequiredFields(wasatchCoAddPts, wasatchCoAddFLDS)

    iCursor = arcpy.da.InsertCursor(agrcAddPts_wasatchCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(wasatchCoAddPts, wasatchCoAddFLDS) as sCursor_wasatchCo:
        for row in sCursor_wasatchCo:

            addNum = removeBadValues(row[2], errorList)

            if addNum in errorList:
                continue
            parcel = removeBadValues(row[0], errorList)
            fullAdd = removeBadValues(row[1], errorList)
            preDir = removeBadValues(row[3], errorList)
            sName = removeBadValues(row[4], errorList)
            sType = removeBadValues(row[5], errorList)
            sufDir = removeBadValues(row[6], errorList)
            structure = removeBadValues(row[7], errorList).title()
            if row[8] != None:
                modDate = row[8]
            else:
                modDate = None
            landmark = removeBadValues(row[9], errorList).upper()
            loadDate = today
            shp = row[10]


            iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, sName, sType, sufDir, landmark, '', '', '', '', '', '49051', 'UT', '', \
                               '', structure, parcel, 'Wasatch County', loadDate, 'COMPLETE', '', modDate, shp))

    del iCursor
    del sCursor_wasatchCo

    inputDict = {
    'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']
    }

    addPolyAttributes(sgid10, agrcAddPts_wasatchCo, inputDict)


def washingtonCounty():

    washcoAddPts = r'C:\ZBECK\Addressing\Washington\Washington.gdb\Incoming\WASHCO_AddressPoints'
    agrcAddPts_washCo = r'C:\ZBECK\Addressing\Washington\Washington.gdb\AddressPoints_Washington'

    washcoAddFLDS = ['TAX_ID', 'ADDRESS', 'NUMB', 'PRE_DIR', 'GEO_NAME', 'S_TYPE', 'SUFFIX', 'SHAPE@']

    checkRequiredFields(washcoAddPts, washcoAddFLDS)

    dirList = ['N', 'S', 'E', 'W']
    sTypeList = ['ALY', 'ANX', 'AVE', 'BLVD', 'BYP', 'CSWY', 'CIR', 'CT', 'CTR', 'CV', 'XING', 'DR', 'EST', 'ESTS', 'EXPY', 'FWY', 'HWY', 'JCT', 'LNDG', 'LN', \
                 'LOOP', 'PARK', 'PKWY', 'PL', 'RAMP', 'RD', 'RTE', 'ROW', 'SQ', 'ST', 'TER', 'TRWY', 'TRL', 'TUNL', 'TPKE', 'WAY']


    iCursor = arcpy.da.InsertCursor(agrcAddPts_washCo, agrcAddFLDS)

    with arcpy.da.SearchCursor(washcoAddPts, washcoAddFLDS) as sCursor_washco:
        for row in sCursor_washco:

            if row[1] not in errorList and len(row[1]) > 6:

                if row[1].split()[0].isdigit():
                    fullAdd = ' '.join(row[1].split())
                    addNum = row[1].split()[0]
                else:
                    continue

                if row[3] in dirList:
                    preDir = row[3]
                else:
                    preDir = ''

                if row[4] not in errorList:
                    if row[4].endswith((' N', ' S', ' E', ' W')):
                        stName = row[4][:-1].strip()
                        sufDir = row[4][-1:]
                    else:
                        sufDir = ''
                        stName = row[4]
                else:
                    stName = ''

                sType = formatValues(row[5], sTypeList)

                unitId = removeBadValues(row[6], errorList)

                parcel = removeBadValues(row[0], errorList)

                date = today
                modDate = None

                shp = row[7]

            else:
                continue


            iCursor.insertRow(('', '', fullAdd, addNum, '', preDir, stName, sType, sufDir, '', '', '', unitId, '', '', '49053', 'UT', 'Unknown', \
                               'Unknown', 'Unknown', parcel, 'WASHINGTON COUNTY', date, 'COMPLETE', '', modDate, shp))

    del iCursor
    del sCursor_washco

    addPolyAttributes(sgid10, agrcAddPts_washCo)


def weberCounty():

   weberCoAddPts = r'C:\ZBECK\Addressing\Weber\AddressPoints.gdb'
   #agrcAddPts_weberCo = r'C:\ZBECK\Addressing\Weber\Weber.gdb\AddressPoints_Weber'
   agrcAddPts_weberCo = r'K:\dbuell\AddressPts_Schema_WeberCo.gdb/EditorApp_AddressPointSchema'

   weberCoAddFLDS = ['ADDR_HN', 'ADDR_PD', 'ADDR_SN', 'ADDR_ST', 'ADDR_SD', 'PT_ADD', 'PLCMT_METH', 'WEBER_DATE', 'ADDRESS_TY', \
                     'ZIP', 'PARCEL_ID', 'EDIT_DATE', 'SHAPE@']

   checkRequiredFields(weberCoAddPts, weberCoAddFLDS)

   iCursor = arcpy.da.InsertCursor(agrcAddPts_weberCo, agrcAddFLDS)

   with arcpy.da.SearchCursor(weberCoAddPts, weberCoAddFLDS) as sCursor_weber:
       for row in sCursor_weber:
           #address = parse_address.parse(row[1])

           addSys = ''
           utAddId = ''
           fulladd = row[5]
           addNum = row[0]
           addNumSuf = ''
           preDir = row[1]
           streetName = row[2]
           streetType = row[3]
           sufDir = row[4]
           landmark = ''
           building = ''
           ptType = ''

           if row[8] not in errorList:
               unitId = row[8].upper()

           city = ''
           zip = ''
           fips = '49035'
           state = 'UT'
           ptLocation = ''
           #ptType = ''
           structure = ''
           parcel = row[0]
           addSource = 'WEBER COUNTY'
           loadDate = today
           status = 'COMPLETE'
           editor = row[9]
           modified = row[10]
           shp = row[12]

           iCursor.insertRow((addSys, utAddId, fulladd, addNum, addNumSuf, preDir, streetName, streetType, sufDir, landmark, building, \
                              unitType, unitId, city, zip, fips, state, ptLocation, ptType, structure, parcel, addSource, loadDate, \
                              status, editor, modified, shp))

   del iCursor

   polyAttributesDict = {
   'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
   'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
   'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']
   }

   addPolyAttributes(sgid10, agrcAddPts_weberCo, polyAttributesDict)


def checkRequiredFields(inCounty, requiredFlds):

    countyFlds = arcpy.ListFields(inCounty)
    countyFldList = []

    for countyFld in countyFlds:
        countyFldList.append(countyFld.name)
    for fld in requiredFlds:
        if fld not in countyFldList and fld != 'SHAPE@':
            sys.exit(fld + ' Is a requided field MISSING from ' + inCounty)


def addPolyAttributes(sgid10, agrcAddPts, polyDict):

    # inputDict = {
    # 'AddSystem':['SGID10.LOCATION.AddressSystemQuadrants', 'GRID_NAME'],
    # 'City':['SGID10.BOUNDARIES.Municipalities', 'SHORTDESC'],
    # 'ZipCode':['SGID10.BOUNDARIES.ZipCodes', 'ZIP5']
    # }

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



#beaverCounty()   #Complete
boxElderCounty()  #Complete
#cacheCounty()  #Complete
#carbonCounty() #In Progress
#davisCounty()  #Complete
#juabCounty()
#kaneCounty()   #Complete
#millardCounty()   #Complete
#saltLakeCounty() #Complete
#summitCounty()
#tooeleCounty()
#utahCounty() #Complete
#wasatchCounty()
#washingtonCounty()  #Complete
#weberCounty()
#addPolyAttributes(sgid10, agrcAddPts_SLCO)






