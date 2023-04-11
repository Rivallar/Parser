FROM python:3.11
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONYWRITEBYTECODE=1
WORKDIR /parser_app
COPY Pipfile Pipfile.lock ./
RUN python -m pip install --upgrade pip
RUN pip install pipenv && pipenv install --dev --system --deploy

EXPOSE 8080

COPY ./ /parser_app
CMD ["python", "main.py"]