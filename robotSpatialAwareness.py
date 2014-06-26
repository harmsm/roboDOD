from random import random, choice
import numpy as np
from math import cos, sin
import time

def randomWalk(number_of_moves=1000,mean_move_time=2):
    """
    Randomly walk around the current space.
    """
    for i in range(number_of_moves):
    
        possible_moves = ["forward","reverse","left","right"]
        sendMessage("robot|drivetrain|%s" % choice(possible_moves))
        time.sleep(random()*doubled_move_time*2)


class SpatialAwareness:

    def __init__(self,box_size=10,resolution=0.05):
        """
        """

        half_length = box_size/2.
        self.xlim = [-half_length,half_length]
        self.ylim = [-half_length,half_length]
        self.resolution = resolution
        self.total_observations = 0
      
        # Create an empty matrix of 0s to represent the coarse-grained space. 
        size = int(np.ceil(box_size/self.resolution))+1
        self.spatial_matrix = np.zeros((size,size),dtype=int)
 

    def calcAngle(self,v1, v2):
        """
        Returns the angle in radians between vectors 'v1' and 'v2'
        """

        v1_u = v1/np.linalg.norm(v1)
        v2_u = v2/np.linalg.norm(v2)
        angle = np.arccos(np.dot(v1_u, v2_u))
        if np.isnan(angle):
            if (v1_u == v2_u).all():
                return 0.0
            else:
                return np.pi

        return angle
    
    def convertCoordinate(self,x,y,coarse=False):
        """
        Convert the raw x, y coordinates that are spit out from the sensors 
        into the same coarse-grained coordinate system.  If coarse is specified,
        the values are actually coarse-grained.  Otherwise, they are left as 
        floats, just in the i,j coordinate system.  Useful for drawing on a 
        client.
        """

        i = (x - self.xlim[0])/self.resolution
        j = (y - self.ylim[0])/self.resolution

        if coarse:
            return int(round(i,0)), int(round(j,0))

        return i, j
   
    def update(self,heading,forward_range):
        """
        Update the spatial matrix with an observation along a vector "heading"
        from our current position at a distance of "foward_range."
        """

        # Calculate the angle of our heading relative to x.
        angle = self.calcAngle(array([1.,0.]),heading[0:2])

        # Given our forward range, we can now place that reading at a fixed 
        # point in x/y space.
        x = cos(angle)*forward_range
        y = sin(angle)*forward_range
    
        # Calculate the coordinates in the coarse-grained spatial matrix
        i = int(round((x - self.xlim[0])/self.resolution,0))
        j = int(round((y - self.ylim[0])/self.resolution,0))
  
        # Eventually we should make the spatial_matrix array dynamic.  That 
        # sounds super painful.  At the moment, just throw an error. 
        if (i < 0):
            err = "passed xmin edge of space!"
            raise ValueError(err)
        if (i > self.spatial_matrix.shape[0]):
            err = "passed xmax edge of space!"
            raise ValueError(err)
        if (j < 0):
            err = "passed ymin edge of space!"
            raise ValueError(err)
        if (j > self.spatial_matrix.shape[1]):
            err = "passed ymax edge of space!"
            raise ValueError(err)
 
        # Record the observation 
        self.spatial_matrix[i,j] += 1
        self.total_observations += 1

        return i, j 

            


"""

# CLIENT

Populate a pretty graphic of squares of increasing 'redness' to indicate found
objects.

Canvas for drawing room:
http://www.williammalone.com/articles/create-html5-canvas-javascript-drawing-app/ 

in js: keydown measures press, keyup measures release.  Therefore, I can make it
so the button presses really do drive the car.  if up-arrow is pressed, turn 
on the motor.  But if it's released, go back to coasting.  Same with left and
right.  Sweet. 

Make acutal buttons for iPad control.  If I'm going this way, I need to have the
tornado server start on boot.

# NAVIGATION

Also, update a strongly-connected-component graph describing the environment in
terms of putative objects.

For navigation purposes:

    1. Define an end point.  
    2. Draw a straight line from our current position to that end point.
    3. Find the first place that line intersects a high probability object.
    4. Identify the strongly-connected-component of that object given some object
       probability cutoff.  
    5. Rotate our driving vector clockwise and counter-clockwise until it does 
       not intersect the current object (or hit an even closer object).  With the
       SCC data, we can jump to the edge of the object.
    6. Start (or continue) moving, updating the spatial_matrix as we go.
    7. Wait some number of steps.
    8. Goto 2.

This strategy is premised on the idea that we have pretty fine steering control.
I'd need to build that too.

What kind of resolution do I need?  How do I think about physical size of bot?
I might imagine having a higher resolution than I need (say 0.05) and then using
the SCC graph to collapse observations that are really close into a single 
object.  
"""
 
