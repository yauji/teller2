$(function() {
    //init format---
    $('#user_pay4').css('display', 'none');

    $('.datepicker').datepicker({
	format: "yyyy/mm/dd"
    });

    $('#lmoveto').css('display', 'none');
    $('#pmg2').css('display', 'none');
    $('#pm2').css('display', 'none');
    

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

       if (e.target.value == 101){
           displayMoveTo('inline');
       }else{
           displayMoveTo('none');
       }
    
    });

    $('#c').change(function(e) {
       if (e.target.value == 101){
           displayMoveTo('inline');
       }else{
           displayMoveTo('none');
       }
    });
    


    $('#pmg').change(function(e) {
	url = 'pmgroup/' + e.target.value+ '/list/';
	$.ajax(url,
	       {
		   type: 'get',
	       }
	      )
	    .done(function(data) {
		var jsondata = $.parseJSON(data);
		//alert(data);
		$('#pm option').remove();
		for(var i in jsondata.pmethod_list){
		    $('#pm').append("<option value='" + jsondata.pmethod_list[i].id + "'>" + jsondata.pmethod_list[i].name + "</option>");
		}
	    });
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
