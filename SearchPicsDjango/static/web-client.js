 var socket = null;
 var isopen = false;

 window.onload = function() {
        user_id = -1;
       if (document.getElementById('user_id') != null){
       user_id = document.getElementById('user_id').value;
       }

    socket = new WebSocket("ws://127.0.0.1:9000?user_id="+user_id.toString());

    socket.onopen = function() {
       console.log("Connected!");
       isopen = true;
      // user_id = -1;
      // if (document.getElementById('user_id') != null){
      // user_id = document.getElementById('user_id').value;
      // }
      // socket.send(user_id);
    }

    socket.onmessage = function(e) {
       if (typeof e.data == "string") {
          data = JSON.parse(e.data);
          console.log(data);
          search_phrase = data['search_phrase'].slice(1, -1);
          //data = e.data.slice(1, -1);

       var search_phrase_normalized = search_phrase;
       if (search_phrase.indexOf(" ")!= -1){
            search_phrase_normalized = search_phrase.replace(" ", ".")
       }
       if ($("."+search_phrase_normalized).length){
           $( ".progressbar."+search_phrase_normalized ).progressbar({
                max:100,
                value: 100*data['num_spiders']/3,
            });

       }
       else{
            var newRow = $("<div />", {class:"row"}).appendTo("#tasks");

            var newTaskCol = $("<div />", {class: "col-md-6 task_name"}).appendTo(newRow)
            var newProgressCol = $("<div />", {class: "col-md-6 task_progress"}).appendTo(newRow)

            var newLink = $("<a />", {
                name : "link",
                href : "/search/"+search_phrase,
                text : search_phrase,
                class : "new_task",
                id: data['search_phrase']
                }).appendTo(newTaskCol);

            var newProgressBar = $("<div />",{class:"progressbar "+search_phrase, style:"height:30px;"}).appendTo(newProgressCol);
            $( ".progressbar."+search_phrase_normalized ).progressbar({
                max:100,
                value: 33,
            });


       }





//       var divProgress = $("<div />", {
//                        name: "Progress",
//                        class:'progress',
//                        style: 'width: 200px; height: 30px; background-color: grey;',
//                        id: 'divProgress'
//       }).appendTo('#tasks');
//
//       var divBar = $("<div /", {
//                        name: "Bar",
//                        class: 'progress-bar',
//                        role:"progressbar",
//                        style: 'width:70%',
//       }).appendTo('.progress');
        }
    }

    socket.onclose = function(e) {
       console.log("Connection closed.");
       socket = null;
       isopen = false;
    }
 };
