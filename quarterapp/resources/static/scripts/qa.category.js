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

    function Category(invoker, options) {
        this.options = $.extend({}, $.fn.category.defaults, options);
        this.$invoker = $(invoker);
        this.$overlay = $("#modal-overlay");
        this.$modal = $("#category-modal");
        this.category_action = this.$invoker.attr("data-category-action"); 
        this.category_group_markup = '<section class="group activities" data-category-id="{0}"><section class="header"><h3><span class="icon medium category">&nbsp;</span><span class="category-title">{1}</span></h3></section><section class="content"></section><section class="actions"><a class="button positive" href="#" data-activity-action="new" data-category-id="{0}">New activity</a><a class="button" href="#" data-new-category-action data-category-action="edit" data-category-id="{0}">Edit category</a><a class="button negative delete" href="#" data-category-action="delete" data-category-id="{0}">Delete</a></section></section>';
       this.init();
    }

    Category.prototype = {
        constructor : Category,

        init : function() {
            this.$invoker.on("click", $.proxy(this.on_action, this));
        },

        on_action : function(event) {
            var self = this;

            event.preventDefault();

            if(this.category_action === "delete") {
                

                var category_id = this.$invoker.attr("data-category-id");
                this.delete_category(category_id);
                return false;
            }

            if(this.category_action === "edit") {
                $("#category-modal").find("h2").html("Edit category");
                var category_id = this.$invoker.attr("data-category-id");
                this.update_field_values(category_id);
            }
            this.$modal.addClass("show");
            this.$overlay.addClass("show");

            this.$overlay.on("click", $.proxy(this.on_close, this));
            this.$modal.find(".button.close").on("click", $.proxy(this.on_close, this));

            self.$modal.find("form").on("submit", $.proxy(this.on_submit, this));

            return false;
        },

        on_close : function() {         
            this.$modal.removeClass("show");
            this.$overlay.removeClass("show");
            this.$modal.find("form").off("submit");
            this.$overlay.off("click");
            this.$modal.find(".button.close").on("off");
            this.restore_modal();

            return false;
        },

        on_submit : function(event) {
            var self = this,
                title = this.$modal.find("input").val();

            event.preventDefault();

            if(this.category_action === "edit") {
                var category_id = this.$invoker.attr("data-category-id");
                this.update_category(category_id, title);
            }
            else {
                this.create_category(title);
            }

            return false;
        },

        restore_modal : function() {
            var $title = this.$modal.find("input");
            $title.val("");
            $title.removeClass("error");
            $title.siblings("div.input-error").remove();
        },

        update_field_values : function(category_id) {
            var self = this;
            
            if(category_id != undefined) {
                $.ajax({
                    url : "/api/category/" + category_id,
                    success : function(data, status, jqXHR) {
                        $("#category-title").val(data.title);
                        self.$modal.find("form").on("submit", $.proxy(this.on_submit, this));
                        
                    },
                    error : function(jqXHR, status, errorThrown) {
                        $("#category-title").attr("disabled", "disabled");
                        self.$modal.find(".message").addClass("negative").html("Could not retrieve category details!");
                        self.$modal.find("form").attr("disabled", "disabled");
                    }
                });
            }   
        },

        create_category : function(title) {
            var self = this;
            $.ajax({
                url : "/api/category",
                type : "POST",
                data : {
                    "title" : title
                },
                success : function(data, status, jqXHR) {
                    self.add_category_group(data);
                    $("body").trigger("ajax");
                    self.on_close();
                },
                error : function(jqXHR, status, errorThrown) {
                    self.$modal.find(".message").addClass("negative").html("<span class='icon error'>&nbsp;</span>Could not create category!");
                }
            });
        },

        update_category : function(category_id, title) {
            var self = this;
            $.ajax({
                url : "/api/category/" + category_id,
                type : "PUT",
                data : {
                    "title" : title
                },
                success : function(data, status, jqXHR) {
                    var header = self.$invoker.parents(".group.activities").find(".category-title").html(data.title);
                    $("body").trigger("ajax");
                    self.on_close();
                },
                error : function(jqXHR, status, errorThrown) {
                    self.$modal.find(".message").addClass("negative").html("<span class='icon error'>&nbsp;</span>Could not update category!");
                }
            });
        },

        delete_category : function(category_id) {
            var self = this;
            $.ajax({
                url : "/api/category/" + category_id,
                type : "DELETE",
                success : function(data, status, jqXHR) {
                    self.$invoker.parents(".group.activities").remove();
                },
                error : function(jqXHR, status, errorThrown) {
                    quarterapp.log("Could not delete category");
                }
            });
        },

        add_category_group : function(category) {
            var $list = $(".container.main");
            $list.append(this.category_group_markup.format(category.id, category.title));
        }
    };

    // jQuery plugin definition
    $.fn.category = function(options) {
        var useOptions = {};
        if(options !== undefined) {
            useOptions = options;
        }

        return this.each(function() {
            var $this = $(this),
                data = $this.data('category');

            if(!data) {
                $this.data("category", (data = new Category($this, useOptions)));
                useOptions = {}; // Reset since we're in a loop
            }
        });
    };

    // Modal default configuration values
    $.fn.category.defaults = {
    };

    $.fn.category.Constructor = Category;

    // Check additional bindings after ajax
    $("body").on("ajax", function() {
        $("[data-category-action]").category();
    });

    // Automatically bind all existing modal invokers
    $(function() {
        $("[data-category-action]").category();
    }());
})(jQuery);