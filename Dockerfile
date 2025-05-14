FROM python:3.11.9-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN pip install uvicorn[standard]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]