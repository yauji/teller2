
$(function() {
    //init format---
    $('.day').datepicker({
	format: "yyyy/mm/dd"
    });
    $('.datepicker').datepicker({
	format: "yyyy/mm",
	startView: "months",
	minViewMode: "months"
    });

    //events---
    $('#ccheck').click(function(e) {
	$("#category > input:checkbox").prop("checked", true);
    });

    $('#cuncheck').click(function(e) {
	$("#category > input:checkbox").prop("checked", false);
    });

    

});

