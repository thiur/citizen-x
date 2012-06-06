#Copyright 2012 Google Inc. All Rights Reserved.
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0

#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.

"""An App Engine site for making calls from a list of phone numbers.

This module handles the data scheme, authentication details, and RPC methods
that control interaction with the frontend.
It was originally built to manage a public opinion poll in Somalia.

    Main(): Renders the home page.
    Admin(): Renders the admin page.
    RPCHandler(): Unpacks incoming requests and throws to RPCMethods.
    RPCMethods(): Processes most incoming requests to the datastore.
"""

import csv
import datetime
import os
from django.utils import simplejson as json
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class UserModel(db.Model):
  """Model for users whitelisted to use the site.

  Note: this is not the same as the list of admins on the site,
  which is set in the App Engine instance's control panel.

  Attributes:
    user: user property, storing name and email of whitelisted user.
  """

  user = db.UserProperty()


class CallRecipient(db.Model):
  """Model for the recipients of the poll.

  Attributes:
    caller: user who made the call.
    phone_number: int of number to call.
    contacted: boolean, defaults to false.
    last_contact: if contacted, the date and time.
    contact_response: string of contact response (e.g. no answer).
  """

  caller = db.UserProperty()
  contact_response = db.StringProperty()
  contacted = db.BooleanProperty(default=False)
  last_contact = db.DateTimeProperty()
  phone_number = db.IntegerProperty()

class Form(db.Model):
  """Model containing single key for the survey form.

  This application uses a form to collect responses.
  This model stores the URI key for that form.
  There should be only one key stored at a time for this app.

  Attributes:
    form_key: string of key.
  """

  form_key = db.StringProperty()


def GetForm():
  """Method for getting current survey form's key.

  Args:
    (none).

  Returns:
    A string of the form's unique key.
  """

  form = db.GqlQuery("SELECT * FROM Form").get()
  if form:
    return form.form_key
  return None


class Admin(webapp.RequestHandler):
  """Renders /admin, where survey key and users are added.

  No log-in logic is necessary: only admins are authorized,
  which is managed through app.yaml.

    Get: Retrieves all current users, and current form.
  """

  def get(self):
    """Renders whitelisted users and survey key on /admin.

    Args:
      (none).

    Returns:
      (none, renders admin page template).
    """

    if users.is_current_user_admin():
      current_users = UserModel.all()
      users_email = [user_model.user.email() for user_model in current_users]

      form_key = GetForm()

      template_values = {"current_users_email": users_email,
                         "form_key": form_key,
                         "logout_url": users.create_logout_url("/")}
      template_page = "admin.html"

    else:
      self.error(403)
      template_values = {"message": "Sorry! The user isn't authorized."}
      template_page = "error.html"

    path = os.path.join(os.path.dirname(__file__), template_page)
    self.response.out.write(template.render(path, template_values))

  def post(self):
    """Receives .csv of phone numbers, stores in CallRecipients.

    Will ignore any numbers already in database.

    Args:
      csv: a csv file with 1 column, and n rows of phone numbers.

    Returns:
      Redirect to admin page.
    """
    if users.is_current_user_admin():
      csv_object = csv.reader(self.request.get("phone-number-csv").split())

      for row in csv_object:
        q = "SELECT * FROM CallRecipient WHERE phone_number = %d" % int(row[0])
        if db.GqlQuery(q).get() is None:
          call_recipient = CallRecipient(phone_number=int(row[0]))
          call_recipient.put()

      self.redirect("/admin")

    else:
      self.error(403)
      template_values = {"message": "Sorry! The user isn't authorized."}
      template_page = "error.html"

      path = os.path.join(os.path.dirname(__file__), template_page)
      self.response.out.write(template.render(path, template_values))

class MainHandler(webapp.RequestHandler):
  """Handles user login and renders home page.

  User ID is handled through App Engine's users() class.
  After users are ID, their emails are checked against the
  UserModel data store. If they are authorized, home page is
  loaded. Else redirect to an error page.
  """

  def get(self):
    """Checks if user is authorized, renders homepage or error page.

    Args:
      (none).

    Returns:
      (none, renders home page template).
    """

    user_email = users.get_current_user().email()
    logout_url = users.create_logout_url("/")
    template_values = {"logout_url": logout_url}

    if self.IsAllowedUser(user_email):
      form_key = GetForm()
      template_values["form_key"] = form_key
      template_page = "index.html"
    else:
      self.error(401)
      template_values["message"] = "Sorry! The user isn't authorized."
      template_page = "error.html"

    path = os.path.join(os.path.dirname(__file__), template_page)
    self.response.out.write(template.render(path, template_values))

  def IsAllowedUser(self, email):
    """Takes email as string, checks if whitelisted user.

    Args:
      email: (string).

    Returns:
      boolean.
    """

    query = "SELECT * FROM UserModel WHERE user = USER('%s')" % email
    allowed_users = db.GqlQuery(query).get()
    if allowed_users:
      return True
    else:
      return False


