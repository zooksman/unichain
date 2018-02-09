import web
import jinja2
import os
import datetime
from unichain import Grade
from unichain import Course
from unichain import Student
from unichain import Teacher
import unichain
import webbrowser

# Link to Unichain getCourse method
# def getCourse(id):
# 	return unichain.getCourse(id)
# 
# Link to Unichain getCourse method
# def getCourse(name):
# 	return unichain.getCourse(name)

# Given a specifically formatted string, parse it to create a list of categories and weights for a course
def parseCategories(input):

	# Split input into list of tuples
	list = input.split("\n")
	result = {}
	
	# Remove all spaces
	for item in list:
		list[list.index(item)] = item.replace(" ", "")
		
	# Split category name from weight
	for item in list:
		separated = item.split(",")
		
		# Add category name as key and weight as value to result dictionary
		result[separated[0]] = int(separated[1]) / 100
		
	return result

# Given a list of grades, return a list of students involved in them
def listStudents(gradeList):
	studentList = {}
	
	# Iterate over list of grades
	for grade in gradeList.values():
		
		# If student ID hasn't already been added, add it along with student name
		if grade.studentID not in studentList.keys():
			studentList[grade.studentID] = unichain.getStudentName(grade.studentID)
			
	return studentList

# Due to the Jinja2 templating language, it is impossible to pass arguments into functions with double asterisk syntax.
# Therefore, I had to make separate methods with only one parameter for use in the web interface.

# Get a list of grades given student ID
def getStudentGrades(studentID):
	return unichain.getGrades(studentID=studentID)

# Get a list of grades given student ID
def getCourseGrades(courseID):
	return unichain.getGrades(courseID=courseID)

# Get a list of grades given student ID
def getNameGrades(courseID, name):
	return unichain.getGrades(courseID=courseID, name=name)

# Check if inputted string is a number or not by attempting to cast it to a float and catching an exception
def inputIsNumber(input):
	try:
		float(input)
		return True
	except ValueError:
		return False

# Remove duplicate entries from a list of grades, and just preserve the name and course ID in a new list
def noDupeList(gradeList):
	nameList = {}
	for txid, grade in gradeList.items():
		if (grade.name not in nameList.keys()) or (nameList.get(grade.name) != grade.courseID):
			nameList[grade.name] = grade.courseID
	return nameList

# Set up Jinja2 template environment
template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True, extensions=['jinja2.ext.loopcontrols'])

# Jinja2's "filters" allow Python methods to be used inside of HTML documents.
# However, they need to be all declared beforehand, which is what all of these next lines are.
jinja_env.filters['getStudentID'] = unichain.getStudentID
jinja_env.filters['getStudentName'] = unichain.getStudentName
jinja_env.filters['getCourseFromID'] = unichain.getCourseFromID
jinja_env.filters['getCourseFromName'] = unichain.getCourseFromName
jinja_env.filters['getStudentGrades'] = getStudentGrades
jinja_env.filters['getCourseGrades'] = getCourseGrades
jinja_env.filters['getNameGrades'] = getNameGrades
jinja_env.filters['calcGrade'] = unichain.calcGrade
jinja_env.filters['calcAverage'] = unichain.calcAverage
jinja_env.filters['zip'] = zip
jinja_env.filters['str'] = str
jinja_env.filters['round'] = round

# Declare student templates
template_studentHome = jinja_env.get_template('studentHome.html')
template_studentCourse = jinja_env.get_template('studentCourse.html')
template_studentGrade = jinja_env.get_template('studentGrade.html')

# Declare teacher templates
template_teacherHome = jinja_env.get_template('teacherHome.html')
template_teacherEdit = jinja_env.get_template('teacherEdit.html')
template_teacherAdd = jinja_env.get_template('teacherAdd.html')
template_teacherAddCourse = jinja_env.get_template('teacherAddCourse.html')
template_teacherCourse = jinja_env.get_template('teacherCourse.html')
template_teacherGrade = jinja_env.get_template('teacherGrade.html')

# Depending on whether or not the user is a teacher, set the home to teacherHome or studentHome
if unichain.teacher:
	home = "teacherHome"
else:
	home = "studentHome"

# Maps URLs to classes in this file. "(.+)" means that arguments in the URL also get passed to the class.
urls = (
  '/', home,
  '/studentHome', 'studentHome',
  '/studentCourse/(.+)', 'studentCourse',
  '/studentGrade/(.+)', 'studentGrade',
  '/teacherAdd', 'teacherAdd',
  '/teacherCourse/(.+)', 'teacherCourse',
  '/teacherHome', 'teacherHome',
  '/teacherGrade/(.+)', 'teacherGrade',
  '/teacherEdit/(.+)', 'teacherEdit',
  '/teacherAddCourse', 'teacherAddCourse'
)

