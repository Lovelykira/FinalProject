 var socket = null;
 var isopen = false;

 window.onload = function() {
       user_id = -1;
       if (document.getElementById('user_id') != null){
       user_id = document.getElementById('user_id').value;
       }

//    socket = new WebSocket("ws://127.0.0.1:9000/?user_id="+user_id.toString());
     socket = new WebSocket("ws://" + window.location.host + "/ws?user_id="+user_id.toString());


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
    })

 };
