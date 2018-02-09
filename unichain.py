import Savoir
import cryptography
import datetime
import pickle as pickle
import os
import binascii
import random
import pip
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet

# The Multichain structure is basically as follows:
# There are five "streams" on the chain which effectively serve as labels.
# Hexadecimal data can be published to these streams. 
# Each entry is associated with one of multiple "keys" which are just small strings with identifying information.
# Through the Multichain API, these entries can be retrieved through any number of identifying parameters.
# You can mainly list items by stream, key, or transaction ID. 

# The first stream publishes users' public keys, with the key for those entries being the student or teacher's ID number.
# The second stream publishes the actual grades, each encrypted with a random secret passphrase. They keys for these entries are the student ID and the course ID.
# The third stream publishes those secret passphrases, encrypted with the public key of the user who has been granted access to that data. The keys for these entries are the transaction ID of the grade it is providing access to and the ID number of the person who is being provided access.
# The fourth stream contains a public list of courses, with the key being a course ID number.
# Finally, the fifth stream contains a blacklist of transaction IDs which correspond to grades which have been edited or changed.

# Data can be encrypted by anyone who has a user's public key, but that data can ONLY be decrypted with that user's private key.
# The idea is that faculty can enter encrypted grades that can be accessed by only those users who have access items in the third stream.
# This system effectively introduces privacy into a blockchain which can inherently be read by everyone who has a copy.

