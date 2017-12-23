CG_SYSTEM_ID=101;
C_MOVE_ID=101;


$(function() {
    //init format---
    //$('#user_pay4').css('display', 'none');

    $('.datepicker').datepicker({
	format: "yyyy/mm/dd"
    });

    //events---
    $('#ccheck').click(function(e) {
	$("#category > input:checkbox").prop("checked", true);
    });

    $('#cuncheck').click(function(e) {
	$("#category > input:checkbox").prop("checked", false);
    });

    $('#pmcheck').click(function(e) {
	$("#pmethod > input:checkbox").prop("checked", true);
    });

    $('#pmuncheck').click(function(e) {
	$("#pmethod > input:checkbox").prop("checked", false);
    });


    
    $('#pmg').change(function(e) {
	changeEventPmg(e, '#pm');
    });
    

    $("input[name=tids]").change(function(e) {
	//TODO get sum of selected trnassg
	//alert('hoge');

	var ids = [];
	$("input[name=tids]").each( function () {
	    if($(this).prop("checked")){
		//alert( $(this).val() );
		ids.push($(this).val());
	    }
	});

	//alert(ids);

	url = 'sum_expense';
	$.ajax(url,
	       {
		   type: 'get',
		   data: { ids :ids}
	       }
	      )
	    .done(function(data) {
		var jsondata = $.parseJSON(data);
		//alert(data);
		$("#sum").text(jsondata['sum']);
	    });
    });


    $('#checkall').click(function(e) {
	$("td > input:checkbox").prop("checked", true);
    });

    $('#uncheckall').click(function(e) {
	$("td > input:checkbox").prop("checked", false);
    });

    
    

});

function changeEventPmg(e, targetname){
    //alert(e.target.value);
    url = 'pmgroup/' + e.target.value+ '/list/';
    $.ajax(url,
	   {
	       type: 'get',
	   }
	  )
	.done(function(data) {
	    var jsondata = $.parseJSON(data);
	    //alert(data);
	    selector = targetname + ' option';
	    $(selector).remove();
	    //$('#pm option').remove();
	    for(var i in jsondata.pmethod_list){
		$(targetname).append("<option value='" + jsondata.pmethod_list[i].id + "'>" + jsondata.pmethod_list[i].name + "</option>");
	    }
	});
}    



