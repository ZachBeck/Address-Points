import arcpy

rds = r'C:\sde\DC_TRANSADMIN@UTRANS@itdb104.dts.utah.gov.sde\UTRANS.TRANSADMIN.Centerlines_Edit\UTRANS.TRANSADMIN.Roads_Edit'

flds = ['ADDRSYS_L', 'ADDRSYS_R', 'PREDIR', 'NAME', 'POSTTYPE', 'POSTDIR', 'A1_NAME',
        'A1_POSTTYPE', 'A2_NAME', 'A2_POSTTYPE', 'AN_NAME', 'AN_POSTDIR', 'CARTOCODE']

ADDRSYS_L = 0
ADDRSYS_R =0
PREDIR = 0
NAME = 0
POSTTYPE = 0
POSTDIR = 0
A1_NAME = 0
A1_POSTTYPE = 0
A2_NAME = 0
A2_POSTTYPE = 0
AN_NAME = 0
AN_POSTDIR = 0
CARTOCODE = 0

with arcpy.da.SearchCursor(rds, flds) as scursor:
    for row in scursor:
        if row[0] == None:
            ADDRSYS_L = ADDRSYS_L + 1
        if row[1] == None:
            ADDRSYS_R = ADDRSYS_R + 1
        if row[2] == None:
            PREDIR = PREDIR + 1
        if row[3] == None:
            NAME = NAME + 1
        if row[4] == None:
            POSTTYPE = POSTTYPE + 1
        if row[5] == None:
            POSTDIR = POSTDIR + 1
        if row[6] == None:
            A1_NAME = A1_NAME + 1
        if row[7] == None:
            A1_POSTTYPE = A1_POSTTYPE + 1
        if row[8] == None:
            A2_NAME = A2_NAME + 1
        if row[9] == None:
            A2_POSTTYPE = A2_POSTTYPE + 1
        if row[10] == None:
            AN_NAME = AN_NAME + 1
        if row[11] == None:
            AN_POSTDIR = AN_POSTDIR + 1
        if row[12] in ['', None]:
            CARTOCODE = CARTOCODE + 1

print('-----NULL values found-----')
# print(f'ADDRSYS_L has {ADDRSYS_L} nulls')
print('ADDRSYS_L has {} nulls'.format(ADDRSYS_L))
print(f'ADDRSYS_R has {ADDRSYS_R} nulls')
print(f'PREDIR has {PREDIR} nulls')
print(f'NAME has {NAME} nulls')
print(f'POSTTYPE has {POSTTYPE} nulls')
print(f'POSTDIR has {POSTDIR} nulls')
print(f'A1_NAME has {A1_NAME} nulls')
print(f'A1_POSTTYPE has {A1_POSTTYPE} nulls')
print(f'A2_NAME has {A2_NAME} nulls')
print(f'A2_POSTTYPE has {A2_POSTTYPE} nulls')
print(f'AN_NAME has {AN_NAME} nulls')
print(f'AN_POSTDIR has {AN_POSTDIR} nulls')
print(f'CARTOCODE has {CARTOCODE} nulls')