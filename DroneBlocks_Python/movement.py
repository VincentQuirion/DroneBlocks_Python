import dronekit
import time

# TODO test
# TODO make scan DRY and comment it

""" Make the drone go to a specified location + can execute a function until it is reached """


def go_to_and_wait_until_location_reached(drone, lat, lon, **kwargs):
    # We dont want the drone to change altitude
    target_location = dronekit.LocationGlobal(lat, lon, drone.location.global_frame.alt)
    drone.simple_goto(target_location)
    while True:
        if 'function_to_execute_while' in kwargs:
            kwargs['function_to_execute_while']
        # Check if arrived at location
        current_lat = drone.location.global_frame.lat
        current_lon = drone.location.global_frame.lon
        difference = (abs(current_lat - target_location.lat) + abs(current_lon - target_location.lon))
        if difference <= 0.00001:
            break
        time.sleep(0.2)


# "Placeholder" for function called when waiting to arrive at target location
def nothing():
    pass


""" Take off and wait until it reached a specified altitude (modified from the dronekit docs) """


def takeoff(drone, alt):
    while not drone.is_armable:  # Wait until vehicule is initialized
        time.sleep(1)

    # Arm motors
    # Copter should arm in GUIDED mode
    drone.mode = dronekit.VehicleMode("GUIDED")
    drone.armed = True

    # Confirm vehicle armed before attempting to take off
    while not drone.armed:
        time.sleep(1)  # Wait until drone is armed
    drone.simple_takeoff(alt)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        # Break and return from function just below target altitude.
        if drone.location.global_relative_frame.alt >= alt * 0.95:
            break
        time.sleep(1)


""" Move the drone into a specified direction for a specified distance/amount of time and can execute a function until 
the manoeuvre is over """


def move(drone, direction, distance, **kwargs):
    if direction == 'up':
        axis = (0, 0, -distance)  # Negative values on the 3rd axis make the drone go up
    elif direction == 'down':
        axis = (0, 0, distance)  # Positive values on the 3rd axis make the drone go down
    elif direction == 'forward':
        axis = (distance, 0, 0)  # Positive values on the 1st axis make the drone go forward
    elif direction == 'backward':
        axis = (-distance, 0, 0)  # Negative values on the 1st axis make the drone go backward
    elif direction == 'right':
        axis = (0, distance, 0)  # Positive values on the 2nd axis make the drone go right
    elif direction == 'left':
        axis = (0, -distance, 0)  # Negative values on the 2nd axis make the drone go left

    message = drone.message_factory.set_position_target_local_ned_encode(
        0,
        0, 0,
        9,  # Set the reference frame to MAV_FRAME_BODY_OFFSET_NED
        0b110111111000,  # -- BITMASK -> Consider only the positions
        axis[0], axis[1], axis[2],  # -- POSITION
        0, 0, 0,  # -- VELOCITY
        0, 0, 0,  # -- ACCELERATIONS
        0, 0)
    drone.send_mavlink(message)
    # Wait for the drone to finish its manoeuvre

    # "Experimental" algorithm to compensate the lack of a way to know exactly when the manoeuvre is over
    time_before_manoeuvre_end = distance * 1.75 / 5
    # If function to do while executing manoeuvre, call the function every 1/5 second
    if 'function_to_execute_while' in kwargs:
        count = 0
        while count < time_before_manoeuvre_end:
            if kwargs['function_to_execute_while'](drone) == 'stop':
                break
            time.sleep(0.2)
            count += 0.2
    else:  # If not, do nothing until the manoeuvre is over
        time.sleep(time_before_manoeuvre_end)


""" Make the drone go to specified coordinates at a specified speed """


def go_to(drone, lat, lon, speed, **kwargs):
    drone.groundspeed = speed
    if 'function_to_execute_while' in kwargs:
        function_to_execute_while = kwargs['function_to_execute_while']
    else:
        function_to_execute_while = nothing

    go_to_and_wait_until_location_reached(drone, lat, lon, function_to_execute_while=function_to_execute_while)


""" Make the drone scan a rectangle-shaped area from current location to a specified location """


