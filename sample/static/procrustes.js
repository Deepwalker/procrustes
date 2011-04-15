function get_html(elem) {
    return $('<div>').append(elem.clone()).remove().html()
}

$(function(){
    // Add new item for list
    window.widget_num = 10000;
    $(".procrustes__placeholder").each(function (i, d) {
        var id = d.id.split('__')
        id.splice(0, 1)
        id = id.join('__')
        var template_name = "#template__" + id
        var template_widgets = get_html($(template_name))
//        console.log(d, id)
        $("#add__" + id).click(function () {
                var widgets = ('' + template_widgets).replace(/%s/g, window.widget_num)
                window.widget_num += 1
                console.log(window.widget_num)
                console.log(widgets)
                $(d).append(widgets)
        })
    })

    // Delete list item
    $(".form_delete").live('click', function(){
        el = this.parentNode
        console.log(el)
        el.parentNode.removeChild(el)
    })
})
