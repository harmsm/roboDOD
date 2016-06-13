// ROBOT CONTROL CONSTANTS
var RANGE_PROXIMITY_CUTOFF = 10;  // cm
var RANGE_CHECK_FREQUENCY = 2000; // milliseconds
var LOG_LEVEL = 4;

/* ------------------------------------------------------------------------- */
/* RobotMessage class.  This is for constructing and parsing messages from   */
/* the robot on the socket. These directly mirror the python RobotMessage    */
/* on the robot side. 
/* ------------------------------------------------------------------------- */

var RobotMessage = function(options){

    /* If options is undefined, make it {} */
    options = typeof options !== 'undefined' ? options : {};    

    /* Construct default values for parameters */
    options.destination = typeof options.destination !== 'undefined' ? options.destination : "robot";    
    options.destination_device = typeof options.destination_device !== 'undefined' ? options.destination_device : "";     
    options.source = typeof options.source !== 'undefined' ? options.source : "controller";    
    options.source_device = typeof options.source_device !== 'undefined' ? options.source_device : "controller";

    options.delay = typeof options.delay !== 'undefined' ? options.delay : 0.0;   
    options.message = typeof options.message !== 'undefined' ? options.message : "";     

    /* Class attributes */
    this.arrival_time       = new Date().getTime();

    this.destination        = options.destination;
    this.destination_device = options.destination_device;
    this.source             = options.source;
    this.source_device      = options.source_device;
    this.delay              = parseFloat(options.delay);
    this.message_id         = Math.floor(Math.random()*1e9);
    this.message            = options.message;

    this.minimum_time       = this.arrival_time + this.delay;

    /* Method: return the message in proper string format */
    this.asString = function(){

        return JSON.stringify(this);

    };

    /* Method: build a RobotMessage from a string */
    this.fromString = function(message_string){

        var raw_msg = JSON.parse(message_string);
        for (var key in raw_msg){
            this[key] = raw_msg[key];
        };

        if (isNaN(this.delay)){
            this.delay = 0;
            console.log("setting minimum time to 0...mangled delay? (",this.delay,")");
        }

        this.arrival_time = new Date().getTime();
        this.minimum_time = this.arrival_time + this.delay;

    };

    /* Method: see if delay condition is met */
    this.checkDelay = function(){

        if (Date().getTime() > this.minimum_time){
            return true;
        } else { 
            return false;
        }

    };

}

/* ------------------------------------------------------------------------- */
/* Message routing                                                           */
/* ------------------------------------------------------------------------- */

function recieveMessage(socket,msg){

    /* Recieve a message:
        socket: socket instance
        msg: RobotMessage instance or string in the RobotMesssage style (from socket)
     */ 

    /* If this is not a RobotMessage instance already, turn it into one */
    if (typeof msg.source_device == 'undefined'){

        var message_string = msg;
  
        /* parse the message */
        msg = new RobotMessage();
        msg.fromString(message_string);
  
        /* update the last message recieved */
        if (msg.source_device != "controller"){
            $("#last-recieved-message").html(message_string);
        }
    }   
 
    /* Log the message to the user interface terminal */
    terminalLogger(msg);

    /* parse messages based on source device */
    var handler = {"forward_range"   : parseDistanceMessage,
                   "drivetrain"      : parseDrivetrainMessage,
                   "attention_light" : parseAttentionLightMessage};

    /* apply handler, if present, to message */
    if (typeof handler[msg.source_device] !== 'undefined'){
        handler[msg.source_device](msg);
    }

}   

function sendMessage(socket,message,allow_repeat){

    /* Send a message.  
      
       socket: currently connected socket instance
       message: RobotMessage instance
       allow_repeat: bool that says whether we can pass same message twice in 
                     a row.
    */
 
    console.log(message);
  
    /* By default, allow repeats */
    allow_repeat = typeof allow_repeat !== 'undefined' ? allow_repeat : true;

    /* If this is a message to self, send it back to self */
    if (message.destination_device == "controller"){
        recieveMessage(socket,message);
    } else { 

        /* Log the message to the terminal */ 
        terminalLogger(message);

        /* Convert the message to a string */
        var message_string = message.asString();

        /* Send the message */
        if (($("#last-sent-message").html() != message_string) || (allow_repeat == true)){

            /* Wait until the state of the socket is ready and send message */
            waitForSocketConnection(socket, function(){

                console.log("HERE")
                console.log(message_string)
                socket.send(message_string);

                /* update the last message sent */
                $("#last-sent-message").html(message_string);
            });
        }
    }

}


/* ------------------------------------------------------------------------- */
/* Core controller functionality                                             */
/* ------------------------------------------------------------------------- */

