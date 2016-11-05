import xml.etree.ElementTree as ET
import sqlite3
from urllib.request import urlopen
train_types = ['D', 'M', 'S']


def setUpSQLTables():
	connection = sqlite3.connect("irishstats.db")
	cursor = connection.cursor()
	cursor.execute("""DROP TABLE currenttimes;""")
	sql_command = """CREATE TABLE currenttimes ( train_code VARCHAR(20) PRIMARY KEY, train_type VARCHAR(1), status VARCHAR(1), direction CHAR(1), latitude REAL, longitude REAL, islate BOOLEAN, public_msg VARCHAR(100));"""
	cursor.execute(sql_command)

	# never forget this, if you want the changes to be saved:
	connection.commit()

def fetchRealtimeData():
	#dart query
	print ("Fetching data...")
	urls = {'D' : 'http://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML_WithTrainType?TrainType=D',
	'M' : 'http://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML_WithTrainType?TrainType=M',
	'S' : 'http://api.irishrail.ie/realtime/realtime.asmx/getCurrentTrainsXML_WithTrainType?TrainType=S'}


	for types in train_types:
		query = urlopen(urls[types])
		extractCurrentTime(query, types)

	print ("Fetched data!")

#XML 4
def extractCurrentTime(xmlfile, train_type):
	tree = ET.parse(xmlfile)
	root = tree.getroot()
	connection = sqlite3.connect("irishstats.db")
	cursor = connection.cursor()
	
	islate = False
	i = 0
	for child in root:
		status = root[i][0].text
		latitude = root[i][1].text
		longitude = root[i][2].text
		train_code = root[i][3].text
		public_msg = root[i][5].text
		if ("late" in public_msg):
			islate = True
		direction = root[i][6].text

		i=i+1
		if ("-" in public_msg and status == 'R'):
			public_msg = cutStringAt(public_msg, " - ", 1)
		params = (train_code, train_type, status, direction, latitude, longitude, islate, public_msg)
		sql_command = "INSERT INTO currenttimes VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
		cursor.execute(sql_command, params)
		connection.commit()

def cutStringAt(string, cutChar, pos):
	return string.split(cutChar)[pos]

		

def getRealTimeStats():
	connection = sqlite3.connect("irishstats.db")
	cursor = connection.cursor()
	lateTrains = 0
	print ("\nSOUTHBOUND TRAINS WITHIN DUBLIN:")
	cursor.execute("SELECT * FROM currenttimes WHERE train_type='D' AND direction='Southbound' AND status='R';")
	result = cursor.fetchall() 
	for r in result:
		print(r[7])
	sbDublin = (len(result))

	print ("\nNORTHBOUND TRAINS WITHIN DUBLIN:")
	cursor.execute("SELECT * FROM currenttimes WHERE train_type='D' AND direction='Northbound' AND status='R';")
	result = cursor.fetchall() 
	for r in result:
		print(r[7])
	nbDublin = (len(result))

	print ("\nOUTSIDE OF DUBLIN:")
	cursor.execute("SELECT * FROM currenttimes WHERE train_type='M' AND status='R';")
	result = cursor.fetchall() 
	for r in result:
		print(r[7])
	outsideDublin = (len(result))

	print ("\nSUBURBS OF DUBLIN:")
	cursor.execute("SELECT * FROM currenttimes WHERE train_type='S' AND status='R';")
	result = cursor.fetchall() 
	for r in result:
		print(r[7])
	suburbDublin = (len(result))

	print ("\nTRAINS RUNNING LATE:")
	nb = 0
	sb = 0
	cursor.execute("SELECT * FROM currenttimes WHERE islate=1 AND status='R';")
	result = cursor.fetchall() 
	for r in result:
		if checkIfActuallyLate(r[7]) == True:
			lateTrains=lateTrains+1
			print (r[7])
			if (r[1] == 'D'):
				if r[3] == "Southbound":
					sb = sb + 1
				elif (r[3] == "Northbound"):
					nb = nb + 1

	num_trains = getCurrentRunningTrains()
	dueToStart = getDueToStartTrains()
	print ("\nThere are %d trains currently running in Ireland: \n\t%d are on the dart line, \n\t%d are on the main line, \n\t%d are on the suburban line" % (num_trains, sbDublin + nbDublin, outsideDublin, suburbDublin))
	print ("On the dart line: %d are running Southbound, and %d are running Northbound." % (sb, nb))
	print ("There are %d trains due to start running in the next 10 minutes." % (dueToStart))
	print ("\nTHE MOST COMMON DIRECTION:")
	cursor.execute("SELECT direction, COUNT(direction) AS 'value_occurrence' FROM currenttimes GROUP BY direction ORDER BY 'value_occurrence' DESC LIMIT 1")
	result = cursor.fetchall()
	print (result)
	print ("There are %d trains currently running in Ireland, and %d are late" % (num_trains, lateTrains))




def getDueToStartTrains():
	connection = sqlite3.connect("irishstats.db")
	cursor = connection.cursor()
	i = 0
	cursor.execute("SELECT * FROM currenttimes WHERE status='N'")
	result = cursor.fetchall() 
	return len(result)

def checkIfActuallyLate(msg):
	if ('(0 ' in msg or '(1 ' in msg or '(2 ' in msg or '(3 ' in msg or '(4 ' in msg):
		return False
	if ('-' in msg):
		return False
	return True

def getCurrentRunningTrains():
	connection = sqlite3.connect("irishstats.db")
	cursor = connection.cursor()
	i = 0
	cursor.execute("SELECT * FROM currenttimes WHERE status='R'")
	result = cursor.fetchall() 
	return len(result)

def main():

	
	setUpSQLTables()
	fetchRealtimeData()
	getRealTimeStats()
	

	

main()