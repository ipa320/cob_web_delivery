#!/usr/bin/env python

from cob_web_delivery.srv import *
from cob_web_delivery.msg import *
from move_base_msgs.msg import *
from cob_phidgets.msg import DigitalSensor

import rospy
import actionlib


class DeliveryServer:
   # create messages that are used to publish feedback/result
  _feedback = DeliveryFeedback()
  _result = DeliveryResult()

  def __init__(self):
    rospy.on_shutdown(self.shutdown)
    print "Starting delivery Server"
    self.server = actionlib.SimpleActionServer('delivery', DeliveryAction, self.execute, False)
    self.server.start()
    rospy.Subscriber("FB_phidget", DigitalSensor, self.feedback_cb)
    print "Delivery Server started"
    print "Connecting to move_base ActionServer"
    self.mbac = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    self.mbac.wait_for_server()
    print "Connected to MoveBase"

    self.button = False  # not here


  def execute(self, goal):
    print "Got request for %s" % (goal.item)
    rospy.sleep(rospy.Duration.from_sec(1.0))
    self._feedback.state = 2
    self.server.publish_feedback(self._feedback)
    rospy.sleep(rospy.Duration.from_sec(1.0))

    # goto pickup (p2)
    bgoal = MoveBaseGoal()
    bgoal.target_pose.header.frame_id = "map"
    bgoal.target_pose.header.stamp = rospy.Time.now()
    bgoal.target_pose.pose.position = goal.pickup_poses[0].position
    bgoal.target_pose.pose.orientation.w = 1.0
    print "pick:", goal.pickup_poses[0].position
    self.mbac.send_goal(bgoal)

    # wait 4 feedback
    #self.wait_fb()
    rospy.sleep(rospy.Duration.from_sec(1.0))

    #goto destination (p1)
    bgoal = MoveBaseGoal()
    bgoal.target_pose.header.frame_id = "map"
    bgoal.target_pose.header.stamp = rospy.Time.now()
    bgoal.target_pose.pose.position = goal.destinations[0].position
    bgoal.target_pose.pose.orientation.w = 1.0
    print "destination:", goal.destinations[0].position
    self.mbac.send_goal(bgoal)

    #wait 4 FB
    self.wait_fb()

    self._result.success = True
    self._result.Error = "Arrived"
    self._result.state = 1
    self.server.set_succeeded(self._result)
    print "Action done"

  def feedback_cb(self, data):
        print data.state
        print data.uri
        self.button = True

  def wait_fb(self):
        while not self.button:
            rospy.sleep(rospy.Duration.from_sec(0.5))  # better
        self.button = False
        return True

  def shutdown(self):
    print "\n shutdown delivery manager"
    self.mbac.cancel_all_goals()
    self.server.set_aborted()
    #todo publish aborted state


if __name__ == '__main__':
  rospy.init_node('delivery_server')
  server = DeliveryServer()
  print "Ready to Serve"
  rospy.spin()
  

