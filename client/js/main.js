// ROBOT CONTROL CONSTANTS
var RANGE_PROXIMITY_CUTOFF = 10;  // cm
var RANGE_CHECK_FREQUENCY = 2000; // milliseconds

/* ------------------------------------------------------------------------- */
/* Basic socket functions */
/* ------------------------------------------------------------------------- */

function logger(message){

    /* Log commands in the terminal */

    // Write to browser console in case all hell breaks loose
    console.log(message);

    // Split the message
    var message_array = message.split("|");

    // Is the message going out (sending) or coming in (recieving)?
    if (message_array[1] == "robot"){
        $("#terminal").append("Sending ");
    } else {
        $("#terminal").append("Recieving ");
    }
       
    // Write message contents 
    $("#terminal").append(message_array[2] + ": ");
    $("#terminal").append(message_array[3] + "\n");

    // Automatically scroll
    var term = $("#terminal");
    if (term.length){
        term.scrollTop(term[0].scrollHeight - term.height());
    }    

}

function waitForSocketConnection(socket, callback){

    /* Wrapper that forces a function to wait until the socket is connected. */
    
    setTimeout(
        function () {

            // If we're connected, run callback  
            if (socket.readyState === 1) {
                if(callback != null){
                    callback();
                }
                return;

            // Otherwise, wait for 5 ms
            } else {
                console.log("Waiting for connection...")
                waitForSocketConnection(socket, callback);
            }

        }, 5); // wait 5 milisecond for the connection...
}