name = ""

# When a URL is requested via either GET or POST, execution is passed to one of these classes which handle the requests with the appropriately-name GET and POST methods.

# Page that shows information about a specific course (student view)
class studentCourse:
	def GET(self, id):
	
		# Render template with course object and list of grades in course
		gradeList = getCourseGrades(int(id))
		course = unichain.getCourseFromID(id)
		return template_studentCourse.render(gradeList = gradeList, course = course)

# Page that shows information about a specific grade (student view)		
class studentGrade:
	def GET(self, txid):
	
		# Render template with given grade object retrieved from TXID
		grade = unichain.getGrades(txid=txid)
		return template_studentGrade.render(grade=grade)

# Homepage for students
class studentHome:
	def GET(self):
		
		# Render template with current date and list of courses/grades
		date = datetime.datetime.now().date()
		gradeList = unichain.updateAccessible()
		courseList = unichain.accessibleCourses
		name = unichain.getStudentName(unichain.currentID)
		return template_studentHome.render(gradeList = gradeList, courseList = courseList, date = date, name = name)

# Page that shows information about a specific grade (teacher view)				
class teacherGrade:
	def GET(self, txid):
		
		# Render template with specific grade and list of all grades with the same name and course ID
		grade = unichain.getGrades(txid=txid)
		gradeList = unichain.getGrades(name=grade.name, courseID=grade.courseID)
		return template_teacherGrade.render(grade=grade, gradeList=gradeList)	

# Page that shows information about a specific course (teacher view)
class teacherCourse:
	def GET(self, id):
	
		# Render template with full grade list, list of grades without duplicates, course object, and finally list of students involved in those grades
		gradeList = getCourseGrades(int(id))
		nameList = noDupeList(gradeList)			
		course = unichain.getCourseFromID(id)
		studentList = listStudents(gradeList)
		return template_teacherCourse.render(gradeList = gradeList, course = course, studentList = studentList, nameList = nameList)	

# Homepage for teachers
class teacherHome:
	def GET(self):
	
		# Render template with current date, full grade list, list of grades without duplicated, and finally list of courses
		date = datetime.datetime.now().date()
		gradeList = unichain.updateAccessible()
		nameList = noDupeList(gradeList)			
		courseList = unichain.accessibleCourses
		name = unichain.getStudentName(unichain.currentID)
		return template_teacherHome.render(gradeList = gradeList, courseList = courseList, date = date, nameList = nameList, name = name)

# Page for adding a grade (teachers only)				
class teacherAdd:

	# Render add template
	def GET(self):
		return template_teacherAdd.render()
	
	# Add grade based on HTML form input
	def POST(self):
	
		# Initialize data from forms (data is a dictionary where the keys are the form names and the values are inputs)
		data = web.input()	
		error = ""
		
		# Form validation for inputs
		# Add message to error if a problem is found
		
		# Check if student with given name exists
		if data.get("student") == "" or not (unichain.checkStudent(unichain.getStudentID(data.get("student")))):
			error += "Student not found!"
			
		# Check if score is a number and is positive (if a score is given at all)
		# If a score is not given, set it to -1 which signals an assignment that is yet to be graded
		if data.get("score") != "":
			if not inputIsNumber(data.get("score")) or not (float(data.get("score")) > 0):
				error += "\nScore must be a postive number!"
		else:
			data["score"] = -1
	
		# Check if course with that name exists
		if data.get("course") == "" or not (unichain.checkCourse(unichain.getCourseFromName(data.get("course")).courseID)):
			error += "\nCourse not found!"		
			
		# Check if category exists within given course
		if data.get("category") == "" or not (unichain.checkCategory(unichain.getCourseFromName(data.get("course")).courseID, data.get("category"))):
			error += "\nCategory not found in specified course!"
			print("\nCategory not found in specified course!")
		
		# If there are no errors (meaning the error string is empty):
		if error == "":
		
			# Add grade with given inputs and render homepage with updated grade list
			unichain.addGrade(unichain.getStudentID(data.get("student")), data.get("grade"), float(data.get("score")), unichain.getCourseFromName(data.get("course")).courseID, data.get("comments"), datetime.datetime.strptime(data.get("date"), "%Y-%m-%d").date(), data.get("category"))		
			return template_teacherHome.render(gradeList = unichain.updateAccessible(), courseList = unichain.accessibleCourses, date = datetime.datetime.now().date(), nameList = noDupeList(unichain.updateAccessible()))
		
		# If there is an error, render the add page again with the error, but keep the preserved inputs
		else:
			return template_teacherAdd.render(error = error, student = data.get("student"), grade = data.get("grade"), score = data.get("score"), course = data.get("course"), comments = data.get("comments"), date = data.get("date"), category = data.get("category"))

