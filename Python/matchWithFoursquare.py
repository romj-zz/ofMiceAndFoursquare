# -*- coding: utf-8 -*-

# File that matches data from the NYC hygiene database with the Foursquare API.
# The database must be populated with the NYC data before starting.

import foursquare
import csv
import mysql.connector
import unicodedata

# A few functions
def filterDictList(dictlist, key, valuelist):
      return [dictio for dictio in dictlist if dictio[key] in valuelist]

# Function matching the addresses written in the NYC database with the ones of the Foursquare API
def adressToString(address):
	newAd = address.lower().replace(' ','').replace(',','').replace('avenue','ave').replace('street','st').replace('road','rd').replace('th','').replace('st','').replace('rd','').replace('nd','')
	return newAd

# Normalising the received info from Foursquare. We can receive some strings that are not ascii
def normStr(txt):
	if str == '':
		return ''
	elif type(txt) is str:
		return txt
	elif type(txt) is float or type(txt) is int:
		return str(txt)
	else:
		return unicodedata.normalize('NFKD', txt).encode('ascii','ignore')

# A few settings
# Max number of request when this file is called
maxRequest = 5000
# Minimum Match score required to be added in the database
minimumMatchScore = 30

# INIT foursquare 
clientID = 'YOUR_CLIENT_ID'
#clientID ='bla'
clientSecret = 'YOUR_CLIENT_SECRET'
client = foursquare.Foursquare(client_id=clientID, client_secret=clientSecret, redirect_uri='')


default = '';

# INIT DB
cnx = mysql.connector.connect(user='root', password='root',host='localhost', port='3306', unix_socket='/Applications/MAMP/tmp/mysql/mysql.sock',database='resto')
req = cnx.cursor(buffered=True)
upd = cnx.cursor(buffered=True)
ins = cnx.cursor(buffered=True)

query = ("SELECT `id`, `venue_dba`, `venue_city`,`venue_state`, `venue_building`, `venue_street`, `venue_zip`, `venue_phone`, `venue_cuisine` FROM `venues` WHERE `venue_fqid` = 0 AND `venue_state` <> '' LIMIT 0,"+str(maxRequest))
update = ("UPDATE venues SET `venue_fqid` = %s , `venue_tipCount` = %s , `venue_checkinsCount` = %s , `venue_usersCount` = %s, `venue_rating` = %s, `venue_lat` = %s, `venue_lng` = %s, `venue_price` = %s WHERE `id` = %s")
insert = ("INSERT INTO `phrases` (`phrase_camis`, `typ`, `phrase`) VALUES (%s,  %s,  %s)")
req.execute(query)
restaurantQualifiers = ['restaurant', 'pizza', 'kitchen', 'coffee shop']

for (venue_id, venue_dba, venue_city, venue_state, venue_building, venue_street, venue_zip, venue_phone, venue_cuisine) in req:
	# Prepare Fq search
	near = venue_city+', '+venue_state
	address = normStr((venue_building+' '+venue_street+', '+str(venue_zip)))
	search = client.venues.search(params={'query': venue_dba, 'near': near, 'address': address})
	mainAd = adressToString(venue_building+venue_street)
	matches = []
	highestScore = 0
	# We are probably getting a lot of results for one search (imagine one for "wendy's" near manhattan)
		# We will score them according to the type of data that matches, and keep the one with the best score (higher than minimumMatchScore)
	for row in search['venues']:
		print '	'+row['name']		
		addressrow = normStr(row['location'].get('address',default))
		postalCode = normStr(row['location'].get('postalCode',default))
		city = normStr(row['location'].get('city',default))
		phone = normStr(row['location'].get('phone',default))
		name = normStr(row.get('name',default))
		row['match_score'] = 0
		# Matching phone
		if (phone == venue_phone and venue_phone != ''):
			print '		phone match ! '+phone+' - '+name+' '+addressrow+', '+postalCode+' '+city
			row['match_score'] = 100
			print '		increment score up to '+str(row['match_score'])
			matches.append(row)
		# Matching name
		if name.lower() == venue_dba.lower():
			row['match_score'] += 50
			print '		name match - '+name+' '+addressrow+', '+postalCode+' '+city
			print '		increment score up to '+str(row['match_score'])
		elif (name.lower() in venue_dba.lower() or venue_dba.lower() in name.lower()) and (name.lower() not in restaurantQualifiers):
			row['match_score'] += 15
			print '		name partial match - '+name+' '+addressrow+', '+postalCode+' '+city
			print '		increment score up to '+str(row['match_score'])
		#Matching address
		rowAd = adressToString(addressrow)
		if mainAd == rowAd:
			print '		address match - '+name+' '+addressrow+', '+postalCode+' '+city
			row['match_score'] += 40	
			print '		increment score up to '+str(row['match_score'])	
		#Matching zipcode
		if str(postalCode) == str(venue_zip):
			print '		postalCode match - '+name+' '+addressrow+', '+postalCode+' '+city
			row['match_score'] += 10
			print '		increment score up to '+str(row['match_score'])
		#Filter out places that are not restaurants :
		for category in row['categories']:
			# quite un-pythonesque snippet :
			# use this flag to break x 2 of from loop, to make sure the score is incremented just once
			fResto = 0
			for restaurantQualifier in restaurantQualifiers:
				if restaurantQualifier in category['name'].lower():
					print '		restaurant match : '+category['name']
					row['match_score'] += 5
					print '		increment score up to '+str(row['match_score'])
					fResto = 1
					break
				if fResto:
					break
		if row['match_score']>0:
			matches.append(row)
			highestScore = max(highestScore,row['match_score'])
				
	#print 'the highest score is '+str(highestScore)
	if highestScore < minimumMatchScore:
		print 'No sufficient score'
		data_update = (-1,0,0,0,0,'', '', 0,venue_id)
		upd.execute(update,data_update)
		cnx.commit()
	# Only keep matches with the highest score
	matches = filterDictList(matches,'match_score',[highestScore])		
	if len(matches) == 0:
		print 'no match for '+venue_dba
		data_update = (-1,0,0,0,0,'', '', 0,venue_id)
		upd.execute(update,data_update)
		cnx.commit()
	elif len(matches) == 1:
		venueDetails = client.venues(matches[0]['id'])
		rating = venueDetails['venue'].get('rating', default)
		location = venueDetails['venue'].get('location',default)
		if location == '':
			lat = ''
			lng = ''
		else:
			lat = normStr(location.get('lat',default))
			lng = normStr(location.get('lng',default))
		price = venueDetails['venue'].get('price',default)
		if price == '':
			tier = ''
		else:
			tier = normStr(price.get('tier',default))
		phrases = venueDetails['venue'].get('phrases',default)
		for phrase in phrases:
			text = normStr(phrase.get('phrase',default))
			data_insert = (venue_id,1,text)
			ins.execute(insert,data_insert)
		data_update = (matches[0]['id'],matches[0]['stats']['tipCount'],matches[0]['stats']['checkinsCount'],matches[0]['stats']['usersCount'],rating,lat, lng, tier,venue_id)
		upd.execute(update,data_update)
		cnx.commit()
		print 'updating only match with score of '+str(highestScore)+', fqID = '+matches[0]['id']
	else:
		matches = sorted(matches, key=lambda k: k['match_score']) 
		print str(len(matches))+' matches, need further filtering'
		data_update = (-2,0,0,0,0,'', '', 0,venue_id)
		upd.execute(update,data_update)
		cnx.commit()
cnx.close()


