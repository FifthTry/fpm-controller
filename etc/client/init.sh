#!/usr/bin/bash

# Retrieve the current instance ID of the current machine
INSTANCE_ID=$(curl http://instance-data/latest/meta-data/instance-id/)

echo $INSTANCE_ID

# curl http://explainthisbit.com/v1/fpm/get-package?ec2_reservation=asd