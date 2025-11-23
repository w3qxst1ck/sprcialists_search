FROM python:3.9


WORKDIR /code


COPY app/requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt


COPY ./app /code/app
COPY ./database /code/database
COPY ./settings.py /code/

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]