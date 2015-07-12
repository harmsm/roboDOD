// ROBOT CONTROL CONSTANTS
var RANGE_PROXIMITY_CUTOFF = 10;  // cm
var RANGE_CHECK_FREQUENCY = 2000; // milliseconds
var LOG_LEVEL = 1;

function constructMessage(destination,source,delay,device,message){

    // Construct a message in the string format recognized by RobotMessage and
    // terminalLogger
    
    destination = typeof destination !== 'undefined' ? destination : "robot";    
    source = typeof destination !== 'undefined' ? destination : "controller";    
    delay = typeof delay !== 'undefined' ? delay : "-1";     
    device = typeof device !== 'undefined' ? device : "info";     
    message = typeof message !== 'undefined' ? message : "empty message";     

    return destination + "|" + source + "|" + delay + "|" + device + "|" + message;

}

/* ------------------------------------------------------------------------- */
/* Basic socket functions */
/* ------------------------------------------------------------------------- */

function terminalLogger(message){

    /* Log commands in the terminal */

    // Write to browser console in case all hell breaks loose
    console.log(message);

    // Split the message
    var message_array = message.split("|");

    // If we're not logging *everything* don't log drivetrain and distance stuff.
    if (LOG_LEVEL < 2){
        if (['drivetrain', 'forward_range'].indexOf(message_array[3]) >= 0) {
            return;
        }
    }

    var identifier = '';
    var this_class = '';

    // Is the message going to robot, to the contoller, or a warning?
    if (message_array[0] == "robot"){
        identifier = "You: ";
        this_class = "to-robot-msg";
    } else if (message_array[0] == "warn"){
        identifier = "Warning: ";
        this_class = "warn-msg";
    } else {
        identifier = "Robot: ";
        this_class = "from-robot-msg";
    }

    // Write message contents 
    $("#terminal").append($("<span></span>").addClass(this_class)
                                            .text(identifier + 
                                                  message_array[3] + ": " +
                                                  message_array.slice(4))
                                            .append("<br/>")
                       );

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
    var host = "wss://" + url + "/wss";
    socket = new WebSocket(host);

    // If we connect ...
    if(socket) {

        // Turn on light saying things are connected
        sendMessage(socket,constructMessage(device="client_connected_light",
                                            message="on"),true);

        // Initialize robot to stopped, zero speed.
        setSpeed(0,socket);
        setSteer("forward",socket);
        setSteer("coast",socket);

        // Activate user-interface listener
        socketListener(socket);

        // Indicate that connection has been made.
        $("#connection_status").html("Connected");
        $("#connection_status").toggleClass("text-success",true);
        terminalLogger(constructMessage(destination="controller",
                                        device="info",
                                        message="connected to " + host));

        // Start measuring ranges
        var myInterval = 0;
        if(myInterval > 0) clearInterval(myInterval);  // stop
        myInterval = setInterval( function checkRange(){
            sendMessage(socket,
                        constructMessage(destination="robot",
                                         device="forward_range",
                                         message="get"),
                        true);
        }, RANGE_CHECK_FREQUENCY );  // run

    // Or complain...
    } else {
        terminalLogger(constructMessage(destination="warn",
                                        device="info",
                                        message="invalid socket (" + host ")"));
    }

}


function sendMessage(socket,message,allow_repeat){

    /* Send a message to the socket.  allow_repeat is a bool that says whether
     * we should pass the same message over and over. */

    // Wait until the state of the socket is not ready and send the message when it is...
    waitForSocketConnection(socket, function(){

        // Log the message to the terminal    
        terminalLogger(message);

        if (($("#last-sent-message").html() != message) || (allow_repeat == true)){
            socket.send(message);

            // update the last message sent
            $("#last-sent-message").html(message);
        }
    });

}

function recieveMessage(message) {

    /* Recieve a message */ 

    // update the last message recieved
    $("#last-recieved-message").html(message);

    // Log the message to the terminal
    terminalLogger(message);

    // parse the message 
    var message_array = message.split("|");

    if (message_array[3] == "forward_range"){
        parseDistanceMessage(message_array);
    } else if (message_array[3] == "drivetrain"){
        parseDrivetrainMessage(message_array);
    } else if (message_array[3] == "attention_light"){
        parseAttentionLightMessage(message_array);
    }

}   

