#!/bin/bash
set -e

id -u ros &>/dev/null || adduser --quiet --disabled-password --gecos '' --uid ${UID:=1000} ros

if ! getent group plugdev > /dev/null; then
    groupadd -g ${PLUGDEV_GROUP_ID:=46} plugdev
    echo "Created plugdev group"
fi
usermod -aG dialout,plugdev ros

source /opt/ros/${ROS_DISTRO}/setup.bash
source /colcon_ws/install/setup.bash || true

exec "$@"

# # Set fixed process priority / niceness.
# # The container runs privileged, so CAP_SYS_NICE is available.
# NICE_LEVEL=-20
# RT_PRIORITY=90

# echo "Starting with SCHED_FIFO priority $RT_PRIORITY and nice level $NICE_LEVEL"
# exec chrt -f "$RT_PRIORITY" nice -n "$NICE_LEVEL" "$@"