function openSocket(){ 

    /* Open up the socket */

    /* Grab current url, strip "index.html" if present, strip trailing slash" */
    var url = location.href.replace(/https?:\/\//i, "");
    url = url.replace(/index.html$/,"");
    url = url.replace(/\/+$/, "");

    // Start up socket.
    var host = "ws://" + url + "/ws";
    socket = new WebSocket(host);

    // If we connect ...
    if(socket) {

        // Initialize robot to stopped, zero speed.
        setSpeed(0,socket);
        setSteer("forward",socket);
        setSteer("coast",socket);

        // Activate user-interface listener
        socketListener(socket);

        // Indicate that connection has been made.
        $("#connection_status").html("Connected");
        $("#connection_status").toggleClass("text-success",true);
        logger("controller|-1|info|connected on " + host);

        // Start measuring ranges
        var myInterval = 0;
        if(myInterval > 0) clearInterval(myInterval);  // stop
        myInterval = setInterval( function checkRange(){
            sendMessage(socket,"robot|-1|forward_range|get",true);
        }, RANGE_CHECK_FREQUENCY );  // run

    // Or complain...
    } else {
        logger("controller|-1|info|invalid socket \(" + host + "\)" );
    }

}

function sendMessage(socket,message,allow_repeat){

    /* Send a message to the socket.  allow_repeat is a bool that says whether
     * we should pass the same message over and over. */

    // Wait until the state of the socket is not ready and send the message when it is...
    waitForSocketConnection(socket, function(){
    
        logger(message)
        if (($("#last-sent-message").html() != message) || (allow_repeat == true)){
            socket.send(message);
            $("#last-sent-message").html(message);
        }
    });

}

function recieveMessage(message) {

    /* Recieve a message */ 

    $("#last-recieved-message").html(message);

    logger(message);
 
    var message_array = message.split("|");

    if (message_array[2] == "forward_range"){
        parseDistanceMessage(message_array);
    }

}   

function closeClient(){
    $("#connection_status").html("Disconnected");
    $("#connection_status").toggleClass("text-success",false);
    logger("controller|-1|info|connection closed.");    
}

/* ------------------------------------------------------------------------- */
/* More specifically robot-y function */
/* ------------------------------------------------------------------------- */

function parseDistanceMessage(message_array){

    /* Deal with distance information spewed by robot */

    // Update user interface
    var dist = 100*parseFloat(message_array[3]);
    $("#forward_range").html("Range: " + dist.toFixed(3) + " cm");

    // Deal with distance cutoff.  If we're within 2x cutoff...
    if (dist < 2*RANGE_PROXIMITY_CUTOFF){
       
        // If we're within actual cutoff, stop the robot from moving forward 
        if (dist < RANGE_PROXIMITY_CUTOFF){
            $("#forward_range").toggleClass("range-too-close",true);
            $("#forward_range").toggleClass("range-warning",false);

            if ($("#steer_forward_button").hasClass("btn-current-steer")){
                logger("controller|-1|info|Cannot move forward.  Forward range < " + RANGE_PROXIMITY_CUTOFF.toFixed(3) + " cm.");
                setSteer("coast");
            }

        // If we're not actually within cutoff yet, warn with color
        } else { 
            $("#forward_range").toggleClass("range-too-close",false);
            $("#forward_range").toggleClass("range-warning",true);
        }

    // Otherwise, we're still cool
    } else {
        $("#forward_range").toggleClass("range-too-close",false);
        $("#forward_range").toggleClass("range-warning",false);
    }

}

function setSteer(steer){

    /* Set the current steering for the robot */
    
    // If we're trying to go forward, check for distance
    if ((steer == "forward") && ($("#forward_range").hasClass("range-too-close"))){
        logger("controller|-1|info|Cannot move forward.  Forward range < " + RANGE_PROXIMITY_CUTOFF.toFixed(3) + " cm.");
        steer = "coast";
    }

    // Update user interface
    $(".btn-current-steer").toggleClass("btn-default",true)
                           .toggleClass("btn-success",false)
                           .toggleClass("btn-current-steer",false);
    $("#steer_" + steer + "_button").toggleClass("btn-current-steer",true)
                                    .toggleClass("btn-success",true)
                                    .toggleClass("btn-default",false);

    // Tell the robot what to do
    sendMessage(socket,"robot|-1|drivetrain|" + steer,true);

}

function setSpeed(speed,socket){

    /* Set the current speed for the robot */

    // Update user interface
    $(".btn-current-speed").toggleClass("btn-default",true)
                           .toggleClass("btn-success",false)
                           .toggleClass("btn-current-speed",false);
    $("#speed_" + speed + "_button").toggleClass("btn-current-speed",true)
                                    .toggleClass("btn-success",true)
                                    .toggleClass("btn-default",false);

    // Tell the robot what to do.
    sendMessage(socket,"robot|-1|drivetrain|setspeed|{\"speed\":" + speed + "}",true);

}

function socketListener(socket){

    /* Listen for user interaction with the interface and send down the socket */

    socket.onopen = function() {

        // Key pressed
        document.onkeydown = function KeyCheck(event) {
            passKeyPress(event.which,socket);
        }

        // key released
        document.onkeyup = function KeyCheck(event) {
            passKeyRelease(event.which,socket);
        }

        /* Steering */
        $("#steer_left_button").click(function(){
            setSteer("left",socket);
        });
        $("#steer_right_button").click(function(){
            setSteer("right",socket);
        });
        $("#steer_forward_button").click(function(){
            setSteer("forward",socket);
        });
        $("#steer_reverse_button").click(function(){
            setSteer("reverse",socket);
        });
        $("#steer_coast_button").click(function(){
            setSteer("coast",socket);
        });
   
        /* Speed */
        $("#speed_0_button").click(function(){
            setSpeed(0,socket);
        });
        $("#speed_1_button").click(function(){
            setSpeed(1,socket);
        });
        $("#speed_2_button").click(function(){
            setSpeed(2,socket);
        });
        $("#speed_3_button").click(function(){
            setSpeed(3,socket);
        });
        $("#speed_4_button").click(function(){
            setSpeed(4,socket);
        });
        
        /* Flash button */ 
        $("#flash_button").click(function(){
            sendMessage(socket,"robot|-1|attention_light|flash",true);
        });

    }

    /* Listen for data coming down the socket */
    socket.onmessage = function(msg) {
        recieveMessage(msg.data);
    }

    /* Close the socket */
    socket.onclose = function() {
        closeClient();
    }

}

/* ------------------------------------------------------------------------- */
/* Pass messages from client to DOD */
/* ------------------------------------------------------------------------- */

function passKeyPress(key,socket){

    switch(event.which) {
        
        /* Steer the bot */
        case 16: // esc
            setSteer("coast",socket);
            break;
        case 37: // left
            setSteer("left",socket);
            break;
        case 38: // up
            setSteer("forward",socket);
            break;
        case 39: // right
            setSteer("right",socket);
            break;
        case 40: // down
            setSteer("reverse",socket);
            break;

        /* Set the speed of the bot */

        case 48: // set speed to 0
            setSpeed(0,socket);
            break;
        case 49: // set speed to 1
            setSpeed(1,socket);
            break;
        case 50: // set speed to 2 
            setSpeed(2,socket);
            break;
        case 51: // set speed to 3
            setSpeed(3,socket);
            break;
        case 52: // set speed to 4
            setSpeed(4,socket);
            break;
    }
}

function passKeyRelease(key,socket){
   
    /* This makes it so that keyboard control requires the key to be held down.
       If the steering buttons are release, the motion will stop. */
 
    switch(event.which) {
        case 37: // left
            setSteer("coast",socket);
            break;
        case 38: // up
            setSteer("coast",socket);
            break;
        case 39: // right
            setSteer("coast",socket);
            break;
        case 40: // down
            setSteer("coast",socket);
            break;
    }

}

/* Let 'er rip */
openSocket();

