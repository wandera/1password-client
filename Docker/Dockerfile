FROM python:3.8-slim
RUN useradd --create-home --shell /bin/bash app_user
WORKDIR /home/app_user
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
USER app_user
#RUN echo "export OP_DEVICE=yqxxxxxxxxxa34qltjhfrvdx2a" >> .bashrc
#RUN echo "export OP_SESSION_parksidesecuritiespoc=8958WfPy44mXXXXXX7x386pg7hJQvxdzEpRCk3IXFR4" >> .bashrc
RUN mkdir .op && chown app_user:app_user .op
COPY . .
#CMD ["bash"]
ENTRYPOINT [ "python" ]
CMD [ "compare.py" ]