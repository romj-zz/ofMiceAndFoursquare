
#!/usr/bin/python

# Importing the NYC restaurant data in a mysql database.


import csv
import mysql.connector
from datetime import datetime, date, timedelta



#open connexion and prepare request
cnx = mysql.connector.connect(user='root', password='root',host='localhost', port='3306', unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',database='resto')
# Truncate tables for a clean start
# truncate = cnx.cursor(buffered=True)
# truncate_camis = ("TRUNCATE TABLE `venues`")
# truncate_inspect = ("TRUNCATE TABLE `inspections`")
# truncate.execute(truncate_camis)
# truncate.execute(truncate_inspect)

insert = cnx.cursor(buffered=True)


insert_camis = (
  "INSERT IGNORE INTO `venues` "
		"(`venue_camis`, `venue_dba`, `venue_boro`, `venue_building`, `venue_street`, `venue_zip`, `venue_phone`, `venue_cuisine`)"
		"VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
insert_inspect = (
  "INSERT INTO `inspections` "
		"(`inspect_camis`, `inspect_date`, `inspect_action`, `inspect_code`, `inspect_violation`, `inspect_crit`, `inspect_score`, `inspect_grade`, `inspect_grade_date`, `inspect_record_date`, `inspect_type`) "
		"VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")

with open('HygieneData/DOHMH_New_York_City_Restaurant_Inspection_Results.csv', 'r') as inputFile:
	k = 0
	reader = csv.DictReader(inputFile)
	for row in reader:
		data_camis = (row['CAMIS'], row['DBA'], row['BORO'], row['BUILDING'], row['STREET'],row['ZIPCODE'],row['PHONE'],row['CUISINE DESCRIPTION'])
		insert.execute(insert_camis,data_camis)
		data_insert = (row['CAMIS'],strToDate(row['INSPECTION DATE']),row['ACTION'],row['VIOLATION CODE'],row['VIOLATION DESCRIPTION'],stringToCrit(row['CRITICAL FLAG']),row['SCORE'],row['GRADE'],strToDate(row['GRADE DATE']),strToDate(row['RECORD DATE']),row['INSPECTION TYPE'])
		insert.execute(insert_inspect,data_insert)
		cnx.commit()
cnx.close()

# custom func and var
def strToDate( string ):
	aDate = string.split('/')
	if len(aDate) > 2:
		stringToDate = date(int(aDate[2]),int(aDate[0]), int(aDate[1]))
	else:
		stringToDate = 0
	return stringToDate;
def stringToCrit( string ):
	if string == 'Critical':
		return 1
	elif string == 'Not Critical':
		return 2
	else:
		return 0