function closeClient(){
    $("#connection_status").html("Disconnected");
    $("#connection_status").toggleClass("text-success",false);
    terminalLogger(constructMessage(destination="controller",
                                    device="info",
                                    message="connection closed."));
}

/* ------------------------------------------------------------------------- */
/* Recieve data from the robot */
/* ------------------------------------------------------------------------- */

function parseDistanceMessage(message_array){

    /* Deal with distance information spewed by robot */
    
    // Ignore ping-back
    if (message_array[4] == "get"){
        return;
    }

    // Update user interface
    var dist = 100*parseFloat(message_array[4]);
    $("#forward_range").html("Range: " + dist.toFixed(3) + " cm");

    // Deal with distance cutoff.  If we're within 2x cutoff...
    if (dist < 2*RANGE_PROXIMITY_CUTOFF){
       
        // If we're within actual cutoff, stop the robot from moving forward 
        if (dist < RANGE_PROXIMITY_CUTOFF){
            $("#forward_range").toggleClass("range-too-close",true);
            $("#forward_range").toggleClass("range-warning",false);

            if ($("#steer_forward_button").hasClass("btn-current-steer")){
                terminalLogger(constructMessage(destination="warn",
                                                device="info",
                                                message="Cannot move forward.  Forward range < "
                                                        + RANGE_PROXIMITY_CUTOFF.toFixed(3) + " cm."));
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

function parseDrivetrainMessage(message_array){

    if (message_array[4] == "setspeed"){

        var current_speed = message_array[5].split(":")[1].split("}")[0];

        // Update user interface
        $(".btn-current-speed").toggleClass("btn-default",true)
                               .toggleClass("btn-success",false)
                               .toggleClass("btn-current-speed",false);
        $("#speed_" + current_speed + "_button").toggleClass("btn-current-speed",true)
                                                .toggleClass("btn-success",true)
                                                .toggleClass("btn-default",false);
    } else { 
    
        var steer = message_array[4];

        // Update user interface
        $(".btn-current-steer").toggleClass("btn-default",true)
                               .toggleClass("btn-success",false)
                               .toggleClass("btn-current-steer",false);
        $("#steer_" + steer + "_button").toggleClass("btn-current-steer",true)
                                        .toggleClass("btn-success",true)
                                        .toggleClass("btn-default",false);
    }

}

function parseAttentionLightMessage(message_array){

    if (message_array[4] == "flash" || message_array[4] == "on"){
        $("#attention_light_button").toggleClass("btn-success",true);
        $("#attention_light_button").toggleClass("btn-default",false);
        $("#attention_light_button").toggleClass("attention-light-active",true);
    } else if (message_array[4] == "off") {
        $("#attention_light_button").toggleClass("btn-success",false);
        $("#attention_light_button").toggleClass("btn-default",true);
        $("#attention_light_button").toggleClass("attention-light-active",false);
    }

}

/* ------------------------------------------------------------------------- */
/* Send data to the robot */
/* ------------------------------------------------------------------------- */

function setSteer(steer){

    /* Set the current steering for the robot */
    
    // If we're trying to go forward, check for distance
    if ((steer == "forward") && ($("#forward_range").hasClass("range-too-close"))){
        terminalLogger(constructMessage(destination="warn",
                                        device="info",
                                        message="Cannot move forward.  Forward range < " +
                                                RANGE_PROXIMITY_CUTOFF.toFixed(3) + " cm."));
        steer = "coast";
    }

    // Tell the robot what to do
    sendMessage(socket,"robot|controller|-1|drivetrain|" + steer,true);

}

function setSpeed(speed,socket){

    /* Set the current speed for the robot */

    // Tell the robot what to do.
    sendMessage(socket,"robot|controller|-1|drivetrain|setspeed|{\"speed\":" + speed + "}",true);

}

function setAttentionLight(socket){

    if ($("#attention_light_button").hasClass("attention-light-active")){
        sendMessage(socket,"robot|controller|-1|attention_light|off",true);
    } else {
        sendMessage(socket,"robot|controller|-1|attention_light|flash",true);
    }

}

/* ------------------------------------------------------------------------- */
/* Deal with user clicks, key presses, key releases, etc.
/* ------------------------------------------------------------------------- */

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
        $("#attention_light_button").click(function(){
            setAttentionLight(socket);
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

