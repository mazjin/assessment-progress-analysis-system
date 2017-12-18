$(document).ready(function(){


	function checkRowColMatchCC(){
		var rowColSame=($("#id_row_choice").find(":selected").text() ==
	 	$("#id_col_choice").find(":selected").text())
		var rowStudents=($("#id_row_choice").find(":selected").text()
			.indexOf("Student")>-1)
		var colStudents=($("#id_col_choice").find(":selected").text()
			.indexOf("Student")>-1)
		if(rowColSame||(rowStudents&&colStudents)){
			$("#id_row_choice").addClass("disabled-exclusive");
			$("#id_col_choice").addClass("disabled-exclusive");
			$('#rowcolalert').show();
			$(".form-group button").prop("disabled",true);
		}
		else{
		$("#id_row_choice").removeClass("disabled-exclusive");
		$("#id_col_choice").removeClass("disabled-exclusive");
		$('#rowcolalert').hide();
		$(".form-group button").prop("disabled",false);
	}
	};


	function checkCalcType(){
		var measureChoiceValue=$('#id_val_choice').find(':selected').text()
		var isAvg=(measureChoiceValue.indexOf('(Avg)')>-1)
		var isScore=(measureChoiceValue=="Progress (Avg)")||
			(measureChoiceValue=="Attainment +=- (Avg)")
		$('label[for="id_only_exceeding"]').toggle(!isAvg)
		$('#id_student_residual').attr('checked',false)
		$('#id_only_exceeding').attr('checked',false)
		$('label[for="id_student_residual"]').toggle(isAvg)
		$('label[for="id_grade_filter"]').toggle(isScore)
	}

	function toggleGap(){
		var calc_gap=$('#id_calc_gap').is(':checked')
		$('#id_gap_type').toggle(calc_gap)
		$('label[for="id_gap_type"]').toggle(calc_gap)
		$('#id_gap_type:hidden').val("")
	};

	function toggleIgnoreYeargroup(){
		var subChoiceNotEmpty=($('#id_subject_selected').find(":selected").val()!="")
		var ddChoiceNotEmpty=($('#id_datadrop_selected').find(":selected").val()!="")

		$('label[for="id_match_subject_by_name"]').toggle(subChoiceNotEmpty)
		$('label[for="id_match_datadrop_by_name"]').toggle(ddChoiceNotEmpty)
	}

	function disableCheckboxGrps(){
		var checkedID = $('.calc-filter:checked').attr("id")
		if (!checkedID){
			$('.calc-filter').prop('disabled',false);
		}
		else{
			checkedID="#".concat(checkedID)
			$('.calc-filter ').prop('disabled',true);
			$(checkedID).prop('disabled',false)
			if($(checkedID).hasClass('diff-toggle')){
				$('.diff-toggle').prop('disabled',false)
			}

		}
		$('.calc-filter').parent().removeClass('checkbox-exclusive');

		$('.calc-filter:disabled').parent().addClass('checkbox-exclusive');


	}

	$("#id_calc_gap").on("change",function(){
		toggleGap();
	});

	$("#id_row_choice, #id_col_choice").on("change",function(){
		checkRowColMatchCC();
	});

	$("#id_val_choice").on("change",function(){
		checkCalcType();
	});
	$('#id_student_residual,#id_residual_toggle_col,#id_residual_toggle_row,#id_grade_filter').addClass('calc-filter');
	$('#id_residual_toggle_col,#id_residual_toggle_row').addClass('diff-toggle');
	$('.calc-filter').on('change',function(){

		disableCheckboxGrps();
	});


	$("#id_subject_selected,#id_datadrop_selected").on("change",function(){
		toggleIgnoreYeargroup();
		});

	disableCheckboxGrps();
	toggleIgnoreYeargroup();
	checkRowColMatchCC();
	checkCalcType();
	toggleGap();
	});
