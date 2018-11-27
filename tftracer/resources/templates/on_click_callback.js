content = "";
let elems = $(".bk-tooltip");
let len = elems.length - 1;
elems.each(function (i) {
    content += $(this).html();
    console.log(content);
    if (len === i) {
        $("#xl-toolbox").html(content);
    }
});
UIkit.modal('#modal-details').show();