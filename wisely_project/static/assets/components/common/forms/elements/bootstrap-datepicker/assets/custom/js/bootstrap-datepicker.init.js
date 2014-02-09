if (typeof $.fn.bdatepicker == 'undefined')
    $.fn.bdatepicker = $.fn.datepicker.noConflict();

$(function () {

    /* DatePicker */
    // default
    $("#datepicker1").bdatepicker({
        format: 'yyyy-mm-dd',
        startView: 2,
        endDate: '2005-01-01',
    });


    // other
    if ($('#datepicker').length) $("#datepicker").bdatepicker({ showOtherMonths: true });
    if ($('#datepicker-inline').length) $('#datepicker-inline').bdatepicker({ inline: true, showOtherMonths: true });

});