from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from django.core import management

try:
    from termcolor import colored
except: pass

import threading, sys, time
from django.db import models
import os
import os.path
from django.db.models import loading
from optparse import OptionParser

class Command(BaseCommand):
    args = 'app_name'
    help = "Automatically generate admin.py based upon your app.models"

    option_list = BaseCommand.option_list + (
        make_option("-o", "--overwrite",
            action='store_true', dest='overwrite', default=False,
            help="Overwrite the admin.py file if it already exists."),
        make_option("-f", "--filename",
            action='store', dest='filename', default='admin.py',
            metavar='FILE',
            help="Name of the file to write to. Default is 'admin.py'"),
        )


    def handle(self, *args, **options):
        self.app_labels = []

        self.overwrite = options.get('overwrite')
        self.verbose = options.get('verbose')
        self.filename = options.get('filename')

        for a in args:

            module, app = self.app_label_to_app_module(a)
            if len(self.get_models(app)) <= 0:
                self.say("No models found.")
                exit(0)

            app, file = self.make_admin(a)
            self.write_lines(app, file)
            self.app_labels.append(a)
            file.close()



    def get_app_label(self,app):
        """ Returns the _internal_ app label for the given app module.
        i.e. for <module django.contrib.auth.models> will return 'auth' """
        return app.__name__.split('.')[-2]

    def file_head(self, file_name, lines=1):
        ''' Print the file head'''
        with open(file_name) as myfile:
            head=[myfile.next() for x in xrange(lines)]
        print head

    def app_label_to_app_module(self, app_label):
        """  Given the app label, returns the module of the app itself
        (unlike models.get_app, which returns the models module) """
        # Get the models module
        app = models.get_app(app_label)
        module_name = ".".join(app.__name__.split(".")[:-1])
        try:
            module = sys.modules[module_name]
        except KeyError:
            __import__(module_name, {}, {}, [''])
            module = sys.modules[module_name]
        return module, app

    def is_admin(self):
        '''Check if the user is an administrator'''
        if hasattr(os, 'getuid'):
            if os.getuid() == 0:
                self.say(os.getuid(), "r00tness!")
                return True
            else:
                self.say(os.getuid(), "I cannot run as a mortal. Sorry.")
                return False
        return None

    def get_models(self, app):
        r =  loading.get_models(app)
        return r

    def make_admin(self, app_label):
        ''' Make an admin file targeting app_label'''
        module, app = self.app_label_to_app_module(app_label)

        path = os.path.abspath(app.__file__)
        loc = path.split(os.path.sep)[:-1]
        loc = os.path.sep.join(loc)

        p = "%s%s%s" % (loc, os.path.sep, self.filename)

        if os.path.isfile(p) is not True:
            # If this file is missing, we create a new one
            file = open(p, 'w')
        else:
            # It does exist.
            if self.overwrite: # overwrite allowed? Bool
                self.say('Overwrite %s' % p)
                file = open(p, 'w')
            else:
                self.say('%s file already exists' % p)
                exit(0)

        return app, file

    def write_fields(self, model, inert=False):
        """
        Write the list display tuple to the file
        list_filter = ('camera', 'zone_id', 'a_name', 'b_name')
        """
        return self._write_list('fields', model, inert)

    def write_list_display(self, model, inert=False):
        """
        Write the list display tuple to the file
        list_filter = ('camera', 'zone_id', 'a_name', 'b_name')
        """
        return self._write_list('list_display', model, inert)

    def write_search_fields(self, model, inert=False):
        """
        Write the search_fields tuple to the file
        search_fields = ('id', 'user', 'session', 'name', 'datetime', )
        """
        return self._write_list('search_fields', model, inert)

    def write_list_filter(self, model, inert=False):
        """
        Write the search_fields tuple to the file
        list_display = ('id', 'user', 'session', 'name', 'datetime', )
        """
        return self._write_list('list_filter', model, inert)

    def filter_horizontal(self, model, inert=False):
        includes = ('ManyToManyField')

        _s = "    filter_horizontal = ("
        for f in self.fields(model):
            if f.get_internal_type() in includes:
                _s += "'%s', " % f.name
        _s += ")\n"

        return _s

    def _write_list(self, label, model, inert=False):
        exclude = ['id']
        c = ''
        _s = ""
        _t = ''
        _i = ''
        if inert:
            _i = '#'
        for f in self.fields(model):
            if f.name in exclude:
                pass
            else:
                _t += "'%s', " % (f.name)
        _s += "    %s%s = (%s)\n" % (_i, label, _t)

        return _s

    def write_admin_classes(self,app):
        models = self.get_models(app)

        #print colored("Models %s" % models, 'red')
        s = ""
        c = ''
        _s =''
        s = s[:-2]
        for m in models:
            _s += "class %sAdmin(admin.ModelAdmin):\n" % (m.__name__)
            _t = ''
            _s += self.write_list_display(m)
            _s += self.write_list_filter(m)
            _s += self.write_search_fields(m)
            _s += self.write_fields(m, inert=True)
            _s += self.filter_horizontal(m)
            _s += "    #exclude = (,)\n\n"

        s += _s
        s += '\n\n'
        return s

    def write_registers(self, app):
        models = self.get_models(app)
        _s = ''
        for m in models:
            _s += "admin.site.register(%(name)s, %(name)sAdmin)\n" % {'name' :m.__name__}

        _s += '\n'
        return _s

    def fields(self, model):
        return model._meta.fields

    def import_models_string(self, app):
        '''
        Return a string for importing all the models within the
        models
        '''
        models = self.get_models(app)

        s = "from django.contrib import admin\n"
        s += "from models import "
        c = ''
        for m in models:
            _s = "%s, " % (m.__name__)
            s = "%s%s" %(s, _s)
            c = ', '

        if s[-2:] == c:
            s = s[:-2]
        return s


    def write_lines(self, app, file):
        lines = [self.import_models_string(app) + '\n\n',
                 self.write_admin_classes(app),
                 self.write_registers(app),
                 ]

        for line in lines:
            file.write(line)

    def say(self, *args):
            s = ''
            c= ''
            for x in args:
                s += "%s%s" % (c, x)
                c = ', '

            v = self.verbose

            if v >= 1 or v is None:
                print(s)
            else:
                print "I'm being quiet"

    def ask(self, q):
        inp = raw_input(q)

        if inp in ['yes', 'ye', 'y' ]:
            return True
        elif inp in ['no', 'n']:
            return False
        else:
            print "Input not correct, answer Y/N"
            self.ask(q)
