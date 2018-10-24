FROM amazonlinux:2.0.20181010

WORKDIR /zap

RUN yum install -y curl wget xmlstarlet unzip tar git python-pip git java-1.8.0-openjdk vim

RUN pip install --install-option="--prefix=/zap/py" python-owasp-zap-v2.4 setuptools

ARG RELEASE=2018-10-22
RUN echo "Installing $RELEASE " && \
wget -q https://github.com/zaproxy/zaproxy/releases/download/w$RELEASE/ZAP_WEEKLY_D-$RELEASE.zip && \	
    unzip *.zip && \
	rm *.zip && \
	cp -R ZAP*/* . &&  \
	rm -R ZAP* && tail -n2 zap.sh

COPY zap_lambda.py  /zap/zap_lambda.py
COPY zap_common.py  /zap/zap_common.py
ENV PATH /zap/:$PATH
ENV ZAP_PATH /zap/zap.sh