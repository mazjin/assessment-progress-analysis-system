$(document).ready(function(){
	$("[for=id_match_subject_by_name],[for=id_match_datadrop_by_name").hide()
	$("#id_subject_select").on("change",function(){
		$("[for=id_match_subject_by_name]").show();
		};
	$("#id_datadrop_select").on("change",function(){
		$("[for=id_match_datadrop_by_name]").show();
		};
	// $("#contentdiv").addClass("container-fluid");
	$("#containerdiv").removeClass("container").addClass("container-fluid");

	};)
