$(function() {
    //events---
    //$('#cg0').change(function(e) {
    $('#tablelist tr td select.cg').change(function(e) {
	//alert("foo");
	//alert(e.target.value);
	url = 'categorygroup/' + e.target.value+ '/list/';
	$.ajax(url,
	       {
		   type: 'get',
	       }
	      )
	    .done(function(data) {
		var jsondata = $.parseJSON(data);
		//alert(jsondata.category_list[0]);
		//alert(e.target.value);
		//alert(e.target.parent());
		//alert($(this).value);
		//alert(e.target.name);
		//alert(e.target.name);
		//var t = '#' + e.target.id;
		//alert($('select[name="' + e.target.name + '"]'));
		//$('select[name="' + e.target.name + '"]').siblings().hide();
		//alert($('select[name="' + e.target.name + '"]').name);
		//alert($(t).id);
		//alert($('#' + e.target.id).value);
		//alert($('#' + e.target.id).parent().name);
		//alert($(e.target.name).siblings());
		//alert($(this).siblings().value);
		$('select[name="' + e.target.name + '"]').siblings().children().remove();
		for(var i in jsondata.category_list){
		    $('select[name="' + e.target.name + '"]').siblings().append("<option value='" + jsondata.category_list[i].id + "'>" + jsondata.category_list[i].name + "</option>");
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