# The student class serves mainly to add a student's public key to the pubKeys stream.
# It generates a private key for the student to keep in order to access any grades.
class Student:

	# Variable initialization
	id = 0
	name = ""
	
	# Constructor
	def __init__(self, id, name, address):
		self.id = id
		self.name = name
		self.address = address
		
		# Check if this is the first student being registered
		firstStudent = False
		if len(api.liststreamitems("pubKeys")) == 0:
			firstStudent = True
		
		# If student is not registered:
		if (not checkStudent(self.id)) or firstStudent:
		
			# Generate RSA key pair
			privKey = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)
			pubKey = privKey.public_key()
			pubKeyPEM = pubKey.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

			# Write private key to file
			file = open("privKey.txt", "wb+")
			file.write(privKey.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
				
			# Publish student pubkey with student ID, name, and Multichain address as identifying keys
			api.publish("pubKeys", [str(self.id), self.name, self.address], {"text": bytes.decode(pubKeyPEM)})
			
		# If student is registered:
		else:
			print("Student already registered!")

# Check if student exists given ID
def checkStudent(studentID):
	
	# Check if a student with that ID exists on the chain	
	for student in api.liststreamitems("pubKeys"):
		if student.get("keys")[0] == str(studentID):
			return True
			
	return False					

# The teacher class serves mainly to add a teacher's public key to the pubKeys stream.
# It generates a private key for the teacher to keep in order to access or add any grades.
class Teacher:

	# Variable initialization
	id = 0
	name = ""
	
	# Constructor
	def __init__(self, id, name, address):
		self.id = id
		self.name = name
		self.address = address
		
		# Check if this is the first teacher being registered
		firstTeacher = False
		if len(api.liststreamitems("pubKeys")) == 0:
			firstTeacher = True
					
		# If teacher is not registered:
		if (not checkTeacher(self.id)) or firstTeacher:
		
			# Generate RSA key pair
			privKey = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)
			pubKey = privKey.public_key()
			pubKeyPEM = pubKey.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

			# Write private key to file
			file = open("privKey.txt", "wb+")
			file.write(privKey.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
				
			# Publish teacher pubkey with teacher ID, name, and Multichain address as identifying keys
			print("Publishing teacher with ID " + self.id + " and name " + self.name)
			api.publish("pubKeys", [str(self.id), self.name, self.address], {"text": bytes.decode(pubKeyPEM)})
			
		# If teacher is registered:
		else:
			print("Teacher already registered!")		

# Check if teacher exists given ID
def checkTeacher(teacherID):
	
	# Check if a student with that ID exists on the chain	
	for teacher in api.liststreamitems("pubKeys"):
		if teacher.get("keys")[0] == str(teacherID):
			return True
			
	return False

# The Grade class models all the data that goes into a grade entry.
# Objects of this class will be serialized and published to the blockchain.
class Grade:

	# Variable initialization
	studentID = 0
	name = ""
	score = 0
	courseID = 0
	comments = ""
	date = datetime.date(2000, 1, 1)
	category = ""
	
	# Constructor
	def __init__(self, studentID, name, score, courseID, comments, date, category):
		self.studentID = studentID
		self.name = name
		self.score = score
		self.courseID = courseID
		self.comments = comments
		self.date = date
		self.category = category		

# The Course class registers Course objects and publishes them to the courses stream.
class Course:

	# Variable initialization
	name = ""
	teacherID = 0
	courseID = 0
	categories = {}
	
	# Constructor
	def __init__(self, name, teacherID, courseID, categories):
		self.name = name
		self.teacherID = teacherID
		self.courseID = courseID						
		self.categories = categories
		
		# Check if this is the first course being registered
		firstCourse = False
		if len(api.liststreamitems("courses")) == 0:
			firstCourse = True
			
		# Check if course is already registered
		registered = False
		if firstCourse == False:
			for course in api.liststreamitems("courses"):
				if course.get("keys")[0] == str(self.courseID):
					registered = True
					break

		# Check if teacher exists based on given teacher ID
		if not checkStudent(str(teacherID)):
			print("Teacher does not exist!")
			return None
		
		# If course is not registered:
		if (not checkCourse(self.courseID) or firstCourse):
			
			# Serialize course and publish to blockchain with course ID, name, and teacher ID as identifying keys
			pickledCourse = pickle.dumps(self)
			print("Publishing course with id " + str(self.courseID) + " and name " + self.name + " and teacher ID " + str(self.teacherID))
			api.publish("courses", [str(self.courseID), self.name, str(self.teacherID)], bytes.decode(binascii.hexlify(pickledCourse)))
			
		# If course is already registered:
		else:
			print("Course already registered!")		

# Check if course exists given course ID
def checkCourse(courseID):
	
	for course in api.liststreamitems("courses"):
		if course.get("keys")[0] == str(courseID):
			return True
			
	return False

# Check if course exists given course name
def checkCourseFromName(name):
	for course in api.liststreamitems("courses"):
		if course.get("keys")[1] == name:
			return True
			
	return False
	
# Check if category exists within a given course
def checkCategory(courseID, category):

	# If course exists:
	if checkCourse(courseID):
	
		# Load course from blockchain
		course = pickle.loads(binascii.unhexlify(api.liststreamkeyitems("courses", str(courseID))[0].get("data")))
		
		# If category exists:
		if (category in course.categories.keys()):
			return True
		else:
			return False
			
	else:
		return False

# Get student ID given student name
def getStudentID(name):
	
	# If there is a student with given name:
	if (len(api.liststreamkeyitems("pubKeys", name)) == 1):
	
		# Return ID of that student
		return api.liststreamkeyitems("pubKeys", name)[0].get("keys")[0]
		
	else:
		return None

# Get student name given student ID
def getStudentName(id):
	
	# If there is a student with given ID:
	if (len(api.liststreamkeyitems("pubKeys", id)) == 1):
	
		# Return name of that student
		return api.liststreamkeyitems("pubKeys", id)[0].get("keys")[1]
		
	else:
		return None

# Get course object given course ID		
def getCourseFromID(id):
	
	# If there is a course with given ID:
	if (len(api.liststreamkeyitems("courses", str(id))) == 1):
		
		# Load and return that course
		return pickle.loads(binascii.unhexlify(api.liststreamkeyitems("courses", str(id))[0].get("data")))
		
	else:
		return None

# Get course object given course name				
def getCourseFromName(name):

	# If there is a course with given name:
	if (len(api.liststreamkeyitems("courses", str(name))) == 1):
	
		# Load and return that course
		return pickle.loads(binascii.unhexlify(api.liststreamkeyitems("courses", str(name))[0].get("data")))
		
	else:
		return None

# Calculate letter grade given a decimal score
def calcGrade(score):
	if (score >= .95):
		return "A+"
	elif (score >= .875 and score < .95):
		return "A"
	elif (score >= .845 and score < .875):
		return "A-"
	elif (score >= .815 and score < .845):
		return "B+"
	elif (score >= .775 and score < .815):
		return "B"
	elif (score >= .745 and score < .775):
		return "B-"
	elif (score >= .715 and score < .745):
		return "C+"
	elif (score >= .685 and score < .715):
		return "C"
	elif (score >= .650 and score < .685):
		return "C-"
	elif (score >= .60 and score < .650):
		return "D"
	else:
		return "F"
	
# Method to add a new grade
def addGrade(studentID, name, score, courseID, comments, date, category):
	
	# Construct a new Grade object and serialize it with pickle
	newGrade = Grade(studentID, name, score, courseID, comments, date, category)
	pickledGrade = pickle.dumps(newGrade)
	 
	# Generate new random secret password with Fernet
	secret = Fernet.generate_key()
	fernet = Fernet(secret)
		
	# Encrypt serialized grade with secret, then convert result to hex
	encryptedGrade = fernet.encrypt(pickledGrade)
	encryptedGradeHex = binascii.hexlify(encryptedGrade)
				
	# Publish encrypted grade hex and record transaction ID coming out
	txout = api.publish("items", [str(studentID), str(courseID)], bytes.decode(encryptedGradeHex))
	
	# Get teacher ID corresponding to this course
	teacherID = api.liststreamkeyitems("courses", str(courseID))[0].get("keys")[2]
		
	# Retrieve relevant student and teacher's pubkeys from blockchain and deserialize them
	pubKeyStudentList = api.liststreamkeyitems("pubKeys", str(studentID))
	pubKeyTeacherList = api.liststreamkeyitems("pubKeys", teacherID) 
	pubKeyStudent = serialization.load_pem_public_key(bytes(pubKeyStudentList[0].get("data").get("text"), "utf-8"), backend=default_backend())
	pubKeyTeacher = serialization.load_pem_public_key(bytes(pubKeyTeacherList[0].get("data").get("text"), "utf-8"), backend=default_backend())	
	
	# Encrypt secret password with student and teacher's pubkeys and convert results to hex
	encryptedStudentSecret = pubKeyStudent.encrypt(secret, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
	encryptedStudentSecretHex = binascii.hexlify(encryptedStudentSecret)
	encryptedTeacherSecret = pubKeyTeacher.encrypt(secret, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
	encryptedTeacherSecretHex = binascii.hexlify(encryptedTeacherSecret)
	
	# Publish the pubkey-encrypted secret password along with identifying transaction ID for both the teacher and the student
	api.publish("access", [str(studentID), str(txout)], bytes.decode(encryptedStudentSecretHex))
	api.publish("access", [str(teacherID), str(txout)], bytes.decode(encryptedTeacherSecretHex))
	
	# Return TXID from publishing of grade
	return txout

# This method returns a list of grades that match a certain set of parameters.
# Using the double asterisk syntax, it can take any number of key-value pairs as a list of parameters.
# These parameters are designed to correspond to Grade object attributes.
def getGrades(**kwargs):

	
	# Copy accessibleGrades into new dictionary
	gradeList = dict(updateAccessible())

	# Check that list of parameters is not empty
	if len(kwargs.keys()) > 0:
	
		# If a TXID is specified, just return that one specific grade immediately
		if "txid" in kwargs.keys():
			return gradeList.get(kwargs.get("txid"))
	
		# Iterate over list of supplied parameters
		for param in kwargs.keys():

			# Iterate over a copy of gradeList and delete entries if any of their attributes do not equal the supplied parameter values		
			for txid, grade in gradeList.copy().items():
				if getattr(grade, param) != kwargs.get(param):
					del gradeList[txid]
		
		# Return result gradeList with deleted entries			
		return gradeList	
			
	# If list of parameters is empty:
	else:
		print("No arguments given!")
		return None			

# Calculate weighted average for a course given its course ID and a list of grades
def calcAverage(courseID, gradeList):

	# Initialize variables
	avg = 0.0
	addedWeights = 0.0
	weightList = {}
	course = getCourseFromID(courseID)	
	
	# Iterate over list of grades to build a list of categories in the course
	for grade in gradeList.values():
		
		# If course ID matches supplied ID:
		if grade.courseID == courseID and grade.score != -1:
		
			# If category is not already in list:
			if grade.category not in weightList.keys():
			
				# Add category to list with its name as the key and its weight as the value
				weightList[grade.category] = course.categories.get(grade.category)
				
	# If there are no categories:
	if len(weightList) == 0:
		return None
	
	# Iterate over list of categories
	for category, weight in weightList.items():
	
		# Initialize counter, which counts the number of grades processed, and totalScore, which tracks the added score of all the grades
		counter = 0
		totalScore = 0
		
		# Iterate over list of grades
		for grade in gradeList.values():
		
			# If category matches this category and course ID:
			if grade.category == category and grade.courseID == courseID and grade.score != -1:
				
				# Increment counter and total score appropriately
				counter += 1
				totalScore += grade.score
		
		# Add total average for this category to the global course average (multiplied by weight appropriately)
		avg += weight * (totalScore / counter)
	
	# If the weights do not add up to 100%:
	if sum(weightList.values()) != 1.0:
		
		# Divide average by the sum of the weights
		avg = avg / sum(weightList.values())
	
	# Calculate letter grade from average and return it
	return calcGrade(avg)

# This method serves to "edit" Grade items on the blockchain.
# Since the blockchain is not truly editable, this "editing" is more like "replacing".
# It utilizes the blacklist to mark the transaction being "edited" as no longer valid.
# It also publishes a new item with the changed values to take the place of the blacklisted one.	
# Similarly to the getGrades method, it can take any number of key-value pairs as parameters for the values to change.				
def edit(txid, **kwargs):
	
	# Check if given TXID is in list of accessible grades
	if str(txid) in accessibleGrades.keys():
	
		# Get student ID for specified grade
		studentID = api.getstreamitem("items", txid).get("keys")[0]
	
		# Publish TXID of item being edited to the blacklist stream with student ID as the key
		api.publish("blacklist", str(api.getstreamitem("items", txid).get("keys")[0]), str(txid))
		
		# Get grade being edited
		gradeSource = accessibleGrades.get(str(txid))
		
		# Construct a new grade with values based on the grade being edited
		newGrade = Grade(gradeSource.studentID, gradeSource.name, gradeSource.score, gradeSource.courseID, gradeSource.comments, gradeSource.date, gradeSource.category) 
	
		# Check that list of parameters is not empty
		if len(kwargs.keys()) > 0:
			
			# Iterate over list of parameters and change new grade values accordingly
			for param in kwargs.keys():
				setattr(newGrade, param, kwargs.get(param))
		
		# Add new grade and return TXID coming out
		txout = addGrade(str(studentID), newGrade.name, newGrade.score, newGrade.courseID, newGrade.comments, newGrade.date, newGrade.category)
		return txout
	
	# If TXID not found in list of accessible grades:
	else:
		print("Grade not found!")
		return None

# This method generates a list of all grades, courses, and students (in the case of a teacher) that are accessible by the entered student ID.
# By generating this list at startup and periodically refreshing it, interactions become much faster since no data is being read live from the blockchain.
# This list is also convenient for displaying the grades which are actually relevant to the user.
# Finally, it prevents the program from attempting to access any grades belonging to a different user.		
def updateAccessible():
	
	# Create list of blacklisted TXIDs from blockchain
	blacklist = []
	for item in api.liststreamkeyitems("blacklist", str(currentID)):
		blacklist.append(item.get("data"))

	# List all access points corresponding to the entered ID number
	accessPoints = api.liststreamkeyitems("access", str(currentID))
	
	# Clear out old lists
	accessibleGrades.clear()
	accessibleCourses.clear()
	accessibleStudents.clear()
	
	# Iterate over list of access points
	for accessPoint in accessPoints:
	
		# Get TXID of corresponding item for current access point
		txid = accessPoint.get("keys")[1]
	
		# Check if TXID is in the blacklist
		if str(txid) in blacklist:
			pass
		
		# If TXID is not in blacklist, add grade to list of accessible grades
		else:
		
			# Decrypt secret passphrase with entered private key
			secret = privKey.decrypt(binascii.unhexlify(accessPoint.get("data")), padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
			fernet = Fernet(secret)
	
			# Get, decrypt, and deserialize the grade with the TXID listed in the access point
			encryptedGradeHex = api.getstreamitem("items", txid).get("data")
			encryptedGrade = binascii.unhexlify(encryptedGradeHex)
			pickledGrade = fernet.decrypt(encryptedGrade)
			grade = pickle.loads(pickledGrade)
	
			# Add the grade to the list of all accessible grades
			accessibleGrades[str(txid)] = grade

	# If the user is a teacher, use their current ID to list all of their taught courses
	courseList = []
	if teacher:
		courseList = api.liststreamkeyitems("courses", currentID)
	
	# Iterate over list of accessible grades
	for v in accessibleGrades.values():
	
		# Get grade's student ID, get name from that ID, and append result to list of accessible students
		studentID = v.studentID
		studentName = api.liststreamkeyitems("pubKeys", str(studentID))[0].get("keys")[1]
		accessibleStudents[studentID] = studentName
		
		# For students, since they have no teacher ID, their course list is generated by collecting course IDs from list of accessible grades:
		courseList.append(api.liststreamkeyitems("courses", str(v.courseID))[0])
	
	# Iterate over course list
	for course in courseList:
	
		# Load course object and add it to list of accessible courses
		courseObj = pickle.loads(binascii.unhexlify(course.get("data")))	
		accessibleCourses[courseObj.courseID] = courseObj				
	
	return accessibleGrades

# This next section of code runs every time the web interface starts up.
			
# Get chain parameters
chainname = input("Enter the chain name: \n")
saveFile = open(os.path.join(os.getcwd(), "chains", chainname, "apiparams"))

# Set up calls to Multichain API
api = Savoir.Savoir(saveFile.readline().strip(),
					saveFile.readline().strip(),
					saveFile.readline().strip(),
					saveFile.readline().strip(),
					chainname)
					
# Ensure that the current address is always updating the five streams by subscribing
api.subscribe("pubKeys")
api.subscribe("items")
api.subscribe("access")
api.subscribe("courses")
api.subscribe("blacklist")

# Initialize variables
teacher = False
myAdd = ""
currentID = 0
registered = False

# Get address of current user
for address in api.listaddresses():
	if address.get("ismine") == True:
		myAdd = address.get("address")	

# Check permissions of address; if the issue permission is granted, then this address is a teacher
for address in api.listpermissions("issue"):
	if address.get("address") == myAdd:
		teacher = True

# Check if current user is registered by searching for their address in the pubKeys stream
for item in api.liststreamitems("pubKeys"):
	if myAdd == item.get("keys")[2]:
		currentID = item.get("keys")[0]
		registered = True

# If the user has not yet been registered:
if not registered:

	# Ask for name
	name = input("Enter your first and last name.\n")
	
	# Generate random unique id for the user
	unique = False
	while not unique:
		randID = random.randint(1,1000)
		if not checkStudent(randID):
			unique = True
	
	# Publish student to blockchain and generate private key file
	currentID = str(randID)
	print("Your ID number is " + str(currentID))
	print("Generating private key...")
	currentStudent = Student(currentID, name, myAdd)
	print("A private key has been generated in 'privKey.txt' inside of this directory.")
	print("Do NOT lose this file. It is essentially your password for accessing the gradebook.")
	privKey = serialization.load_pem_private_key(open("privKey.txt", "rb").read(), password=None, backend=default_backend())

# If the user is already registered:		
else:

	# Ask for student/teacher ID and private key of user
	currentID = input("Please enter your ID number.\n")
	pubKey = serialization.load_pem_public_key(bytes(api.liststreamkeyitems("pubKeys", str(currentID))[0].get("data").get("text"), "utf-8"), backend=default_backend())
	path = input("Please enter the path to your private key.\n")
	privPEM = open(path, "rb").read()
	privKey = serialization.load_pem_private_key(privPEM, password=None, backend=default_backend())
	
# Initialize lists of accessible grades, courses, and students
accessibleGrades = {}
accessibleCourses = {}
accessibleStudents = {}

# Update those lists (see method for more information)
updateAccessible()