# TODO make this code DRY and comment it
def scan(drone, lat, lon, speed, **kwargs):
    if 'function_to_execute_while' in kwargs:
        function_to_execute_while = kwargs['function_to_execute_while']
    else:
        function_to_execute_while = nothing
    start_location = drone.location.global_frame
    target_location = dronekit.LocationGlobal(lat, lon, start_location.alt)

    if abs(target_location.lat - start_location.lat) >= abs(target_location.lon - start_location.lon):
        while True:
            heading_to = dronekit.LocationGlobal(target_location.lat, drone.location.global_frame.lon,
                                                 drone.location.global_frame.alt)

            go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

            if (target_location.lon - drone.location.global_frame.lon) >= 0.0005:
                heading_to = dronekit.LocationGlobal(target_location.lat, drone.location.global_frame.lon + 0.0005,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                heading_to = dronekit.LocationGlobal(start_location.lat, drone.location.global_frame.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                if (target_location.lon - drone.location.global_frame.lon) >= 0.0005:
                    heading_to = dronekit.LocationGlobal(start_location.lat, drone.location.global_frame.lon + 0.0005,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                else:
                    heading_to = dronekit.LocationGlobal(start_location.lat, target_location.lon,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

            elif (target_location.lon - drone.location.global_frame.lon) <= -0.0005:
                heading_to = dronekit.LocationGlobal(target_location.lat, drone.location.global_frame.lon - 0.0005,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                heading_to = dronekit.LocationGlobal(start_location.lat, drone.location.global_frame.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                if (target_location.lon - drone.location.global_frame.lon) <= -0.0005:
                    heading_to = dronekit.LocationGlobal(start_location.lat, drone.location.global_frame.lon - 0.0005,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)
                else:
                    heading_to = dronekit.LocationGlobal(start_location.lat, target_location.lon,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

            else:
                heading_to = dronekit.LocationGlobal(target_location.lat, target_location.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

            difference = (abs(drone.location.global_frame.lat - target_location.lat) + abs(
                drone.location.global_frame.lon - target_location.lon))
            if difference <= 0.000125:
                break
            time.sleep(0.2)
    else:
        while True:
            heading_to = dronekit.LocationGlobal(drone.location.global_frame.lat, target_location.lon,
                                                 drone.location.global_frame.alt)
            go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

            if (target_location.lat - drone.location.global_frame.lat) >= 0.0005:
                heading_to = dronekit.LocationGlobal(drone.location.global_frame.lat + 0.0005, target_location.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                heading_to = dronekit.LocationGlobal(drone.location.global_frame.lat, start_location.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                if (target_location.lat - drone.location.global_frame.lat) >= 0.0005:
                    heading_to = dronekit.LocationGlobal(drone.location.global_frame.lat + 0.0005, start_location.lon,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                else:
                    heading_to = dronekit.LocationGlobal(target_location.lat, start_location.lon,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

            elif (target_location.lat - drone.location.global_frame.lat) <= -0.0005:
                heading_to = dronekit.LocationGlobal(drone.location.global_frame.lat - 0.0005, target_location.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                heading_to = dronekit.LocationGlobal(drone.location.global_frame.lat, start_location.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                if (target_location.lat - drone.location.global_frame.lat) <= -0.0005:
                    heading_to = dronekit.LocationGlobal(drone.location.global_frame.lat - 0.0005, start_location.lon,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

                else:
                    heading_to = dronekit.LocationGlobal(target_location.lat, start_location.lon,
                                                         drone.location.global_frame.alt)
                    go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)
            else:
                heading_to = dronekit.LocationGlobal(target_location.lat, drone.location.global_frame.lon,
                                                     drone.location.global_frame.alt)
                go_to_and_wait_until_location_reached(drone, heading_to.lat, heading_to.lon, function_to_execute_while=function_to_execute_while)

            difference = (abs(drone.location.global_frame.lat - target_location.lat) + abs(
                drone.location.global_frame.lon - target_location.lon))
            if difference <= 0.000125:
                break
            time.sleep(0.2)
