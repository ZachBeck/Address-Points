import arcpy
from pathlib import Path
from UpdatePointAttributes import addPolyAttributes
from UpdatePointAttributes import update_alias_AddPtID

def removeNone(word):
    if word == None:
        word = ''
    return word

def return_key(word, d):
    if word == None:
        word = ''
    # word = word.upper()
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

def truncateOldCountyPts(inPts):
    pointCount = int(arcpy.GetCount_management(inPts).getOutput(0))
    if pointCount > 0:
        arcpy.TruncateTable_management(inPts)
        print (f'Deleted {pointCount} points in {inPts}')
    else:
        print ('No points to delete')

sgid = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_agrc.sde'))

alias_flds = ['AddSystem', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir',
              'ZipCode', 'UnitType', 'UnitID', 'City', 'CountyID', 'UTAddPtID', 'SHAPE@']

stype_dir = {'ALY':'ALLEY', 'AVE':'AVENUE', 'BAY':'BAY', 'BND':'BEND', 'BLVD':'BOULEVARD', 'CYN':'CANYON',
            'CTR':'CENTER', 'CIR':['CR', 'CIRCLE'], 'COR':'CORNER', 'CT':'COURT', 'CV':'COVE', 'CRK':'CREEK',
            'CRES':'CRESCENT', 'XING':'CROSSING', 'DR':'DRIVE', 'EST':'ESTATE', 'ESTS':'ESTATES',
            'EXPY':'EXPRESSWAY', 'FLT':'FLAT', 'FRK':'FORK', 'FWY':'FREEWAY', 'GLN':'GLEN', 'GRV':'GROVE',
            'HTS':'HEIGHTS','HWY':'HIGHWAY', 'HL':'HILL', 'HOLW':'HOLLOW', 'JCT':'JUNCTION', 'LN':'LANE',
            'LNDG':'LANDING', 'LOOP':'LOOP', 'MNR':'MANOR','MDW':'MEADOW', 'MDWS':'MEADOWS', 'PARK':'PARK', 'PKWY':'PARKWAY',
            'PASS':'PASS', 'PL':'PLACE', 'PLZ':'PLAZA', 'PT':['POINT', 'POINTE'], 'RAMP':'RAMP', 'RNCH':'RANCH', 'RDG':'RIDGE',
            'RD':'ROAD', 'RST':'REST', 'RTE':'ROUTE', 'ROW':'ROW', 'RUN':'RUN', 'SQ':'SQUARE', 'ST':'STREET',
            'TER':'TERRACE', 'TRCE':'TRACE', 'TRL':'TRAIL', 'VW':'VIEW', 'VLG':'VILLAGE', 'WAY':['WY','WAY']}



