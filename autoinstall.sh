#!/bin/bash

echo "Đang tiến hành cài đặt.."

sudo apt install ffmpeg

echo "Đang cài đặt LIB"

python3 -m pip install -r ./requirements.txt

echo "Đã cài đặt thành công!!!"

read -p "Bấm Enter để tiếp tục..."

clear

