FROM python:3.8.16-bullseye

# Needed for fury vtk. ffmpeg also needed
RUN apt-get update -y; apt-get install libgl1-mesa-dev xvfb ffmpeg libsm6 libxext6 -yq

# Copy the package requirements
COPY requirements.txt /opt

WORKDIR /opt
# Install the package requirements
RUN pip install -U pip
RUN pip install -r requirements.txt

RUN git clone https://github.com/wasserth/TotalSegmentator.git
RUN sed -i '/nibabel/d' /opt/TotalSegmentator/totalsegmentator/preview.py

COPY . /opt

ENV DISPLAY=:0
RUN Xvfb :0 -screen 1920x1080x24 > /dev/null 2>1 &