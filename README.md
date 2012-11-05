#Django Make Admin

Making Django apps is fun, remembering to always ensure my admin.py matches my
models isn't. So this management command does just that.

django-make-admin is a django management command for creating a django admin.py
file for you app.

##Installation:

This is a manage.py executed management script.
Add the file make_admin.py to your chosen management app folder.

*Or with heavy lifting*

	+ root
	|
	|---- app_name
	      |
	      |---- __init__.py
	      |---- views.py
	      |---- models.py
	      |---- management
	      		|
	      		|---- __init__.py
	      		|---- commands
	      			  |---- __init__.py
	      			  |---- make_admin.py


##Usage:

Using your standard method to invoke your django-admin utility management command

	$ python manage.py make_admin app_name

If an admin.py already exists for the application, it will not be overwritten.

###Some extra flags:

To overwrite an existing admin.py app:

	$ python manage.py make_admin app_name -o

To change the name of the target file:

	$ python manage.py make_admin app_name -f foo.py

And that's it!

suggestions and the like:
jay@strangemother.com