# bota_node

ROS2 node for data collection from a Bota Systems force/torque sensor using the `bota-driver` Python package.

## Published topics

- `/bota/wrench_N_and_Nm` (`geometry_msgs/WrenchStamped`) – force [N] and torque [Nm]
- `/bota/imu_mps2_and_radps` (`sensor_msgs/Imu`) – linear acceleration [m/s^2] and angular rate [rad/s]
- `/bota/temperature_C` (`sensor_msgs/Temperature`) – sensor temperature [C]
- `/bota/status_int` (`std_msgs/UInt32`) – driver frame status as integer
- `/bota/status_string` (`std_msgs/String`) – driver frame status as string

## Parameters

- `config_path` – path to the Bota driver JSON config file. Defaults to the installed `config/bota_serial_binary.json`.
- `publish_rate` – publication frequency in Hz. Default: `100.0`.
- `frame_id` – `frame_id` used in message headers. Default: `bota_sensor`.
- `tare_on_startup` – whether to tare the sensor when the node starts. Default: `true`.

## Build & run

```bash
./build.sh
./run.sh
```

Inside the container the node is launched with:

```bash
ros2 run bota_node bota_node
```

## USB latency setup

For high frequency communication, lower the USB serial latency timer. This increases CPU usage.

Create a systemd service, adapting `ttyACM0` to your actual serial device:

```bash
sudo nano /etc/systemd/system/set-usb-latency.service
```

```ini
[Unit]
Description=Set USB serial latency timer
After=syslog.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo 1 > /sys/bus/usb-serial/devices/ttyACM0/latency_timer'

[Install]
WantedBy=multi-user.target
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable set-usb-latency.service
```
