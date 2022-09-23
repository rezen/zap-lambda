FROM owasp/zap2docker-weekly:w2022-09-20

# Make sure Java writes to /tmp directory
ENV JAVA_OPTS=-Djava.util.prefs.systemRoot=/tmp -Djava.util.prefs.userRoot=/tmp

# Add additional paths for python to load
ENV PYTHONPATH=/zap:/function

# Create directory for lambda code to run in
USER root
RUN mkdir -p /function && chown -R zap:zap /function

USER zap
ARG FUNCTION_DIR="/function"
RUN pip install --target ${FUNCTION_DIR} awslambdaric boto3

COPY prepare.sh .
RUN ./prepare.sh && \
    # Set zap.out dir to tmp path since in lambda only /tmp is writeable
    sed -i  -E "s|[^']+?zap.out|/tmp/zap.out|g" /zap/zap_common.py 


WORKDIR ${FUNCTION_DIR}
COPY app.py .

# The module awslambdaric implements the interface for custom lambdas
ENTRYPOINT [ "/usr/bin/python", "-m", "awslambdaric" ]
CMD [ "app.handler" ]