function main(){ 

    /* Grab current url, strip "index.html" if present, strip trailing slash" */
    var url = location.href.replace(/https?:\/\//i, "");
    url = url.replace(/index.html$/,"");
    url = url.replace(/\/+$/, "");

    /* Start up socket. */
    var host = "ws://" + url + "/ws";
    socket = new WebSocket(host);


    /* If we connect take command of the robot. */
    if(socket) {

        /* Turn on light saying things are connected */
        sendMessage(socket,new RobotMessage({destination_device:"client_connected_light",message:"on"}));

        /* Initialize robot to stopped, zero speed.*/
        setSpeed(0,socket);
        setSteer("forward",socket);
        setSteer("coast",socket);

        /* Start listening for input from robot and commands from controller */
        socketListener(socket);

        /* Indicate that connection has been made on contoller user interface */
        $("#connection_status").html("Connected");
        $("#connection_status").toggleClass("text-success",true);
        sendMessage(socket,new RobotMessage({destination_device:"controller",
                                             message:"connected to " + host}));

        // Start measuring ranges
        var myInterval = 0;
        if(myInterval > 0) clearInterval(myInterval);  // stop
        myInterval = setInterval( function checkRange(){
            sendMessage(socket,new RobotMessage({destination_device:"forward_range",
                                                 message:"get"}));
        }, RANGE_CHECK_FREQUENCY );  // run

    /* Or complain...  */
    } else {
        sendMessage(socket,new RobotMessage({destination:"controller",
                                             destination_device:"warn",
                                             message:"Could not connect to " + host + " socket"}));
    }

}

function terminalLogger(msg){

    /* Log commands in the user interface terminal */
    
    /* write to broswer console for debugging purposes */ 
    console.log(msg);

    // If we're not logging *everything* don't log drivetrain and distance stuff.
    if (LOG_LEVEL < 2){
        if (msg.source_device == "drivetrain" || msg.source_device == "forward_range"){
            return;
        }
    }

    var identifier = '';
    var device = '';
    var this_class = '';

    /* Who sent the message? */
    if (msg.source_device == "controller"){
        identifier = "You: ";
        device = msg.destination_device;
        this_class = "to-robot-msg";
    } else {
        identifier = "Robot: ";
        device = msg.source_device;
        this_class = "from-robot-msg";
    }
  
    /* If this is a warning, override existing stylle with warning */
    if (msg.destination_device == "warn"){
        identifier = "Warning: ";
        device = msg.source_device;
        this_class = "warn-msg";
    }

    // Write message contents 
    $("#terminal").append($("<span></span>").addClass(this_class)
                                            .text(identifier + " " +
                                                  device + ": " +
                                                  JSON.stringify(msg.message))
                                            .append("<br/>")
                       );

    // Automatically scroll
    var term = $("#terminal");
    if (term.length){
        term.scrollTop(term[0].scrollHeight - term.height());
    }

}

function closeClient(){
    $("#connection_status").html("Disconnected");
    $("#connection_status").toggleClass("text-success",false);
    sendMessage(socket,new RobotMessage({destination_device:"controller",
                                         message:"connection closed."}));
}


/* ------------------------------------------------------------------------- */
/* Functions for parsing data from the robot                                 */
/* ------------------------------------------------------------------------- */


function parseDistanceMessage(msg){

    /* Update user interface with distance information returned by robot */
    
    /* Ignore distance request ping back */
    if (msg.message == "get"){
        return;
    }

    /* Update range display */
    var dist = 100*parseFloat(msg.message);
    $("#forward_range").html("Range: " + dist.toFixed(3) + " cm");

    /* Deal with distance cutoff to avoid collision */

    /* If we're within 2x cutoff... */
    if (dist < 2*RANGE_PROXIMITY_CUTOFF){
       
        /* If we're within actual cutoff, stop the robot from moving forward */
        if (dist < RANGE_PROXIMITY_CUTOFF){
            $("#forward_range").toggleClass("range-too-close",true);
            $("#forward_range").toggleClass("range-warning",false);

            if ($("#steer_forward_button").hasClass("btn-current-steer")){
                sendMessage(socket,
                            new RobotMessage({destination:"controller",
                                              destination_device:"warn",
                                              message:"Cannot move forward.  Forward range < "
                                                      + RANGE_PROXIMITY_CUTOFF.toFixed(3) + " cm."}));
                setSteer("coast",socket);
            }

        /* If we're not actually within cutoff yet, warn with color */
        } else { 
            $("#forward_range").toggleClass("range-too-close",false);
            $("#forward_range").toggleClass("range-warning",true);
        }

    /* Otherwise, we're still cool */
    } else {
        $("#forward_range").toggleClass("range-too-close",false);
        $("#forward_range").toggleClass("range-warning",false);
    }

}

function parseDrivetrainMessage(msg){

    /* Update user interface with messages from robot about current speed */

    if (msg.destination_device == "warn"){ return; }

    /* If message is about setting speed, update interface with speed */
    if (msg.message[0] == "setspeed"){

        var current_speed = msg.message[1].speed;

        // Update user interface
        $("#actualspeed").html(Math.round(current_speed));
        $("#speedometer").toggleClass("speed-in-sync",true);

    /* Otherwise, update steering interface */ 
    } else { 
    
        var steer = msg.message;

        // Update user interface
        $(".btn-current-steer").toggleClass("btn-default",true)
                               .toggleClass("btn-success",false)
                               .toggleClass("btn-current-steer",false);
        $("#steer_" + steer + "_button").toggleClass("btn-current-steer",true)
                                        .toggleClass("btn-success",true)
                                        .toggleClass("btn-default",false);
    }

}

function parseAttentionLightMessage(msg){
   
    /* update user interface with messages from robot about attention light status */
 
    /* If the message is to turn the light on or flashing, make button active */
    if (msg.message == "flash" || msg.message == "on"){
        $("#attention_light_button").toggleClass("btn-success",true);
        $("#attention_light_button").toggleClass("btn-default",false);
        $("#attention_light_button").toggleClass("attention-light-active",true);

    /* Otherwise, make button inactive */
    } else if (msg.message == "off") {
        $("#attention_light_button").toggleClass("btn-success",false);
        $("#attention_light_button").toggleClass("btn-default",true);
        $("#attention_light_button").toggleClass("attention-light-active",false);
    }

}

/* ------------------------------------------------------------------------- */
/* Functions for sending data to the robot                                   */
/* ------------------------------------------------------------------------- */

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
                waitForSocketConnection(socket, callback);
            }

        }, 5); // wait 5 milisecond for the connection...
}