def davisCounty_alias():
    davisCoAddPts = r'..\Davis\DavisCounty.gdb\DavisAddress'
    agrcAddPts_AliasDavisCo = r'..\Davis\Davis.gdb\AliasAddressPoints_Davis'
    out_county_fgdb = r'..\Davis\Davis.gdb'

    # davisCoAddFLDS = ['AddressNum', 'AddressN_1', 'UnitType', 'UnitNumber', 'RoadPrefix', 'RoadName', 'RoadNameTy', 'RoadPostDi',
    #                   'FullAddres', 'SHAPE@', 'PrimaryAdd', 'MunicipalN']
    davisCoAddFLDS = ['AddressNumber', 'AddressNumberSuffix', 'UnitType', 'UnitNumber', 'RoadPrefixDirection', 'RoadName', 'RoadNameType',
                      'RoadPostDirection', 'FullAddress', 'SHAPE@', 'PrimaryAddress', 'MunicipalName']
    
    # alias_flds = ['AddSystem', 'AddNum', 'AddNumSuffix', 'PrefixDir', 'StreetName', 'StreetType', 'SuffixDir',
    #               'ZipCode', 'UnitType', 'UnitID', 'City', 'CountyID', 'UTAddPtID', 'SHAPE@']
        

    checkRequiredFields(davisCoAddPts, davisCoAddFLDS)
    #archive_last_month(agrcAddPts_AliasDavisCo)
    truncateOldCountyPts(agrcAddPts_AliasDavisCo)

    noTypeList = ['ANTELOPE ISLAND CAUSEWAY', 'APPLE ACRES', 'ASPEN GROVE', 'BOUNTIFUL MEMORIAL PARK', 'BROADWAY',
                  'BUFFALO RANCH DEVELOPMENT', 'BURN PLANT', 'CARRIAGE CROSSING', 'CENTERVILLE MEMORIAL PARK',
                  'CHERRY HILL ENTRANCE', 'CHEVRON REFINERY', 'CHRISTY', 'COMPTONS POINTE', 'DEER CREEK', 'EAST ENTRANCE',
                  'EAST PROMONTORY', 'EGG ISLAND OVERLOOK', 'FAIRVIEW PASEO', 'FARMINGTON CEMETERY', 'FARMINGTON CROSSING',
                  'FREEPORT CENTER', 'GARDEN CROSSING PASEO', 'HAWORTH', 'HWY 106', 'HWY 126', 'HWY 193', 'HWY 68', 'HWY 89',
                  'HWY 93', 'HOLLY HAVEN I', 'HOLLY HAVEN II', 'IBIS CROSSING', 'KAYSVILLE AND LAYTON CEMETERY',
                  'LLOYDS PARK', 'MOUNTAIN VIEW PASEO', 'NORTH ENTRANCE', 'NORTHEAST ENTRANCE', 'NORTHWEST ENTRANCE',
                  'POETS REST', 'PRESERVE PASEO', 'SOMERSBY', 'SOUTH CAUSEWAY', 'SOUTH ENTRANCE', 'SOUTHEAST ENTRANCE',
                  'STATION', 'STONEY BROOK', 'SYRACUSE CEMETERY', 'VALIANT', 'VALLEY VIEW', 'WARD', 'WARWICK', 'WEST PROMONTORY',
                  'WETLAND POINT', 'WHISPERING PINE', 'WILLOW BEND PASEO', 'WILLOW FARM PASEO', 'WILLOW GARDEN PASEO',
                  'WILLOW GREEN PASEO', 'WILLOW GROVE PASEO', 'WYNDOM']

    remove_stypes = ['STONEY BROOK CIR', 'ANGEL ST', 'BROWNING LN', 'CHARLENE WAY', 'COUNTRY WAY', 'EAGLES LNDG', 'GRANTS LN',
                     'SAGE DR']

    hwy_dict = {'SR 37':'HWY 37', 'SR 193':'HWY 193'}


    with arcpy.da.SearchCursor(davisCoAddPts, davisCoAddFLDS) as sCursor_davis, \
        arcpy.da.InsertCursor(agrcAddPts_AliasDavisCo, alias_flds) as iCursor:

        for row in sCursor_davis:
            if row[10] == 'A':
                if row[0] == 0 and row[5] != 'Freeport Center':
                    continue
                if row[11] in ['Ogden', 'Roy', 'Uintah', 'Washington Terrace']:
                    continue   

                elif row[0] not in errorList and row[5] not in errorList:

                    addNum = row[0]
                    addNumSuf = formatValues(row[1], addNumSufList)

                    unitId = removeBadValues(row[3], errorList).upper()
                    preDir = formatValues(row[4], dirs)

                    unitType = formatValues(row[2], unitTypeDir).upper()
                    if unitType != '' and unitId == '':
                        unitType = ''

                    streetName = removeBadValues(row[5], errorList).upper()

                    streetType = returnKey(removeNone(row[6]).upper(), sTypeDir)

                    if streetName.startswith('BEVERLY'):
                        streetName = 'BEVERLY'
                        streetType = 'WAY'
                    if streetName in remove_stypes:
                        long_sname = clean_street_name(streetName)
                        streetName = long_sname.name
                        streetType = long_sname.type
                        print(streetName)

                    if 'HIGHWAY' in streetName:
                        streetName = streetName.replace('HIGHWAY', 'HWY')

                    sufDir = formatValues(row[7], dirs)

                    if streetName in hwy_dict:
                        streetName = hwy_dict[streetName]
                        streetType = ''
                        sufDir = ''

                    if streetName == 'FREEPORT CENTER':
                        addNum = ''

                    addSys = ''
                    utAddId = ''
                    city = ''
                    zip = ''
                    fips = '49011'
                    shp = row[9]

                    iCursor.insertRow((addSys, addNum, addNumSuf, preDir, streetName, streetType, sufDir, 
                                       zip, unitType, unitId, city, fips, utAddId, shp))
                    
    inputDict = {
        'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
        'City':['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],
        'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', '']
        }

    # alias_pts = {
    #     'UTAddPtID':['AddressPoints_Davis', 'UTAddPtID', '']
    #     }

    addPolyAttributes(sgid, agrcAddPts_AliasDavisCo, inputDict)
    # addPolyAttributes(out_county_fgdb, agrcAddPts_AliasDavisCo, alias_pts)
    update_alias_AddPtID(agrcAddPts_AliasDavisCo)
    deleteDuplicatePts(agrcAddPts_AliasDavisCo, ['UTAddPtID', 'SHAPE@WKT', 'OBJECTID'])


