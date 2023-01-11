FROM iqtlabs/edgetech-core:latest
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
ADD ./c2_pub_sub.py .
ENTRYPOINT [ "python3", "c2_pub_sub.py" ]