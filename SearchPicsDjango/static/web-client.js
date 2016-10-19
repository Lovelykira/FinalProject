 var socket = null;
 var isopen = false;

 window.onload = function() {
       user_id = -1;
       if (document.getElementById('user_id') != null){
       user_id = document.getElementById('user_id').value;
       }

    //url = "ws://127.0.0.1:9000?user_id="+user_id.toString();
    //for vm
    //url = "ws://" + window.location.host + "/ws?user_id="+user_id.toString();

    socket = new WebSocket(url);


    socket.onopen = function() {
       console.log("Connected!");
       isopen = true;
    }

    socket.onmessage = function(e) {
       if (typeof e.data == "string") {

           data = JSON.parse(e.data);
           console.log(data);
           search_phrase = data['search_phrase'].slice(1, -1);

           var search_phrase_normalized = search_phrase;
           if (search_phrase.indexOf(" ")!= -1){
                search_phrase_normalized = search_phrase.replace(" ", ".")
           }
           if ($("."+search_phrase_normalized).length ){
               $( ".progressbar."+search_phrase_normalized ).progressbar();
               $( ".progressbar."+search_phrase_normalized ).progressbar({
                    max:100,
                    value: $( ".progressbar."+search_phrase_normalized ).progressbar( "option", "value" ) + 33
                });

           }
           else{
                if ($("#tasks div.row").length >=10){
                    $('#tasks div:lt(1)').remove();
                }
                var newRow = $("<div />", {class:"row"}).appendTo("#tasks");

                var newTaskCol = $("<div />", {class: "col-md-6 task_name"}).appendTo(newRow)
                var newProgressCol = $("<div />", {class: "col-md-6 task_progress"}).appendTo(newRow)

                if (user_id == -1){
                    user_id = "anonymous"
                }

                var newLink = $("<a />", {
                    name : "link",
                    href : "/search/"+user_id+"/"+search_phrase,
                    text : search_phrase,
                    class : "task",
                    id: data['search_phrase']
                    }).appendTo(newTaskCol);

                var newProgressBar = $("<div />",{class:"progressbar "+search_phrase, style:"height:30px;"}).appendTo(newProgressCol);
                $( ".progressbar."+search_phrase_normalized ).progressbar({
                    max:100,
                    value: 33,
                });


           }
        }
    }

    socket.onclose = function(e) {
       console.log("Connection closed.");
       socket = null;
       isopen = false;
    }

    function post(e){
        $.ajax({type: "POST",
                url: "/",
                data: {"search": $(".search").val()},
                success: function(response) {
                    console.log(response);
                    response = JSON.parse(response);
                    if (response.hasOwnProperty('task_number')){
                        socket.send(response['task_number']);
                        console.log("Sent to server");
                    }
                    else if (response.hasOwnProperty('search_phrase')){
                        if (user_id == -1){
                            user_id = "anonymous"
                        }
                        document.location = '/search/'+user_id+"/"+response['search_phrase'];
                    }
                }
                });
        $(".search").val("");
        }

    $(".go_button").click(post);

    $('.search').keydown(function (e){
        if(e.keyCode == 13){
            post(e);
        }
    });

    var keyword = $("#keyword").val();
    var user_id = $(".user_id").val();

    function normalize_folder_path(input_folder){
        if (input_folder[0] != '/')
            input_folder = '/' + input_folder;
        if (input_folder.slice(-1) != '/')
            input_folder = input_folder + '/';
        return input_folder
    }

    function add_message(input_folder){
        $( "dropdown_row" ).removeClass( "down" );
        var MessageRow = $("<div />", {class:"row"}).prependTo(".main");
        var Message = $("<div />", {class: "alert alert-success", role:"alert", text:"Uploading to "+input_folder+"..."}).appendTo(MessageRow);
    }

    $("#input_folder").keydown(function(event){
        var input_folder = $("#input_folder").val();
        input_folder = normalize_folder_path(input_folder);
        if(event.keyCode == 13){
            $.ajax({type: "GET",
                    url: "/authorize/?keyword="+keyword+"&folder="+input_folder,
                    success: function(data, textStatus) {
                        window.location.href = '/search/'+user_id+'/'+keyword+'/';}
                        });
            add_message(input_folder);
        }});


    $(".yandex_folder").click(function() {
        var input_folder = $(this).text();
        add_message(normalize_folder_path(input_folder));
    });



 };