function setSteer(steer,socket){

    /* Set the current steering for the robot */
    
    // If we're trying to go forward, check for distance
    if ((steer == "forward") && ($("#forward_range").hasClass("range-too-close"))){
        sendMessage(socket,
                    new RobotMessage({destination:"controller",
                                      destination_device:"warn",
                                      message:"Cannot move forward.  Forward range < " +
                                              RANGE_PROXIMITY_CUTOFF.toFixed(3) + " cm."}));
        steer = "coast";
    }

    // Tell the robot what to do
    sendMessage(socket,new RobotMessage({destination_device:"drivetrain",
                                         message:steer}));

}

function setSpeed(speed,socket){

    /* Set the current speed for the robot */

    // Tell the robot what to do.

    sendMessage(socket,new RobotMessage({destination_device:"drivetrain",
                                         message:["setspeed",{"speed":Number(speed)}]}));
}

function setAttentionLight(socket){

    if ($("#attention_light_button").hasClass("attention-light-active")){
        sendMessage(socket,new RobotMessage({destination_device:"attention_light",
                                             message:"off"}));
    } else {
        sendMessage(socket,new RobotMessage({destination_device:"attention_light",
                                             message:"flash"}));
    }

}

/* ------------------------------------------------------------------------- */
/* Deal with user clicks, key presses, key releases, etc.
/* ------------------------------------------------------------------------- */

function socketListener(socket){

    /* Listen for user interaction with the interface and send down the socket */

    socket.onopen = function() {

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

        /* New speed */
        $("#setspeed")[0].noUiSlider.on('change',function(){
            $("#speedometer").toggleClass("speed-in-sync",false);
            setSpeed($("#setspeed")[0].noUiSlider.get(),socket);
        });

        /* Speed 
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
        }); */
        
        /* Flash button */ 
        $("#attention_light_button").click(function(){
            setAttentionLight(socket);
        });
        
        // Key pressed
        document.onkeydown = function KeyCheck(event) {
            passKeyPress(event.which,socket);
        }

        // key released
        document.onkeyup = function KeyCheck(event) {
            passKeyRelease(event.which,socket);
        }

    }

    /* Listen for data coming down the socket */
    socket.onmessage = function(socket_spew) {
        recieveMessage(socket,socket_spew.data);
    }

    /* Close the socket */
    socket.onclose = function() {
        closeClient();
    }

}

function passKeyPress(key,socket){

    switch(event.which) {
        
        /* Steer the robot */
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

        /* Set the speed of the robot */
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
   
    /* This makes it so that keyboard control requires the arrow keys to be held
       down. If the steering buttons are released, the motion will stop. */
 
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

/* ------------------------------------------------------------------------- */
/* Start the controller running                                              */
/* ------------------------------------------------------------------------- */

main();

