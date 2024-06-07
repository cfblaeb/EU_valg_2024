FROM python:3.12.3-bookworm

RUN mkdir wd
WORKDIR wd
COPY requirements.txt .
COPY server.py .
COPY 2024_EP_Lasse_data.feather .
COPY tv2_sprg.json .
COPY dr1_sprg.json .
COPY various.json .
RUN pip3 install -r requirements.txt