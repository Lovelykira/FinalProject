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
          data = e.data.slice(1, -1);
          var newLink = $("<a />", {
                        name : "link",
                        href : "/search/"+data,
                        text : data,
                        class : "new_task"
                        }).appendTo('#tasks');


       }
    }

    socket.onclose = function(e) {
       console.log("Connection closed.");
       socket = null;
       isopen = false;
    }
 };
