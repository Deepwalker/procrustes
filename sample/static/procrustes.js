function get_html(elem) {
    return $('<div>').append(elem.clone()).remove().html();
}

$(function(){
    "use strict";

    // Add new item for list
    window.widget_num = 10000;
    $(".procrustes__placeholder").each(function (i, d) {
        var id = d.id.split('__'),
            template_name = '',
            template_widgets = '';

        id.splice(0, 1);
        id = id.join('__');

        template_name = "#template__" + id;
        template_widgets = get_html($(template_name));

        $("#add__" + id).click(function () {
                var widgets = (template_widgets.toString()).replace(/%s/g, window.widget_num);
                window.widget_num += 1;
                $(d).append(widgets);
        });
    });

    // Delete list item
    $(".form_delete").live('click', function(){
        var el = this.parentNode;
        el.parentNode.removeChild(el);
    });
});