class PhoneNumbers(webapp.RequestHandler):
  """Fetches an uncalled phone number and records responses.

  Attributes:
    get: fetches current uncalled phone number.
    post: sets the call response for a given number.
  """

  def get(self):
    """Fetches an uncalled phone number.

    Args:
      (none).

    Returns:
      phone_number: json encoded phone number {'phone_number':''}
    """

    q = "SELECT * FROM CallRecipient WHERE contacted = False AND " \
        "caller IN (NULL, USER('%s'))" % users.get_current_user().email()

    phone_number_obj = db.GqlQuery(q).get()
    if phone_number_obj:
      phone_number = phone_number_obj.phone_number
      phone_number_obj.caller = users.get_current_user()
      phone_number_obj.put()
      self.response.out.write(json.dumps({"phone_number": phone_number}))
    else:
      return json.dumps("no number")

  def post(self):
    """Given a phone number and string, store string as call response.

    We assume phone numbers are unique in the datastore.

    Args:
      phone_number: int of call recipient's number.
      contact_response: string.

    Returns:
      (none).
    """

    try:
      phone_number = self.request.get("phone_number")
      contact_response = self.request.get("contact_response")
    except:
      self.response.out.write("problem loading params")
      self.error(400)

    self.response.out.write(str(phone_number) + " marked " + contact_response)
    query = "SELECT * FROM CallRecipient WHERE phone_number = %s" % phone_number
    recipient = db.GqlQuery(query).get()
    if recipient:
      recipient.contact_response = contact_response
      recipient.last_contact = datetime.datetime.now()
      recipient.contacted = True
      recipient.put()
    else:
      self.response.out.write("problem putting in data")
      self.error(400)


class UserMethod(webapp.RequestHandler):
  """Adds and deletes whitelisted application users.

  Atrributes:
    get: fetches list of current.
    post: adds and deletes users
  """

  def post(self):
    """Adds or deletes new whitelisted user by their email.

    Args:
      add_email: user's email to add to whitelist (string).
      delete_email: user's email to delete from whitelist (string).

    Returns:
      (none)
    """

    add_email = self.request.get("add_email")
    delete_email = self.request.get("delete_email")

    if users.is_current_user_admin():
      if add_email:
        new_user_obj = UserModel()
        new_user_obj.user = users.User(email=add_email)
        new_user_obj.put()
      if delete_email:
        query = "SELECT * FROM UserModel WHERE user = USER('%s')" % delete_email
        delete_user = db.GqlQuery(query).get()
        if delete_user:
          delete_user.delete()
    self.redirect("/admin")


class FormMethod(webapp.RequestHandler):
  """Gets and sets current survey form key.

  Survey responses are recorded through a form.
  The form is identified through a unique key.
  This gets and sets the current form.
  """

  def get(self):
    """Gets the unique key for the survey form.

    Args:
      (none).

    Returns:
      form_key: the form key (string).
    """

    form = db.GqlQuery("SELECT * FROM Form").get()
    if form:
      return form.form_key
    else:
      self.reply_error(400)

  def post(self):
    """Given a string, sets the unique key for the input form.

    Args:
      form_key: (string).

    Returns:
      form_key: (string).

    replace the existing form, or add one if none exists.
    """

    form_key = self.request.get("form_key")
    if users.is_current_user_admin():
      query = "SELECT * FROM Form"
      form = db.GqlQuery(query).get()
      if form:
        form.form_key = form_key
        datastore_key = form.put()
      else:
        form = Form()
        form.form_key = form_key
        datastore_key = form.put()
      self.response.out.write("set %s as key" % datastore_key)
    else:
      self.error(403)
    self.redirect("/admin")


def main():
  application = webapp.WSGIApplication(
      [("/", MainHandler),
       ("/admin", Admin),
       ("/formmethod", FormMethod),
       ("/usermethod", UserMethod),
       ("/phonenumbers", PhoneNumbers),
      ], debug=True)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
