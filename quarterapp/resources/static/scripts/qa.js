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
(function() {
    "use strict";

    function Quarterapp() {
    };

    Quarterapp.prototype = {
        constructor : Quarterapp,

        /**
         * Function used to calculate a darker or lighter shade of a color.
         * hex - The base hex color
         * lum - Percentage luminance to alter
         *
         * Inspired from http://www.sitepoint.com/javascript-generate-lighter-darker-color/
         */
        luminance : function(hex, lum) {
            function from_hex(x) {
                return ("0" + parseInt(x).toString(16)).slice(-2);
            }

            try {
                // validate hex string
                hex = String(hex).replace(/[^0-9a-f]/gi, '');
                if (hex.length < 6) {
                    hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2]
                }

                lum = lum || 0;

                // convert to decimal and change luminosity
                var rgb = "#", c, i
                for (i = 0; i < 3; i++) {
                    c = parseInt(hex.substr(i*2,2), 16)
                    c = Math.round(Math.min(Math.max(0, c + (c * lum)), 255)).toString(16);
                    rgb += ("00"+c).substr(c.length);
                }
                return rgb;
            }
            catch(e) {
                return hex;
            }
        },

        /**
         * Return the YYYY-MM-DD representation for the given date object.
         */
        to_date_string : function(date) {
            var month = (date.getMonth() + 1).toString();
            if(month.length === 1) {
                month = "0" + month;
            }

            var day = date.getDate().toString();
            if(day.length === 1) {
                day = "0" + day;
            }
            return "{0}-{1}-{2}".format(date.getFullYear(), month, day);
        },

        /**
         * Log message to console
         */
        log : function(msg) {
            if(console.log !== undefined) {
                console.log(msg);
            }
        },
    };

    window.quarterapp = new Quarterapp();
})();

/*
 * Add a format function to String that formats a string containing
 * {index} with the given values.
 *
 * E.g.
 * "Hello {0}, nice to meet {1}",format("John", "you");
 *
 * will return the string:
 * "Hello John, nice to meet you"
 */
if(String.prototype.format === undefined) {
    String.prototype.format = function() {
        var formatted = this;
        for(var i = 0; i < arguments.length; i++) {
            var regexp = new RegExp('\\{'+i+'\\}', 'gi');
            formatted = formatted.replace(regexp, arguments[i]);
        }
        return formatted;
    };
}

/*
 * Make jquery return hex code on background-color instead of rbg
 * From http://stackoverflow.com/questions/6177454/can-i-force-jquery-cssbackgroundcolor-returns-on-hexadecimal-format
 */
$.cssHooks.backgroundColor = {
    get: function(elem) {
        if (elem.currentStyle)
            var bg = elem.currentStyle["backgroundColor"];
        else if (window.getComputedStyle)
            var bg = document.defaultView.getComputedStyle(elem,
                null).getPropertyValue("background-color");
        if (bg.search("rgb") == -1)
            return bg;
        else {
            bg = bg.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
            function hex(x) {
                return ("0" + parseInt(x).toString(16)).slice(-2);
            }
            return "#" + hex(bg[1]) + hex(bg[2]) + hex(bg[3]);
        }
    }
};