/* Global variables accessible across all functions.  */

var LAST_SENT_MESSAGE = '';
var LAST_RECIEVED_MESSAGE = '';
var LAST_SPEED_BUTTON = '';
var LAST_STEER_BUTTON = '';

/* ------------------------------------------------------------------------- */
/* Basic socket functions */
/* ------------------------------------------------------------------------- */

function logger(message){

    console.log(message);

    var message_array = message.split("|");

    if (message_array[1] == "robot"){
        $("#terminal").append("Sending ");
    } else {
        $("#terminal").append("Recieving ");
    }
        
    $("#terminal").append(message_array[2] + ": ");
    $("#terminal").append(message_array[3] + "\n");
    var term = $("#terminal");
    if (term.length){
        term.scrollTop(term[0].scrollHeight - term.height());
    }    

}

function openSocket(){ 

    /* Open up the socket */

    /* Grab current url, strip "index.html" if present, strip trailing slash" */
    var url = location.href.replace(/https?:\/\//i, "");
    url = url.replace(/index.html$/,"");
    url = url.replace(/\/+$/, "");

    var host = "ws://" + url + "/ws";
    socket = new WebSocket(host);

    if(socket) {
        // Initialize to stopped

        triggerSetSpeed(0,socket);
        triggerSetSteer("forward",socket);
        triggerSetSteer("coast",socket);

        socketListener(socket);
        $("#connection_status").append("<h4 class=\"text-success\">Connected</h4>");
        logger("controller|-1|info|connected on " + host);


        var iFrequency = 2000; // expressed in miliseconds
        var myInterval = 0;

        if(myInterval > 0) clearInterval(myInterval);  // stop
        myInterval = setInterval( function checkRange(){
            sendMessage(socket,"robot|-1|forward_range|get",true);

        }, iFrequency );  // run

    } else {
        logger("controller|-1|info|invalid socket \(" + host + "\)" );
    }

}

function updateButton(this_button,previous_button){

    $(previous_button).addClass("btn-default");
    $(previous_button).removeClass("btn-success");
    
    $(this_button).removeClass("btn-default");
    $(this_button).addClass("btn-success");

    return this_button;

}

function triggerSetSteer(steer){
    LAST_STEER_BUTTON = updateButton("#" + steer + "_button",LAST_STEER_BUTTON);
    sendMessage(socket,"robot|-1|drivetrain|" + steer,true);
}

function triggerSetSpeed(speed,socket){
    
    LAST_SPEED_BUTTON = updateButton("#speed_" + speed + "_button",LAST_SPEED_BUTTON);
    sendMessage(socket,"robot|-1|drivetrain|setspeed|{\"speed\":" + speed + "}",true);
}

function socketListener(socket){

    /* Listen for spew on the socket */

    socket.onopen = function() {

        // Key pressed
        document.onkeydown = function KeyCheck(event) {
            passKeyPress(event.which,socket);
        }

        // key released
        document.onkeyup = function KeyCheck(event) {
            passKeyRelease(event.which,socket);
        }

        $("#left_button").click(function(){
            triggerSetSteer("left",socket);
        });
        $("#right_button").click(function(){
            triggerSetSteer("right",socket);
        });
        $("#forward_button").click(function(){
            triggerSetSteer("forward",socket);
        });
        $("#reverse_button").click(function(){
            triggerSetSteer("reverse",socket);
        });
        $("#coast_button").click(function(){
            triggerSetSteer("coast",socket);
        });

        $("#speed_0_button").click(function(){
            triggerSetSpeed(0,socket);
        });
        $("#speed_1_button").click(function(){
            triggerSetSpeed(1,socket);
        });
        $("#speed_2_button").click(function(){
            triggerSetSpeed(2,socket);
        });
        $("#speed_3_button").click(function(){
            triggerSetSpeed(3,socket);
        });
        $("#speed_4_button").click(function(){
            triggerSetSpeed(4,socket);
        });
         
        $("#flash_button").click(function(){
            sendMessage(socket,"robot|-1|attention_light|flash",true);
        });

    }

    socket.onmessage = function(msg) {
        recieveMessage(msg.data);
    }
    socket.onclose = function() {
        closeClient();
    }

}

// Make the function wait until the connection is made...
function waitForSocketConnection(socket, callback){
    setTimeout(
        function () {
            if (socket.readyState === 1) {
                console.log("Connection is made")
                if(callback != null){
                    callback();
                }
                return;

            } else {
                console.log("wait for connection...")
                waitForSocketConnection(socket, callback);
            }

        }, 5); // wait 5 milisecond for the connection...
}

function sendMessage(socket,message,allow_repeat){

    /* Send a message to the socket.  allow_repeat is a bool that says whether
     * we should pass the same message over and over. */

    // Wait until the state of the socket is not ready and send the message when it is...
    waitForSocketConnection(socket, function(){
    
        logger(message)
        if ((LAST_SENT_MESSAGE != message) || (allow_repeat == true)){
            socket.send(message);
            LAST_SENT_MESSAGE = message;
        }
    });

}

function recieveMessage(message) {

    /* Recieve a message */ 

    LAST_RECIEVED_MESSAGE = message;

    logger(message);
 
    var message_array = message.split("|");

    if (message_array[2] == "forward_range"){
        var dist = 100*parseFloat(message_array[3]);
        $("#forward_range").html("Range: " + dist.toFixed(3) + " cm");
    }

}   

function closeClient(){
    $("#connection_status").html("<h4 class=\"text-success\">Disconnected</h4>");
    logger("controller|-1|info|connection closed.");    
}

/* ------------------------------------------------------------------------- */
/* Pass messages from client to DOD */
/* ------------------------------------------------------------------------- */

function passKeyPress(key,socket){

    switch(event.which) {
        case 16: // esc
            sendMessage(socket,"robot|-1|drivetrain|stop",allow_repeat=true);
            sendMessage(socket,"robot|-1|drivetrain|coast",allow_repeat=true);
            break;
        case 37: // left
            sendMessage(socket,"robot|-1|drivetrain|left",allow_repeat=false);
            break;
        case 38: // up
            sendMessage(socket,"robot|-1|drivetrain|forward",allow_repeat=false);
            break;
        case 39: // right
            sendMessage(socket,"robot|-1|drivetrain|right",allow_repeat=false);
            break;
        case 40: // down
            sendMessage(socket,"robot|-1|drivetrain|reverse",allow_repeat=false);
            break;
    }
}

function passKeyRelease(key,socket){
    
    switch(event.which) {
        case 37: // left
            sendMessage(socket,"robot|-1|drivetrain|center",allow_repeat=false);
            break;
        case 38: // up
            sendMessage(socket,"robot|-1|drivetrain|coast",allow_repeat=false);
            break;
        case 39: // right
            sendMessage(socket,"robot|-1|drivetrain|center",allow_repeat=false);
            break;
        case 40: // down
            sendMessage(socket,"robot|-1|drivetrain|coast",allow_repeat=false);
            break;
    }

}

/* ------------------------------------------------------------------------- */
/* Pass messages from DOD to client */
/* ------------------------------------------------------------------------- */


function populateMap( ) { 

    // Script for updating moving map.  Currently hacked to generate random
    // values for the density at each point in the grid.

    RGBToHex = function(r,g,b){
        return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
    }

    // HACK
    var density = 0.5;    
 
    var i = 0; 
    var j = 0;
    var x = 0;
    var y = 0;
    var mainMatrix = Array(200);
    for (i = 0; i < 200; i++){
        mainMatrix[i] = Array(200);
    } 

    // Initialize drawing area
    var c = document.getElementById("moving_map");
    var ctx = c.getContext("2d");
    ctx.clearRect(0, 0, ctx.width, ctx.height);
    ctx.fillStyle = "#FF0000";

    // Update the display every 500 ms.
    var nIntervId = setInterval(updateDrawing,500);
   
    function updateDrawing(){

        // Update the matrix
        for (i = 0; i < 200; i++){
            for (j = 0; j < 200; j++){
                if (Math.random() < density){
                    mainMatrix[i][j] = 255 - Math.floor(Math.random()*255);
                } else { 
                    mainMatrix[i][j] = 255;
                }
            }
        }
      
        // Update the display 
        ctx.clearRect(0, 0, 800, 800);  //ctx.width, ctx.height);
        for (i = 0; i < 200; i++){
            for (j = 0; j < 200; j++){
                ctx.fillStyle=RGBToHex(255,mainMatrix[i][j],mainMatrix[i][j]);
                ctx.fillRect(i*4,j*4,4,4);
            }
        }

        // Draw the robot on the display
        var robot_icon = new Image();
        robot_icon.src = "img/robot-icon.png";
        ctx.drawImage(robot_icon,400,400) 
    }

}

openSocket();

