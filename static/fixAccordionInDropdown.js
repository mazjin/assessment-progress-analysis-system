$(document).ready(function(){
	// Collapse accordion every time dropdown is shown
	$('.dropdown-accordion').on('shown.bs.dropdown', function (event) {
	  var accordion = $(this).find($(this).data('accordion'));
	  accordion.find('.panel-collapse.in').collapse('hide');
	});

	// Prevent dropdown to be closed when we click on an accordion link
	$(".dropdown-accordion").on("click",selector="a[data-toggle='collapse']",function(event){
		event.preventDefault();
		event.stopPropagation();
		$($(this).data('parent')).find('.panel-collapse.in').collapse('hide');
		$($(this).attr('href')).collapse('show');
	});


	//Navbar Box Shadow on Scroll 
	$(function(){
		var navbar = $('.navbar');
		$(window).scroll(function(){
			if($(window).scrollTop() <= 40){
				navbar.css('box-shadow', 'none');
			} else {
			  navbar.css('box-shadow', '0px 10px 20px rgba(0, 0, 0, 0.4)'); 
			}
		});  
	})

	//Offset scrollspy height to highlight li elements at good window height
	$('body').scrollspy({
		offset: 80
	});

	// Close Nav When Link Is Selected
	$('.panel-body a[href^="#section"], a[href^="#section"]').on('click', function(){
		$('.navbar-collapse').collapse('hide');
		$('.dropdown-toggle').click();
	  alert("4 fired");
	});


	//Smooth Scrolling For Internal Page Links
	$(function() {
	  $('.list-group a[href*=#]:not([href=#]), a[href="#toTop"]').click(function() {
		if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
		  var target = $(this.hash);
		  target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
		  if (target.length) {
			$('html,body').animate({
			  scrollTop: target.offset().top
			}, 1000);
			return false;
		  }
		}
	  });
	});
});