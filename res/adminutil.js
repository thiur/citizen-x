/**
 * Copyright 2012 Google Inc. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// Javascript utility methods used by the admin page.

/**
 * Sets a new form key in the data store and refreshes the page to reflect the
 * change. This is used by the admin page.
 * @param {string} key The form key to set.
 */
function setFormKey(key) {
  $.post('formmethod', {form_key: key}, function(data) {
    window.location.reload();
  });
}


/**
 * Adds a new user to the whitelist on the data store, and refreshes the page to
 * reflect the change.
 * @param {string} email The email address to add to the whitelist.
 */
function addUser(email) {
  $.post('usermethod', { add_email: email }, function(data) {
    window.location.reload();
  });

}


/**
 * Removes a user from the whitelist on the data store, and refreshes the page
 * to reflect the change.
 * @param {string} email The emmail address to remove from the whitelist.
 */
function deleteUser(email) {
  $.post('usermethod', { delete_email: email }, function(data) {
    window.location.reload();
  });
}