def UtahCounty_alias():
    utah_cnty_alias = r'..\Utah\Address.gdb\Address_Alternate'
    ugrc_alias_utah = r'..\Utah\Utah.gdb\AliasAddressPoints_Utah'

    utah_cnty_flds =  ['ADDRNUM', 'ROADPREDIR', 'ROADNAME', 'ROADTYPE',
                      'POINT_X', 'POINT_Y']
        
    truncateOldCountyPts(ugrc_alias_utah)


    hwy_dict = {'HIGHWAY 189':'HWY 189', 'HIGHWAY 198':'HWY 198', 'HIGHWAY 89':'HWY 89', 'SR 114':'HWY 114', 
                'SR 115':'HWY 115', 'SR 141':'HWY 141', 'SR 146':'HWY 146', 'SR 147':'HWY 147',
                'SR 156':'HWY 156', 'SR 164':'HWY 164', 'SR 178':'HWY 178', 'SR 198':'HWY 198',
                'SR 51':'HWY 51', 'SR 68':'HWY 68', 'SR 73':'HWY 73', 'SR 77':'HWY 77',
                'SR 92':'HWY 92', 'SR115':'HWY 115', 'SR141':'HWY 141', 'SR146':'HWY 146',
                'SR147':'HWY 147', 'SR198':'HWY 198', 'SR265':'HWY 265', 'SR51':'HWY 51',
                'SR77':'HWY 77', 'US  89':'HWY 89', 'US 189':'HWY 189', 'US 6':'HWY 6',
                'US 89':'HWY 89', 'US6':'HWY 6', 'US89':'HWY 89', 'UT 89':'HWY 89'}

    error_values = [0, '0', None, '', ' ', 'NA', '<Null>']

    with arcpy.da.SearchCursor(utah_cnty_alias, utah_cnty_flds) as scursor, \
        arcpy.da.InsertCursor(ugrc_alias_utah, alias_flds) as icursor:

        for row in scursor:
            if row[0] not in error_values and row[2] not in error_values:
                add_num = row[0]
                pre_dir = removeNone(row[1]).strip()
                street_name = row[2].strip()
                stype = return_key(row[3], stype_dir)

                if street_name[0].isdigit():
                    suf_dir = street_name.split()[1][0]
                    street_name = street_name.split()[0]
                    stype = ''
                else:
                    suf_dir = '' 

                if street_name in hwy_dict:
                    street_name = hwy_dict[street_name]
                    stype = ''
                    suf_dir = ''

                x = row[4]
                y = row[5]
                if x == None:
                    continue
                shp = arcpy.Point(x, y)

                
                icursor.insertRow(('', add_num, '', pre_dir, street_name, stype, suf_dir, 
                                    '', '', '', '', '49049', '', shp))
                
    fc_dict = {'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', ''],
               'ZipCode':['SGID.BOUNDARIES.ZipCodes', 'ZIP5', ''],
               'City': ['SGID.BOUNDARIES.Municipalities', 'SHORTDESC', ''],}

    addPolyAttributes(sgid, ugrc_alias_utah, fc_dict)
    update_alias_AddPtID(ugrc_alias_utah)
                

            


UtahCounty_alias()