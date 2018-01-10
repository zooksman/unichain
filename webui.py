import web
import jinja2
import os
#import unichain

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)
template_home = jinja_env.get_template('home.html')
template_add = jinja_env.get_template('add.html')


urls = (
  '/', 'home',
  '/home', 'home',
  '/add', 'add'
)

name = ""

class home:
	def GET(self):
		formname = name
		return template_home.render(endname=formname)
		
	def POST(self):
		data = web.input()
		return template_home.render(endname=data.name)
			
class add:
	def GET(self):
 		return template_add.render()			

		
if __name__ == "__main__": 
    app = web.application(urls, globals())
    app.run()