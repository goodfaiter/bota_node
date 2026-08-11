# bota_node

ROS2 node for data collection from a Bota Systems force/torque sensor using the `bota-driver` Python package.

## Published topics

- `/bota/wrench_N_and_Nm` (`geometry_msgs/WrenchStamped`) – force [N] and torque [Nm]

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
