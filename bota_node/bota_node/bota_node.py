#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

from geometry_msgs.msg import WrenchStamped
from sensor_msgs.msg import Imu, Temperature
from std_msgs.msg import UInt32, String
from std_srvs.srv import Trigger

import bota_driver
import enum
import os
import threading


class BotaSensorNode(Node):
    def __init__(self):
        super().__init__("bota_node")

        self._frame = None

        # Declare parameters
        default_config_path = os.path.join(
            get_package_share_directory("bota_node"), "config", "bota_serial_binary.json"
        )
        self.declare_parameter("config_path", default_config_path)
        self.declare_parameter("read_rate", 50.0)
        self.declare_parameter("publish_rate", 50.0)
        self.declare_parameter("frame_id", "bota_sensor")
        self.declare_parameter("tare_on_startup", True)
        self.declare_parameter("reset_service_name", "/bota_node/reset")

        config_path = self.get_parameter("config_path").get_parameter_value().string_value
        read_rate = self.get_parameter("read_rate").get_parameter_value().double_value
        publish_rate = self.get_parameter("publish_rate").get_parameter_value().double_value
        self.frame_id = self.get_parameter("frame_id").get_parameter_value().string_value
        tare_on_startup = self.get_parameter("tare_on_startup").get_parameter_value().bool_value
        reset_service_name = self.get_parameter("reset_service_name").get_parameter_value().string_value

        self.get_logger().info(f"Using Bota driver config: {config_path}")
        self.get_logger().info(f"Read rate: {read_rate} Hz")
        self.get_logger().info(f"Publish rate: {publish_rate} Hz")
        self.get_logger().info(f"Frame ID: {self.frame_id}")

        self.wrench_pub = self.create_publisher(WrenchStamped, "bota/wrench_N_and_Nm", 10)

        # Create and start driver
        self.driver = bota_driver.BotaDriver(config_path)

        self.get_logger().info("Configuring Bota driver...")
        if not self.driver.configure():
            raise RuntimeError("Failed to configure Bota driver")

        if tare_on_startup:
            self.get_logger().info("Taring Bota sensor...")
            if not self.driver.tare():
                raise RuntimeError("Failed to tare Bota sensor")

        self.reset_service = self.create_service(Trigger, reset_service_name, self._reset_service_callback)
        self.get_logger().info(f"Reset service advertised on {reset_service_name}")

        self.get_logger().info("Activating Bota driver...")
        if not self.driver.activate():
            raise RuntimeError("Failed to activate Bota driver")

        self.get_logger().info("Bota sensor initialized successfully")

        # Start read timer
        self.read_timer = self.create_timer(
            1.0 / read_rate,  # Read at read_rate Hz
            self.read_sensor,
            clock=rclpy.clock.Clock(clock_type=rclpy.clock.ClockType.STEADY_TIME),
        )

        # Start publish timer
        self.timer = self.create_timer(
            1.0 / publish_rate,  # Publish at publish_rate Hz
            self.publish_frame,
            clock=rclpy.clock.Clock(clock_type=rclpy.clock.ClockType.STEADY_TIME),
        )

    def _reset_service_callback(self, request, response):
        """ROS service callback for the reset service.

        Returns success immediately, then shuts down the node so Docker can restart it.
        """
        response.success = True
        response.message = "Resetting node..."
        self.get_logger().info("Reset requested, shutting down node...")
        # Shutdown from a separate thread so the service response can be sent first.
        threading.Thread(target=self._request_shutdown, daemon=True).start()
        return response

    def _request_shutdown(self):
        """Trigger rclpy shutdown from outside the service callback thread."""
        # Give the service response a moment to be sent.
        threading.Event().wait(0.1)
        rclpy.shutdown()

    def read_sensor(self):
        self._frame = self.driver.read_frame()


    def publish_frame(self):
        stamp = self.get_clock().now().to_msg()

        # Wrench (force / torque)
        wrench_msg = WrenchStamped()
        wrench_msg.header.stamp = stamp
        wrench_msg.header.frame_id = self.frame_id
        wrench_msg.wrench.force.x = float(self._frame.force[0])
        wrench_msg.wrench.force.y = float(self._frame.force[1])
        wrench_msg.wrench.force.z = float(self._frame.force[2])
        wrench_msg.wrench.torque.x = float(self._frame.torque[0])
        wrench_msg.wrench.torque.y = float(self._frame.torque[1])
        wrench_msg.wrench.torque.z = float(self._frame.torque[2])
        self.wrench_pub.publish(wrench_msg)

    def destroy_node(self):
        self.get_logger().info("Shutting down Bota driver...")
        if self.driver is not None:
            if not self.driver.deactivate():
                self.get_logger().error("Failed to deactivate Bota driver")
            if not self.driver.shutdown():
                self.get_logger().error("Failed to shutdown Bota driver")
            self.driver = None
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = BotaSensorNode()
        rclpy.spin(node)
    except Exception as e:
        if node is not None:
            node.get_logger().fatal(f"Fatal error: {e}")
        else:
            print(f"Fatal error: {e}")
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
