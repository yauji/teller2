CG_SYSTEM_ID=101;
C_MOVE_ID=101;

$(function() {
    //init format---
    $('#user_pay4').css('display', 'none');

    displayMoveTo('none');

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

       if (e.target.value == CG_SYSTEM_ID){
           displayMoveTo('inline');
       }else{
           displayMoveTo('none');
       }
    
    });

    $('#c').change(function(e) {
       if (e.target.value == C_MOVE_ID){
           displayMoveTo('inline');
       }else{
           displayMoveTo('none');
       }
    });
    


    $('#pmg2').change(function(e) {
	changeEventPmg(e, '#pm2');
    });

    $('#share_type').change(function(e) {
	//3 is pay4other
	if( e.target.value == 3 ){
	    //alert('pay for');
	    $('#user_pay4').css('display', 'inline');
	}else{
	    $('#user_pay4').css('display', 'none');
	}
    });
    });

function displayMoveTo(value){
    $('#lmoveto').css('display', value);
    $('#pmg2').css('display', value);
    $('#pm2').css('display', value);
}

