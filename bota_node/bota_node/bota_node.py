#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

from geometry_msgs.msg import WrenchStamped
from sensor_msgs.msg import Imu, Temperature
from std_msgs.msg import UInt32, String

import bota_driver
import enum
import os


class BotaSensorNode(Node):
    def __init__(self):
        super().__init__("bota_node")

        # Declare parameters
        default_config_path = os.path.join(
            get_package_share_directory("bota_node"), "config", "bota_serial_binary.json"
        )
        self.declare_parameter("config_path", default_config_path)
        self.declare_parameter("publish_rate", 100.0)
        self.declare_parameter("frame_id", "bota_sensor")
        self.declare_parameter("tare_on_startup", True)

        config_path = self.get_parameter("config_path").get_parameter_value().string_value
        publish_rate = self.get_parameter("publish_rate").get_parameter_value().double_value
        self.frame_id = self.get_parameter("frame_id").get_parameter_value().string_value
        tare_on_startup = self.get_parameter("tare_on_startup").get_parameter_value().bool_value

        self.get_logger().info(f"Using Bota driver config: {config_path}")
        self.get_logger().info(f"Publish rate: {publish_rate} Hz")
        self.get_logger().info(f"Frame ID: {self.frame_id}")

        self.wrench_pub = self.create_publisher(WrenchStamped, "bota/wrench_N_and_Nm", 10)
        self.imu_pub = self.create_publisher(Imu, "bota/imu_mps2_and_radps", 10)
        self.temperature_pub = self.create_publisher(Temperature, "bota/temperature_C", 10)
        self.status_int_pub = self.create_publisher(UInt32, "bota/status_int", 10)
        self.status_string_pub = self.create_publisher(String, "bota/status_string", 10)

        # Create and start driver
        self.driver = bota_driver.BotaDriver(config_path)

        self.get_logger().info("Configuring Bota driver...")
        if not self.driver.configure():
            raise RuntimeError("Failed to configure Bota driver")

        if tare_on_startup:
            self.get_logger().info("Taring Bota sensor...")
            if not self.driver.tare():
                raise RuntimeError("Failed to tare Bota sensor")

        self.get_logger().info("Activating Bota driver...")
        if not self.driver.activate():
            raise RuntimeError("Failed to activate Bota driver")

        self.get_logger().info("Bota sensor initialized successfully")

        # Start publish timer
        timer_period = 1.0 / publish_rate
        self.timer = self.create_timer(
            timer_period,
            self.publish_frame,
            clock=rclpy.clock.Clock(clock_type=rclpy.clock.ClockType.STEADY_TIME),
        )

    def publish_frame(self):
        if self.driver is None:
            return

        try:
            frame = self.driver.read_frame()
        except Exception as e:
            self.get_logger().error(f"Failed to read Bota frame: {e}")
            return

        stamp = self.get_clock().now().to_msg()

        # Wrench (force / torque)
        wrench_msg = WrenchStamped()
        wrench_msg.header.stamp = stamp
        wrench_msg.header.frame_id = self.frame_id
        wrench_msg.wrench.force.x = float(frame.force[0])
        wrench_msg.wrench.force.y = float(frame.force[1])
        wrench_msg.wrench.force.z = float(frame.force[2])
        wrench_msg.wrench.torque.x = float(frame.torque[0])
        wrench_msg.wrench.torque.y = float(frame.torque[1])
        wrench_msg.wrench.torque.z = float(frame.torque[2])
        self.wrench_pub.publish(wrench_msg)

        # IMU (angular rate / acceleration)
        imu_msg = Imu()
        imu_msg.header.stamp = stamp
        imu_msg.header.frame_id = self.frame_id
        # Orientation unknown
        imu_msg.orientation.x = 0.0
        imu_msg.orientation.y = 0.0
        imu_msg.orientation.z = 0.0
        imu_msg.orientation.w = 1.0
        imu_msg.orientation_covariance[0] = -1.0

        imu_msg.angular_velocity.x = float(frame.angular_rate[0])
        imu_msg.angular_velocity.y = float(frame.angular_rate[1])
        imu_msg.angular_velocity.z = float(frame.angular_rate[2])

        imu_msg.linear_acceleration.x = float(frame.acceleration[0])
        imu_msg.linear_acceleration.y = float(frame.acceleration[1])
        imu_msg.linear_acceleration.z = float(frame.acceleration[2])
        self.imu_pub.publish(imu_msg)

        # Temperature
        temp_msg = Temperature()
        temp_msg.header.stamp = stamp
        temp_msg.header.frame_id = self.frame_id
        temp_msg.temperature = float(frame.temperature)
        temp_msg.variance = 0.0
        self.temperature_pub.publish(temp_msg)

        # Status (handle both enum and raw integer types)
        # status = frame.status
        # if isinstance(status, enum.Enum):
        #     status_name = status.name
        #     status_value = status.value
        # else:
        #     status_name = str(status)
        #     status_value = int(status)

        # status_int_msg = UInt32()
        # status_int_msg.data = status_value
        # self.status_int_pub.publish(status_int_msg)

        # status_string_msg = String()
        # status_string_msg.data = status_name
        # self.status_string_pub.publish(status_string_msg)

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
