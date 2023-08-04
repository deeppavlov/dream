#!/usr/bin/env python
import rospy
from std_msgs.msg import String


def callback(data):
    rospy.loginfo(rospy.get_caller_id() + "Received: %s", data.data)
    # TODO: implement logic


def listener():
    rospy.init_node("listener", anonymous=True)

    rospy.Subscriber("talker", String, callback)

    rospy.spin()


if __name__ == "__main__":
    listener()
