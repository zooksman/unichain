import Savoir
import cryptography
import datetime
import pickle as pickle
import os
import binascii
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet

# Get chain parameters
chainname = input("Enter the chain name: \n")
saveFile = open(os.path.join(os.getcwd(), "chains", chainname, "apiparams"))

# Set up calls to Multichain API
api = Savoir.Savoir(saveFile.readline().strip(),
					saveFile.readline().strip(),
					saveFile.readline().strip(),
					saveFile.readline().strip(),
					chainname)
					
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
	def __init__(self, id, name):
		self.id = id
		self.name = name
		
		# Check if this is the first student being registered
		firstStudent = False
		if len(api.liststreamitems("pubKeys")) == 0:
			firstStudent = True
			
		# Check if student is already registered
		registered = False
		if firstStudent == False:
			for student in api.liststreamitems("pubKeys"):
				if student.get("keys")[0] == str(self.id):
					registered = True
					break
		
		# If student is not registered:
		if registered == False:
		
			# Generate RSA key pair
			privKey = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)
			pubKey = privKey.public_key()
			pubKeyPEM = pubKey.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

			# Write private key to file
			file = open("privKeyStudent.txt", "wb+")
			file.write(privKey.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
				
			# Publish student pubkey 
			api.publish("pubKeys", [str(self.id), self.name], {"text": bytes.decode(pubKeyPEM)})
			
			
		# If student is registered:
		else:
			print("Student already registered!")		
			
# The teacher class serves mainly to add a teacher's public key to the pubKeys stream.
# It generates a private key for the teacher to keep in order to access any grades.
class Teacher:

	# Variable initialization
	id = 0
	name = ""
	
	# Constructor
	def __init__(self, id, name):
		self.id = id
		self.name = name
		
		# Check if this is the first teacher being registered
		firstTeacher = False
		if len(api.liststreamitems("pubKeys")) == 0:
			firstTeacher = True
			
		# Check if teacher is already registered
		registered = False
		if firstTeacher == False:
			for teacher in api.liststreamitems("pubKeys"):
				if teacher.get("keys")[0] == str(self.id):
					registered = True
					break
		
		# If teacher is not registered:
		if registered == False:
		
			# Generate RSA key pair
			privKey = rsa.generate_private_key(backend=default_backend(), public_exponent=65537, key_size=2048)
			pubKey = privKey.public_key()
			pubKeyPEM = pubKey.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

			# Write private key to file
			file = open("privKeyTeacher.txt", "wb+")
			file.write(privKey.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
				
			# Publish teacher pubkey 
			api.publish("pubKeys", [str(self.id), self.name], {"text": bytes.decode(pubKeyPEM)})
			
		# If teacher is registered:
		else:
			print("Teacher already registered!")		

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
		
		# If course is not registered:
		if registered == False:
			
			# Serialize course and publish to blockchain
			pickledCourse = pickle.dumps(self)
			print("Publishing course with id " + str(self.courseID) + " and name " + self.name)
			api.publish("courses", [str(self.courseID), str(self.teacherID)], bytes.decode(binascii.hexlify(pickledCourse)))
			
		# If course is already registered:
		else:
			print("Course already registered!")		
	
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
	teacherID = api.liststreamkeyitems("courses", str(courseID))[0].get("keys")[1]
		
	# Retrieve relevant student and teacher's pubkeys from blockchain and deserialize them
	pubKeyStudentList = api.liststreamkeyitems("pubKeys", str(studentID))
	pubKeyTeacherList = api.liststreamkeyitems("pubKeys", str(teacherID)) 
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

# This method returns a list of grades that match a certain set of parameters
# Using the double asterisk syntax, it can take any number of key-value pairs as a list of parameters
# These parameters are designed to correspond to Grade object attributes
def getGrades(**kwargs):

	# Copy accessibleGrades into new dict
	gradeList = dict(accessibleGrades)

	# Check that list of parameters is not empty
	if len(kwargs.keys()) > 0:
	
		# Iterate over list of supplied parameters
		for param in kwargs.keys():
			print(param)

			# Iterate over a copy of gradeList and delete entries if any of their attributes do not equal the supplied parameter values		
			for txid, grade in gradeList.copy().items():
				if getattr(grade, param) != kwargs.get(param):
					del gradeList[txid]
		
		# Return result gradeList with deleted entries			
		print(gradeList)
		return gradeList	
			
	# If list of parameters is empty:
	else:
		print("No arguments given!")
		return None			

# This method serves to "edit" Grade items on the blockchain.
# Since the blockchain is not truly editable, this "editing" is more like "replacing".
# It utilizes the blacklist to mark the transaction being "edited" as no longer valid.
# It also publishes a new item with the changed values to take the place of the blacklisted one.	
# Similarly to the getGrades method, it can take any number of key-value pairs as parameters for the values to change.				
def edit(txid, studentID, **kwargs):
	
	# Check if given TXID is in list of accessible grades
	if str(txid) in accessibleGrades.keys():
	
		# Publish TXID of item being edited to the blacklist stream with student ID as the key
		print("TXID being blacklisted: " + txid)
		api.publish("blacklist", str(studentID), str(txid))
		
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
		txout = addGrade(studentID, newGrade.name, newGrade.score, newGrade.courseID, newGrade.comments, newGrade.date, newGrade.category)
		return txout
	
	# If TXID not found in list of accessible grades:
	else:
		print("Grade not found!")
		return None
			
# Ask user for student and teacher IDs and get corresponding private keys
currentID = input("Enter your ID number. \n")
newStudent = Student(currentID, "Student Example")
currentTeacherID = input("Enter the teacher ID number. \n")
newTeacher = Teacher(currentTeacherID, "Teacher Example") 
privKeyStudentPath = "privKeyStudent.txt"
privKeyTeacherPath = "privKeyTeacher.txt"

# Open and load given student private keys
privKeyStudentFile = open(privKeyStudentPath, "rb")
privKeyStudentPEM = privKeyStudentFile.read()
privKeyStudent = serialization.load_pem_private_key(privKeyStudentPEM, password=None, backend=default_backend())

# Open and load given student private keys
privKeyTeacherFile = open(privKeyTeacherPath, "rb")
privKeyTeacherPEM = privKeyTeacherFile.read()
privKeyTeacher = serialization.load_pem_private_key(privKeyTeacherPEM, password=None, backend=default_backend())

# Add a sample course and some grades
physics = Course("Physics", 1111, 401, {"Homework" : .25, "Quizzes" : .25, "Tests" : .50})
newGradeTX1 = addGrade(currentID, "Homework 1", .95, 401, "Comment 1", datetime.date(2018, 1, 1), "Homework")
newGradeTX2 = addGrade(currentID, "Quiz 1", .86, 401, "Comment 2", datetime.date(2018, 1, 2), "Quizzes")
	
# Create list of blacklisted TXIDs from blockchain
blacklist = []
for item in api.liststreamkeyitems("blacklist", str(currentID)):
	blacklist.append(item.get("data"))
print("Blacklist: " + str(blacklist))

# This next section of code generates a list of all grades that are accessible by the entered student ID.
# By generating this list at startup, interactions become much faster since no data is being read live from the blockchain.
# This list is also convenient for displaying the grades which are actually relevant to the user.
# Finally, it prevents the program from attempting to access any grades belonging to a different user.
accessibleGrades = {}

# List all access points corresponding to the entered ID number
accessPoints = api.liststreamkeyitems("access", str(currentID))
print("Generating grade list...")

# Iterate over list of access points
for accessPoint in accessPoints:
	
	# Get TXID of corresponding item for current access point
	txid = accessPoint.get("keys")[1]
	
	# Check if TXID is in the blacklist
	if str(txid) in blacklist:
		print("Found blacklisted item with txid " + txid)
		
	# If TXID is not in blacklist, add grade to list of accessible grades
	else:
	
		# Decrypt secret passphrase with entered private key
		secret = privKeyStudent.decrypt(binascii.unhexlify(accessPoint.get("data")), padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
		fernet = Fernet(secret)
	
		# Get, decrypt, and deserialize the grade with the TXID listed in the access point
		encryptedGradeHex = api.getstreamitem("items", txid).get("data")
		encryptedGrade = binascii.unhexlify(encryptedGradeHex)
		pickledGrade = fernet.decrypt(encryptedGrade)
		grade = pickle.loads(pickledGrade)
	
		# Add the grade to the list of all accessible grades
		accessibleGrades[str(txid)] = grade

# Edit comments on sample grades
newtxid1 = edit(newGradeTX1, currentID, comments="Good job!")
newtxid2 = edit(newGradeTX2, currentID, comments="Great job!!!")

# Print comments for sample grades (will not update after edit until next run)
gradeResult1 = getGrades(studentID=currentID, name="Homework 1", courseID=401)
gradeResult2 = getGrades(studentID=currentID, name="Quiz 1", courseID=401)
print(gradeResult1.get(list(gradeResult1.keys())[0]).comments)
print(gradeResult2.get(list(gradeResult2.keys())[0]).comments)
