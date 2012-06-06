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

// Javascript utility file used by the index page.

// Global variable for the number of times the form iframe is loaded. This is
// used to reload the form in the iframe every other time the iframe is loaded.
var loadCount = 0;


/**
 * Refreshes the form iframe with a new form and makes a call to mark the number
 * as answered. Does this every other load because even numbered loads are when
 * the form has just been submitted. On that we load a new form, which is an odd
 * numbered load.
 */
function formRefresh() {
  loadCount++;
  if (loadCount % 2 == 0) {
    var formKey = $('#bbForm').attr('rel');
    $('#bbForm').html(
        "<iframe src='https://docs.google.com/spreadsheet/" +
        "embeddedform?formkey=" + formKey + "' width='575' height='575' " +
        "frameborder='0' marginheight='0' marginwidth='0' " +
        "onLoad='formRefresh()'>" +
        "Loading...</iframe>");
    updateNumber('answered');
  }
}


/**
 * Updates the status of a phone number in the data store. The number is
 * retrieved from the dom. This makes a call to retrieve a new number.
 * @param {string} result The user selected result of calling the number.
 */
function updateNumber(result) {
  var number = $('#phone-number-text').html();
  $.post('phonenumbers',
      { phone_number: number, contact_response: result },
      function(data) {
        getNewNumber();
  });
}


/**
 * Retrieves a new number from the data store and updates the dom with it.
 */
function getNewNumber() {
  $.get('phonenumbers', {}, function(jsonData) {
    var data = $.parseJSON(jsonData);
    var newNumber = data['phone_number'];
    $('#phone-number').attr('href', 'tel:' + newNumber + '?call');
    $('#phone-number-text').html(newNumber);
  });
}