# Page for adding a new course (teachers only)			
class teacherAddCourse:

	# Render add course template
	def GET(self):
		return template_teacherAddCourse.render()
	
	# Add course based on HTML form input	
	def POST(self):
	
		# Initialize data from forms (data is a dictionary where the keys are the form names and the values are inputs)
		data = web.input()
		error = ""
		
		# Form validation for inputs
		# Add message to error if a problem is found
		
		# Check if course with given name already exists
		if data.get("course") == "" or (unichain.checkCourseFromName(data.get("course"))):
			error += "A course with that name already exists!"
			print("A course with that name already exists!")
			
		# Check if teacher with given name exists
		if data.get("teacher") == "" or not (unichain.checkStudent(unichain.getStudentID(data.get("teacher")))):
			error += "Teacher not found!"
			print("Teacher not found!")
		
		# Check if course with given ID number already exists
		if data.get("id") == "" or (unichain.checkCourse(int(data.get("id")))):
			error += "A course with that ID already exists!"
			print("A course with that ID already exists!")
		
		# If there are no errors (meaning the error string is empty):
		if error == "":
		
			# Add course with given inputs and render homepage with updated course list
			newCourse = unichain.Course(data.get("course"), unichain.getStudentID(data.get("teacher")), int(data.get("id")), parseCategories(data.get("categories")))
			return template_teacherHome.render(gradeList = unichain.updateAccessible(), courseList = unichain.accessibleCourses, date = datetime.datetime.now().date(), nameList = noDupeList(unichain.updateAccessible()))
		
		# If there is an error, render the add course page again with the error, but keep the preserved inputs
		else:
			return template_teacherAddCourse.render(error = error, course = data.get("course"), teacher = data.get("teacher"), id = data.get("id"), categories = data.get("categories"))
	
# Page for editing a grade (teachers only)
class teacherEdit:

	# Render edit page with grade object from given TXID so the forms can be pre-filled-out
	def GET(self, txid):
		grade = unichain.getGrades(txid=txid)
		return template_teacherEdit.render(grade=grade, txid=txid)
	
	# Edit grade based on HTML form input	
	def POST(self, txid):
		
		# Initialize data from forms (data is a dictionary where the keys are the form names and the values are inputs)
		data = web.input()
		error = ""
		
		# Form validation for inputs
		# Add message to error if a problem is found
		
		# Check if student with given name exists
		if data.get("student") == "" or not (unichain.checkStudent(unichain.getStudentID(data.get("student")))):
			error += "Student not found!"
			print("Student not found!")
		
		# Check if score is a number and is positive (if a score is given at all)
		# If a score is not given, set it to -1 which signals an assignment that is yet to be graded
		if data.get("score") != "":
			if not inputIsNumber(data.get("score")) or not (float(data.get("score")) > 0):
				error += "\nScore must be a postive number!"
				print("\nScore must be a postive number!")
		else:
			data["score"] = -1
		
		# Check if course with that name exists
		if data.get("course") == "" or not (unichain.checkCourse(unichain.getCourseFromName(data.get("course")).courseID)):
			error += "\nCourse not found!"		
			print("\nCourse not found!")
		
		# Check if category with given name exists within specified course
		if data.get("category") == "" or not (unichain.checkCategory(unichain.getCourseFromName(data.get("course")).courseID, data.get("category"))):
			error += "\nCategory not found in specified course!"
			print("\nCategory not found in specified course!")
			
		# Retrieve grade object for passing into result page
		grade = unichain.getGrades(txid=txid)
		
		# If there are no errors (meaning the error string is empty):
		if error == "":
			
			# Edit grade based on given inputs and render homepage with updated grade list
			studentID = grade.studentID
			unichain.edit(txid, studentID=unichain.getStudentID(data.get("student")), name=data.get("name"), score=float(data.get("score")), courseID=unichain.getCourseFromName(data.get("course")).courseID, comments=data.get("comments"), date=datetime.datetime.strptime(data.get("date"), "%Y-%m-%d").date(), category=data.get("category"))		
			gradeList = unichain.updateAccessible()
			return template_teacherHome.render(nameList = noDupeList(gradeList), gradeList = gradeList, courseList = unichain.accessibleCourses, date = datetime.datetime.now().date())
		
		# If there is an error, render the edit page again with the error, but keep the preserved inputs
		else:
			return template_teacherEdit.render(txid = txid, error = error, student = data.get("student"), name = data.get("name"), score = data.get("score"), course = data.get("course"), comments = data.get("comments"), date = data.get("date"), category = data.get("category"), grade=grade)

# Launches web framework and opens web browser to page
if __name__ == "__main__": 
	app = web.application(urls, globals())
	webbrowser.open("http://localhost:8080")
	app.run()
	
