$(function () {

    function update_form_data(res)
    {
        $("#product_id").val(res.id);
        $("#product_name").val(res.name);
        $("#product_category").val(res.category);
		$("#product_price").val(res.price);
		$("#product_color").val(res.color);
		$("#product_count").val(res.count);
		$("#product_description").val(res.description);
    }

    function clear_form_data() {
		$("#product_name").val("");
        $("#product_category").val("");
		$("#product_price").val("");
		$("#product_color").val("");
		$("#product_count").val("");
		$("#product_description").val("");
        
    }

    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    $("#create-btn").click(function () {

        var name = $("#product_name").val();
        var category = $("#product_category").val();
		var price = $("#product_price").val();
		var color = $("#product_color").val();
		var count = $("#product_count").val();
		var description =$("#product_description").val();

        var data = {
            "name": name,
            "category": category,
            "color": color,
			"price": price,
			"count": count,
			"description": description
			
        };

        var ajax = $.ajax({
            type: "POST",
            url: "/products",
            contentType:"application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Great Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });
    });


    $("#update-btn").click(function () {

        var product_id = $("#product_id").val();
        var name = $("#product_name").val();
        var category = $("#product_category").val();
        var price = $("#product_price").val();
		var color = $("#product_color").val();
		var count = $("#product_count").val();
		var description =$("#product_description").val();

        var data = {
            "name": name,
            "category": category,
            "color": color,
			"price": price,
			"count": count,
			"description": description
        };

        var ajax = $.ajax({
                type: "PUT",
                url: "/products/" + product_id,
                contentType:"application/json",
                data: JSON.stringify(data)
            })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Great Success")
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.message)
        });

    });

    $("#retrieve-btn").click(function () {

        var product_id = $("#product_id").val();
        var count = $("#product_count").val();
        var ajax = $.ajax({
            type: "GET",
            url: "/products/" + product_id,
            contentType:"application/json",
            data: ''
        })

        ajax.done(function(res){
            update_form_data(res)
            flash_message("Great Success,let's have fun")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    $("#add-unit-btn").click(function () 
    {

        var product_id = $("#product_id").val();

        var ajax = $.ajax({
            type: "PUT",
            url: "/products/" + product_id + "/add_unit",
            contentType:"application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Great Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    $("#sell-unit-btn").click(function () 
    {

        var product_id = $("#product_id").val();

        var ajax = $.ajax({
            type: "PUT",
            url: "/products/" + product_id + "/sell_products",
            contentType:"application/json",
            data: ''
        })

        ajax.done(function(res){
            //alert(res.toSource())
            update_form_data(res)
            flash_message("Great Success")
        });

        ajax.fail(function(res){
            clear_form_data()
            flash_message(res.responseJSON.message)
        });

    });

    $("#delete-btn").click(function () {

        var product_id = $("#product_id").val();

        var ajax = $.ajax({
            type: "DELETE",
            url: "/products/" + product_id,
            contentType:"application/json",
            data: '',
        })

        ajax.done(function(res){
            clear_form_data()
            flash_message("Product has been deleted!")
        });

        ajax.fail(function(res){
            flash_message("Server error!")
        });
    });

    $("#clear-btn").click(function () {
        $("#product_id").val("");
        clear_form_data()
    });
	
	$("#sell-btn").click(function () 
    {
		$("#delete-btn").show();
		$("#product_count").prop('disabled', false);
		$("#purchase_count").hide();
		$("#create-btn").show();
		$("#update-btn").show();
		$("#add-unit-btn").show();
		$("#sell-unit-btn").hide();
		$("#search_results").hide();
	});
	
	$("#buy-btn").click(function () 
    {
		$("#delete-btn").hide();
		$("#product_count").prop('disabled', true);
		$("#purchase_count").show();
		$("#purchase_count2").val("1");
		$("#create-btn").hide();
		$("#update-btn").hide();
		$("#add-unit-btn").hide();
		$("#sell-unit-btn").show();
		$("#search_results").hide();
	});

    $("#search-btn").click(function () 
    {
		$("#search_results").show();
        var name = $("#product_name").val();
        var category = $("#product_category").val();
        var price = $("#product_price").val();
		var color = $("#product_color").val();
		var count = $("#product_count").val();
		var description =$("#product_description").val();

        var queryString = ""

        if (name) {
            queryString += 'name=' + name
        }
        if (category) {
            if (queryString.length > 0) {
                queryString += '&category=' + category
            } else {
                queryString += 'category=' + category
            }
        }

        var ajax = $.ajax({
            type: "GET",
            url: "/products?" + queryString,
            contentType:"application/json",
            data: ''
        })

        ajax.done(function(res)
        {
            $("#search_results").empty();
            $("#search_results").append('<table class="table-striped">');
            var header = '<tr>'
            header += '<th style="width:10%">ID</th>'
            header += '<th style="width:20%">Name</th>'
            header += '<th style="width:10%">Category</th>'
			header += '<th style="width:10%">Color</th>'
			header += '<th style="width:10%">Price</th>'
			header += '<th style="width:20%">Count</th>'
            header += '<th style="width:20%">Description</th></tr>'
            $("#search_results").append(header);
            for(var i = 0; i < res.length; i++) {
                product = res[i];
                var row = "<tr><td>"+product.id+"</td><td>"+product.name+"</td><td>"+product.category+"</td><td>"+product.color+"</td><td>"+product.price+"</td><td>"+product.count+"</td><td>"+product.description+"</td></tr>";
                $("#search_results").append(row);
            }

            $("#search_results").append('</table>');

            flash_message("Great Success")
        });

        ajax.fail(function(res)
        {
            flash_message(res.responseJSON.message)
        });

    });

})
