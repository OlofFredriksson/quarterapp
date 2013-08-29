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
 */
(function($) {
    "use strict";

    var Switcher = function(element, options) {
        this.$element = $(element),
        this.options = $.extend({}, $.fn.palette.defaults, options);
        this.init();
    }

    Switcher.prototype = {
        constructor : Switcher,

        init : function() {
            this.$element.on('click', $.proxy(this.on_switch, this));
        },
        
        on_switch : function() {
            if(this.$element.hasClass("on")) {
                this.$element
                    .removeClass("on")
                    .addClass("off");
            }
            else {
                this.$element
                    .removeClass("off")
                    .addClass("on");
            }
        }
    };

    $.fn.switcher = function(options) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('switcher');
            if(!data) {
                $this.data('switcher', (data = new Switcher(this, options)));
            }
        });
    }

    $.fn.switcher.defaults = {
    };

    $.fn.switcher.Constructor = Switcher;

    // Automatically bind all palette
    $(function() {
        $(".switcher").switcher();
    }());

})(jQuery);
