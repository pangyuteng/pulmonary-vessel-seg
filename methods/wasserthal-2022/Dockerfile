FROM wasserth/totalsegmentator_container:master

#
# download weights! https://github.com/wasserth/TotalSegmentator/blob/bc865436188c68fff55dadff4aaa8940a96609e5/totalsegmentator/libs.py#L77
#
ENV TOTALSEG_WEIGHTS_PATH=/opt/totalsegmentator_weights
RUN python /opt/conda/lib/python3.6/site-packages/totalsegmentator/download_pretrained_weights.py

RUN chmod 777 /opt/totalsegmentator_weights