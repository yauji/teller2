CG_SYSTEM_ID=101;
C_MOVE_ID=101;

$(function() {
    $('.datepicker').datepicker({
	format: "yyyy/mm/dd"
    });

    //events---
    $('#cg').change(function(e) {
	url = 'categorygroup/' + e.target.value+ '/list/';
	$.ajax(url,
	       {
		   type: 'get',
		   //data: { query: $('#keyword').val() },
		   //dataType: 'xml'
	       }
	      )
	    .done(function(data) {
		var jsondata = $.parseJSON(data);
		$('#c option').remove();
		for(var i in jsondata.category_list){
		    $('#c').append("<option value='" + jsondata.category_list[i].id + "'>" + jsondata.category_list[i].name + "</option>");
		}
	    });
    });
    
    $('#pmg').change(function(e) {
	changeEventPmg(e, '#pm');
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


