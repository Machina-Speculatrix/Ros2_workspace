#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from turtlesim.srv import Spawn, SetPen
from turtlesim.msg import Pose
from functools import partial
import math
import random

class CollisionAvoidance(Node):
    def __init__(self):
        super().__init__("collision_avoidance_node")
        
        self.turtle1_pose = None
        self.turtle2_pose = None

        self.vel1 = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)
        self.vel2 = self.create_publisher(Twist, "/turtle2/cmd_vel", 10)

        self.create_subscription(Pose, "/turtle1/pose", self.pose_callback1, 10)
        self.create_subscription(Pose, "/turtle2/pose", self.pose_callback2, 10)

        self.spawn(2.0, 2.0, 0.0)
        self.timer = self.create_timer(1.0, self.random_movement)

    def pose_callback1(self, msg: Pose):
        self.turtle1_pose = msg

    def pose_callback2(self, msg: Pose):
        self.turtle2_pose = msg

    def spawn(self, x, y, theta):
        client = self.create_client(Spawn, "/spawn")
        while not client.wait_for_service(1.0):
            self.get_logger().info("Waiting for /spawn service...")
        
        request = Spawn.Request()
        request.x = x
        request.y = y
        request.theta = theta

        future = client.call_async(request)
        future.add_done_callback(partial(self.spawn_callback))

    def spawn_callback(self, future):
        try:
            name = future.result().name
            self.get_logger().info(f"Spawned new turtle: {name}")
        except Exception as e:
            self.get_logger().error(f"Failed to spawn turtle: {e}")

    def random_movement(self):
        if self.turtle1_pose is None or self.turtle2_pose is None:
            return

        cmd1 = Twist()
        cmd2 = Twist()

        distance = math.sqrt(
            (self.turtle1_pose.x - self.turtle2_pose.x) ** 2 +
            (self.turtle1_pose.y - self.turtle2_pose.y) ** 2
        )

        if distance < 1.0:
            cmd1.linear.x = -1.0
            cmd1.angular.z = random.uniform(1.0, 2.0)
            cmd2.linear.x = -1.0
            cmd2.angular.z = random.uniform(-2.0, -1.0)
        else:
            cmd1.linear.x = random.uniform(1.0, 2.0)
            cmd1.angular.z = random.uniform(-1.0, 1.0)
            cmd2.linear.x = random.uniform(1.0, 2.0)
            cmd2.angular.z = random.uniform(-1.0, 1.0)

        if self.turtle1_pose.x <= 0.5 or self.turtle1_pose.x >= 10.5:
            cmd1.linear.x = -cmd1.linear.x
            cmd1.angular.z = random.uniform(1.0, 2.0)

        if self.turtle1_pose.y <= 0.5 or self.turtle1_pose.y >= 10.5:
            cmd1.linear.x = -cmd1.linear.x
            cmd1.angular.z = random.uniform(1.0, 2.0)

        if self.turtle2_pose.x <= 0.5 or self.turtle2_pose.x >= 10.5:
            cmd2.linear.x = -cmd2.linear.x
            cmd2.angular.z = random.uniform(-2.0, -1.0)

        if self.turtle2_pose.y <= 0.5 or self.turtle2_pose.y >= 10.5:
            cmd2.linear.x = -cmd2.linear.x
            cmd2.angular.z = random.uniform(-2.0, -1.0)

        self.vel1.publish(cmd1)
        self.vel2.publish(cmd2)

        if self.turtle1_pose.x > 5.5 and self.turtle2_pose.x <= 5.5:
            self.setpen(0, 255, 0, 3, 1)
        elif self.turtle2_pose.x > 5.5 and self.turtle1_pose.x <= 5.5:
            self.setpen(255, 0, 0, 3, 1)
        else:
            self.setpen(0, 0, 255, 3, 1)

    def setpen(self, r, g, b, width, off):
        client1 = self.create_client(SetPen, "/turtle1/set_pen")
        client2 = self.create_client(SetPen, "/turtle2/set_pen")
        
        while not client1.wait_for_service(1.0):
            self.get_logger().warn("Waiting for service /turtle1/set_pen...")
        while not client2.wait_for_service(1.0):
            self.get_logger().warn("Waiting for service /turtle2/set_pen...")
        
        request = SetPen.Request()
        request.r = r
        request.g = g
        request.b = b
        request.width = width
        request.off = off

        future1 = client1.call_async(request)
        future1.add_done_callback(partial(self.callpen))
        future2 = client2.call_async(request)
        future2.add_done_callback(partial(self.callpen))

    def callpen(self, future):
        try:
            response = future.result()
        except Exception as e:
            self.get_logger().error("Service call failed: %r" % (e,))

def main(args=None):
    rclpy.init(args=args)
    node = CollisionAvoidance()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()