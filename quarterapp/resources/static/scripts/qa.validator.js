/*
 *
 * Copyright (c) 2013 Markus Eliasson, http://www.quarterapp.com/
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 *
 *

 Validates a form's input fields either at focus loss or at form submission (default).

 To mark a form for validation, add the attribute "data-validation"
 To add a validator for an input element, add the validation strategy in the input field's
 data-validor attribute (may be a list of space separated strategies).


 <form data-validation>
    <label for="username">Username</label>
    <input type="text" name="username" id="username" 
        data-validator="required email"
        data-validator-on="focus-loss" />
                
    <label for="password">Password</label>
    <input type="password" name="password" id="password"
        data-validator="required password"
        data-validator-on="focus-loss" />
                
    <label for="verify-password">Verify password</label>
    <input type="password" name="verify-password" id="verify-password"
        data-validator="required password mirror"
        data-validator-on="focus-loss"
        data-validator-mirror="password" />
 </form>


    data-validator                  List of validation strategies (space separated)

        required                        Validates that this element contains data

        email                           Validates a simple e-mail address

        password                        Validates a password
                                        Rules are  > 8 chars

        mirror                          Validates this field's value as a mirror. Needs
                                        attribute 'data-validator-mirror'

    data-validator-on               Specifies when validation should occur
        submit (default)                Just before form submission
        focus-loss                      At elements focus loss
    
    data-validator-mirror           Specifies the id of the mirroring field
*/
(function($) {
    "use strict";

    function Validator(form, options, strategies) {
        this.options = $.extend({}, $.fn.validator.defaults, options);
        this.strategies = $.extend({}, $.fn.validator.strategies, strategies);
        this.$form = $(form);
        this.$elements = jQuery();
        this.init();
    }

    Validator.prototype = {
        init : function() {
            var self = this;
            this.$elements = this.$form.find('input[data-validator]');

            this.$form.find('input[data-validator-on="focus-loss"]').each(function(i, e) {
                $(e).blur($.proxy(self.on_blur, self));
            });
            
            this.$form.submit($.proxy(this.on_submit, this));    
        },

        on_blur : function(event) {
            this.validate_element($(event.target));
        },

        on_submit : function(event) {
            var self = this;

            $.each(this.$elements, function(index, element) {
                self.validate_element($(element));
            });

            if(this.$form.find("input." + self.options.error_class).length > 0) {
                this.$form.attr("data-validation-result", "not-valid");
                event.preventDefault();
                return false;
            }
            return true;
        },

        validate_element : function($element) {
            var self = this;
            var strategies = $element.attr("data-validator").split(" ");

            $.each(strategies, function(index, element_strategy) {
                var strategy = self.strategies[element_strategy];
                if(strategy !== undefined) {
                    var message = strategy.check(self, $element);
                    if(message !== undefined) {
                        if(!$element.hasClass(self.options.error_class)) {
                            $element.addClass(self.options.error_class);
                        }
                        if($element.siblings("div.input-error").length == 0) {
                            $element.after('<div class="input-error">' + message + '</div>');
                        }
                        return false; // Break each loop
                    }
                    else {
                        // Remove any previous added markup
                        $element.removeClass(self.options.error_class);
                        $element.siblings("div.input-error").remove();
                    }
                }
            });
        }
    };

    $.fn.validator = function(options, strategies) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data("validator"),
                opts = $.extend({}, options),
                stgs = $.extend({}, strategies);

            if(!data) {
                $this.data("validator", (data = new Validator($this, opts, stgs)));
            }
        });
    };

    /* The default options */
    $.fn.validator.defaults = {
        /* The CSS class added to the input fields and form element at validation error */
        error_class : "error"
    };

    /* The supported types of strategies */
    $.fn.validator.strategies = {
        /* Validates that a required field has a value*/
        "required" : {
            check : function(self, $element) {
                var type = $element.attr("type"),
                    valid = false;
                if(type === "checkbox") {
                    valid = $element.attr("checked");
                } 
                else if(type === "text" || type === "password") {
                    valid = $element.val().length > 0;
                }
                return valid ? undefined : "This field is required";
            }
        },

        /* Very simple e-mail validation. */
        "email"    : {
            check : function(self, $element) {
                var type = $element.attr("type"),
                    valid = false;

                if(type === "text") {
                    valid = /\S+@\S+\.\S+/.test($element.val());
                }
                return valid ? undefined : "This is not a valid email adress";
            }
        },

        /* Verify password */
        "password" : {
            check : function(self, $element) {
                var type = $element.attr("type"),
                    valid = false;
                if(type === "password") {
                    /* one digit, one lowercase, one upper case, and >5 in length */
                    var text = $element.val();

                    valid = text.length > 7;
                    if(!valid) {
                        return "Password needs to be more than 7 characters";
                    }
                }
                return undefined; // Should really be an error
            }
        },

        /* Verity this field's value mirrors another field  */
        "mirror" : {
            check : function(self, $element) {
                var mirror = $element.attr("data-validator-mirror");
                if(mirror !== undefined) {
                    var $mirror = self.$form.find("#" + mirror); 
                    if($element.val() !== $mirror.val()) {
                        return "Not matching";
                    }
                }
                return undefined; // Should really be an error
            }
        },

        /* Verify this field's value is a hex color code, three or six digits, possibly starting with a hash (#) */
        "color-hex" : {
            check : function(self, $element) {
                var type = $element.attr("type"),
                    valid = false;
                if(type === "text") {
                    var text = $element.val();

                    valid = /^(#)?([0-9a-fA-F]{3})([0-9a-fA-F]{3})?$/.test(text);
                    if(!valid) {
                        return "Must be a hex color code (e.g. #ffbbcc)";
                    }
                }
                return undefined;
            }
        }
    };

    $.fn.validator.Constructor = Validator;

    /* Automatically wire the validator plugin for all forms marked for validation */
    $(function() {
        $("form[data-validation]").validator();
    });
})(jQuery);
