FROM alpine
RUN apk add python3
ENV PATH $PATH:/usr/share/pythonapp
workdir /SampleProject/PythonPrograme
ADD test.py test.py
ENTRYPOINT python3 test.py $NUMBER