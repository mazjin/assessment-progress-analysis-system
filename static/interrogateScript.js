$(document).ready(function(){

	
	function checkRowColMatchCC(){if($("#id_row_choice").find(":selected").text() == $("#id_col_choice").find(":selected").text()){
		$("#id_row_choice").css("background-color","red");
		$("#id_col_choice").css("background-color","red");
		$(".form-group button").prop("disabled",true);
	}else{
		$("#id_row_choice").css("background-color","white");
		$("#id_col_choice").css("background-color","white");
		$(".form-group button").prop("disabled",false);
		}
	};
	function checkDatadropSet(){
		if( $("#id_row_choice").find(":selected").text()!="Data Drops" &&
			$("#id_col_choice").find(":selected").text()!="Data Drops" &&
			$("#id_datadrop_selected").find(":selected").text()=="---------"){
			
			$("#id_datadrop_selected").css("background-color","orange");
		}
		else{
			$("#id_datadrop_selected").css("background-color","white");
		}
	}
	


	$("#id_row_choice, #id_col_choice").on("change",function(){checkRowColMatchCC();
	checkDatadropSet();});
	
	$("[for=id_match_subject_by_name],[for=id_match_datadrop_by_name").hide();
	$("#id_subject_selected").on("change",function(){
		$("[for=id_match_subject_by_name]").show();
		});
	$("#id_datadrop_selected").on("change",function(){
		$("[for=id_match_datadrop_by_name]").show()
		checkDatadropSet();
		});
	
	checkDatadropSet();
	checkRowColMatchCC();
	});